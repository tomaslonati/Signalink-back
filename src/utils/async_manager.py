"""
AsyncManager - Manejador robusto de operaciones asíncronas en Flask
Solución para Cloud Run y entornos con event loops existentes
"""
import asyncio
import threading
import concurrent.futures
from functools import wraps
from typing import Any, Callable, Coroutine
import nest_asyncio

class AsyncManager:
    """
    Manejador thread-safe para operaciones asíncronas en Flask.
    Resuelve conflictos de event loop en Cloud Run.
    """
    
    _instance = None
    _lock = threading.Lock()
    _executor = None
    _loop_thread = None
    _loop = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._setup_async_environment()
    
    def _setup_async_environment(self):
        """Configurar el entorno asíncrono"""
        try:
            # Aplicar nest_asyncio para permitir loops anidados
            nest_asyncio.apply()
            
            # Crear executor para operaciones async
            self._executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=4, 
                thread_name_prefix="async_manager"
            )
            
            print("✅ AsyncManager inicializado correctamente")
        except Exception as e:
            print(f"❌ Error inicializando AsyncManager: {e}")
            raise e
    
    def run_async(self, func_or_coro) -> Any:
        """
        Ejecuta una función async (callable) o corrutina de forma thread-safe.
        Preferimos recibir una función asíncrona (no llamada) para crear la corrutina
        dentro del thread donde se ejecutará — así evitamos reutilizar coroutines
        creadas en otro loop (causa del error en Cloud Run).
        """
        print("🔄 Running sync function")
        # Si nos pasan una función (async def), delegar a la versión que crea
        # la corrutina dentro del thread para evitar problemas de loop.
        if callable(func_or_coro):
            return self._run_in_thread_callable(func_or_coro)

        # Si nos pasan una corrutina directamente, esto es peligroso: intentamos
        # ejecutarla en un thread nuevo, pero la corrutina puede estar ligada a
        # otro loop. Mejor lanzar un error claro para forzar el cambio a pasar
        # funciones en lugar de objetos coroutine.
        raise TypeError("run_async expects a callable (async function) not a coroutine object. "
                        "Pass a zero-arg callable like: lambda: my_async_func(...)")
    
    def _run_in_thread(self, coro: Coroutine) -> Any:
        """Ejecutar corrutina en un thread separado con su propio loop"""
        result_container = {}
        exception_container = {}
        
        def run_coro():
            try:
                print("🔄 Creating new event loop in thread")
                # Crear nuevo loop para este thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    print("🔄 Running coroutine in new loop")
                    result = new_loop.run_until_complete(coro)
                    result_container['result'] = result
                    print("✅ Coroutine completed successfully")
                except Exception as e:
                    print(f"❌ Error in coroutine: {e}")
                    exception_container['exception'] = e
                finally:
                    try:
                        new_loop.close()
                        print("🔄 Event loop closed")
                    except:
                        pass
            except Exception as e:
                print(f"❌ Error creating thread loop: {e}")
                exception_container['exception'] = e
        
        thread = threading.Thread(target=run_coro)
        thread.start()
        thread.join(timeout=30)  # Timeout de 30 segundos
        
        if thread.is_alive():
            print("❌ Thread timeout - operación async muy lenta")
            raise TimeoutError("Async operation timed out")
        
        if 'exception' in exception_container:
            raise exception_container['exception']
        
        return result_container.get('result')

    def _run_in_thread_callable(self, func: Callable) -> Any:
        """Crear y ejecutar la corrutina dentro de un thread nuevo.
        Esto evita crear la corrutina en el hilo principal y luego intentar
        ejecutarla en otro loop (lo que produce 'cannot reuse already awaited coroutine').
        """
        result_container = {}
        exception_container = {}

        def run_func():
            new_loop = None
            try:
                print("🔄 Creating new event loop in thread")
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                
                # Crear la corrutina DENTRO del thread
                coro = func()
                print("🔄 Running coroutine in new loop")
                
                # Verificar que el loop no está cerrado antes de usar
                if new_loop.is_closed():
                    raise RuntimeError("Event loop was closed before execution")
                
                result = new_loop.run_until_complete(coro)
                result_container['result'] = result
                print("✅ Coroutine completed successfully")
                
            except Exception as e:
                print(f"❌ Error in coroutine: {e}")
                exception_container['exception'] = e
            finally:
                # Cleanup más seguro del event loop
                if new_loop and not new_loop.is_closed():
                    try:
                        # Cancelar tareas pendientes si las hay
                        pending_tasks = asyncio.all_tasks(new_loop)
                        if pending_tasks:
                            for task in pending_tasks:
                                task.cancel()
                        
                        # Ejecutar un último ciclo para manejar cancelaciones
                        new_loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
                    except Exception as cleanup_error:
                        print(f"⚠️ Warning during cleanup: {cleanup_error}")
                    finally:
                        try:
                            new_loop.close()
                            print("🔄 Event loop closed cleanly")
                        except Exception as close_error:
                            print(f"⚠️ Warning closing loop: {close_error}")
                else:
                    print("🔄 Event loop was already closed")

        thread = threading.Thread(target=run_func, name="AsyncManager-Thread")
        thread.start()
        thread.join(timeout=30)

        if thread.is_alive():
            print("❌ Thread timeout - operación async muy lenta")
            raise TimeoutError("Async operation timed out")

        if 'exception' in exception_container:
            raise exception_container['exception']

        return result_container.get('result')
    
    def _run_with_executor(self, func: Callable) -> Any:
        """Fallback: usar ThreadPoolExecutor y ejecutar la función dentro del executor."""
        def run_in_executor():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                coro = func()
                return loop.run_until_complete(coro)
            finally:
                loop.close()

        future = self._executor.submit(run_in_executor)
        return future.result()
    
    def sync_wrapper(self, async_func: Callable) -> Callable:
        """
        Decorator para convertir funciones async a sync de forma thread-safe
        """
        @wraps(async_func)
        def wrapper(*args, **kwargs):
            # Devolver una callable que, cuando se ejecute dentro del thread,
            # creará la corrutina y la ejecutará allí.
            return self.run_async(lambda: async_func(*args, **kwargs))
        return wrapper
    
    def cleanup(self):
        """Limpiar recursos"""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

# Instancia global
async_manager = AsyncManager()

def make_sync(async_func: Callable) -> Callable:
    """
    Decorator simple para convertir funciones async a sync
    Uso: @make_sync
    """
    return async_manager.sync_wrapper(async_func)

def run_async_safe(coro: Coroutine) -> Any:
    """
    Función utilitaria para ejecutar corrutinas de forma segura
    """
    # Preferimos que se pase una callable; si se pasa una corrutina, lanzamos
    # un error útil para que el llamador cambie la forma de invocar.
    if callable(coro):
        return async_manager.run_async(coro)
    raise TypeError("run_async_safe expects a callable (zero-arg) that returns a coroutine. "
                    "Use: run_async_safe(lambda: my_async_func(...))")