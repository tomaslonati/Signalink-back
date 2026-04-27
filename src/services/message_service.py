# Importaciones necesarias para el servicio
import asyncio  # Para manejo asíncrono de websockets
import base64  # Para decodificar chunks de audio
import json  # Para serializar/deserializar mensajes JSON
import os  # Para acceder a variables de entorno
import threading  # Para ejecutar el loop asíncrono en un hilo separado
import time  # Para control de rate limiting
from typing import Optional  # Para type hints
import websockets  # Para conexión websocket con OpenAI
from datetime import datetime  # Para manejar timestamps
from src.utils.cloudinary_handler import upload_audio_to_cloudinary
from src.schemas.Message import Message
from src.utils.serializers import serialize_dict, serialize_list  # Para serializar datetime a JSON


class MessageService:
    """    
    Servicio que mantiene una conexión websocket persistente con OpenAI Realtime
    para transcripción de audio entre usuarios. Ejecuta un event loop de asyncio 
    en un hilo en segundo plano.
    """

    def __init__(self, socketio: Optional[object] = None):
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        # URL del endpoint de OpenAI Realtime con el modelo específico
        self.url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        
        # Guarda la instancia de SocketIO para comunicación en tiempo real con el frontend
        self.socketio = socketio

        # Conexión websocket (inicialmente None hasta conectar)
        self.ws = None
        
        # Rate limiting control
        self.last_chunk_time = 0
        self.min_chunk_interval = 0.5  # Minimum 500ms between chunks (más conservador)
        self.is_rate_limited = False
        self.rate_limit_until = 0
        
        # Buffer acumulativo para reducir requests
        self.audio_buffer = []
        self.buffer_max_chunks = 3  # Acumular 3 chunks antes de enviar
        
        # Event loop de asyncio que se ejecutará en el hilo separado
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread = threading.Thread(target=self._start_loop, daemon=True)
        self._stop_event = threading.Event()
        
        # Buffer para acumular chunks de audio
        self.audio_buffer = ""
        
        # Metadata del mensaje actual
        self.current_message_metadata = {}
        
        # Inicia el hilo que ejecutará el event loop
        self._thread.start()

    async def create_text_message(self, transmitter_id: int, group_id: int, content: str):
        """
        Crear un mensaje de texto para un grupo.
        
        """
        try:
            # Crear objeto del mensaje para guardar en DB
            message=Message(
                group_id=group_id,
                sender=transmitter_id,
                type="text",
                text=content
            )
            # Guardar mensaje en la base de datos
            await message.insert()

            # Emitir el mensaje a los clientes conectados
            self.socketio.emit("new_message", {
                "text": content,
                "group_id": group_id,
                "transmitter_id": transmitter_id
            })
            
            # Limpiar el buffer de audio
            self.audio_buffer = ""
            self.current_message_metadata = {}
            # Serializar el mensaje antes de devolverlo
            return serialize_dict(message)
        except Exception as e:
            print(f"Error al guardar el mensaje en la base de datos: {e}")

    def _start_loop(self):
        """
        Crea y ejecuta un event loop de asyncio dedicado a este servicio.
        Este método se ejecuta en un hilo separado para no bloquear el hilo principal.
        """
        # Crea un nuevo event loop para este hilo
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Programa la tarea de conexión con reintentos
        self.loop.create_task(self.connect_with_retries())
        try:
            self.loop.run_forever()
        finally:
            # Limpieza cuando el loop se detiene
            # Obtiene todas las tareas pendientes
            pending = asyncio.all_tasks(loop=self.loop)
            
            # Cancela todas las tareas pendientes
            for task in pending:
                task.cancel()
            try:
                # Cierra los generadores asíncronos pendientes
                self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            except Exception:
                pass
            
            # Cierra el event loop
            self.loop.close()

    async def connect(self):
        """
        Establece la conexión websocket con OpenAI Realtime API.
        Configura los headers de autenticación y versión beta.
        """
        # Headers requeridos para la autenticación con OpenAI
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1",
        }
        
        # Establece la conexión websocket
        self.ws = await websockets.connect(
            self.url,
            extra_headers=headers
        )
        
        # ✅ Configurar sesión según documentación
        await self.configure_session()
        
        # Inicia la tarea de escucha de mensajes del websocket
        self.loop.create_task(self.listen())

    async def configure_session(self):
        """
        Configura la sesión de OpenAI Realtime para transcripción entre usuarios.
        Solo transcribe audio, sin respuestas del asistente.
        """
        session_update = {
            "type": "session.update",
            "session": {
                "modalities": ["audio", "text"],  # Combinación soportada por OpenAI
                "input_audio_format": "pcm16",  # PCM16 mono 24kHz
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                "voice": "alloy"  # Voz por defecto aunque no se use
            }
        }
        
        # Envía la configuración al websocket
        await self.ws.send(json.dumps(session_update))

    async def connect_with_retries(self, retries: int = 5, delay: float = 2.0):
        """
        Intenta conectar al websocket con reintentos automáticos.
        
        Args:
            retries: Número máximo de reintentos antes de aumentar el delay
            delay: Segundos de espera entre reintentos
        """
        attempt = 0
        
        # Intenta conectar hasta que se detenga el servicio
        while not self._stop_event.is_set():
            try:
                await self.connect()
                return
            except Exception as e:
                attempt += 1
                print(f"OpenAI connect failed (attempt {attempt}): {e}")
                
                # Si excedió los reintentos, espera más tiempo
                if attempt >= retries:
                    await asyncio.sleep(delay * 5)
                else:
                    await asyncio.sleep(delay)

    async def _send_audio_chunk(self, audio_b64: str):
        """
        Método privado asíncrono para enviar un chunk de audio al websocket.
        Implementa rate limiting para evitar errores 429.
        
        Args:
            audio_b64: Audio codificado en base64 para enviar
        """
        # Verifica que el websocket esté conectado
        if not self.ws:
            print("❌ WS no conectado aún")
            return
        
        # Acumula el audio en el buffer
        self.audio_buffer += audio_b64
        # Validación del audio base64
        if not audio_b64:
            print("❌ Audio chunk vacío")
            return
        
        # Rate limiting check
        current_time = time.time()
        
        # Si estamos en rate limit, no enviar
        if self.is_rate_limited and current_time < self.rate_limit_until:
            time_left = self.rate_limit_until - current_time
            print(f"⏸️ Rate limited, esperando {time_left:.1f}s más")
            return
        
        # Reset rate limit flag if time has passed
        if current_time >= self.rate_limit_until:
            self.is_rate_limited = False
        
        # Enforce minimum interval between chunks
        time_since_last = current_time - self.last_chunk_time
        if time_since_last < self.min_chunk_interval:
            sleep_time = self.min_chunk_interval - time_since_last
            print(f"⏱️ Throttling: esperando {sleep_time:.3f}s")
            await asyncio.sleep(sleep_time)
        
        # Log para debug - solo los primeros caracteres
        print(f"📨 Enviando chunk de {len(audio_b64)} caracteres: {audio_b64[:50]}...")
        
        # Validar que sea base64 válido
        try:
            import base64
            decoded = base64.b64decode(audio_b64)
            print(f"✅ Base64 válido, {len(decoded)} bytes decodificados")
            
            # Diagnóstico del formato de audio
            if len(decoded) > 0:
                print(f"🔍 Primeros 20 bytes (hex): {decoded[:20].hex()}")
                
                # Calcular duración asumiendo PCM16 mono 24kHz
                # PCM16 = 2 bytes por sample, 24000 samples por segundo
                duration_seconds = len(decoded) / (2 * 24000)
                duration_ms = duration_seconds * 1000
                print(f"⏱️ Duración calculada (PCM16 24kHz): {duration_ms:.2f}ms")
                
                # Verificar si parece ser PCM16 (valores típicos)
                if len(decoded) >= 2:
                    sample = int.from_bytes(decoded[:2], byteorder='little', signed=True)
                    print(f"🎵 Primer sample (PCM16 LE): {sample}")
            else:
                print("⚠️ Audio chunk está vacío después de decodificar")
                return
        except Exception as e:
            print(f"❌ Base64 inválido: {e}")
            return
        
        # Crea el mensaje para agregar audio al buffer
        msg = {"type": "input_audio_buffer.append", "audio": audio_b64}
        
        try:
            # Envía el chunk de audio al websocket
            await self.ws.send(json.dumps(msg))
            
            # Update last chunk time
            self.last_chunk_time = time.time()
            
        except Exception as e:
            print(f"❌ Error sending audio chunk: {e}")

    def send_audio_chunk(self, audio_b64: str):
        """
        Método público thread-safe para enviar un chunk de audio.
        Implementa buffer acumulativo para reducir rate limiting.
        
        Args:
            audio_b64: Audio codificado en base64 para enviar
        """
        # Verifica que el event loop esté inicializado
        if not self.loop:
            print("Service loop not initialized yet")
            return
        
        # Si estamos en rate limit, descartar chunks
        if self.is_rate_limited:
            print("⏸️ Rate limited - descartando chunk")
            return
            
        # Agregar al buffer acumulativo
        self.audio_buffer.append(audio_b64)
        print(f"📦 Buffer: {len(self.audio_buffer)}/{self.buffer_max_chunks} chunks")
        
        # Enviar cuando el buffer esté lleno o forzar envío después de commit
        if len(self.audio_buffer) >= self.buffer_max_chunks:
            self._send_buffered_audio()
    
    def _send_buffered_audio(self):
        """Envía todos los chunks del buffer como uno solo"""
        if not self.audio_buffer:
            return
            
        try:
            # Combinar todos los chunks en uno solo
            combined_audio_bytes = b''
            for chunk_b64 in self.audio_buffer:
                chunk_bytes = base64.b64decode(chunk_b64)
                combined_audio_bytes += chunk_bytes
            
            # Convertir de vuelta a base64
            combined_b64 = base64.b64encode(combined_audio_bytes).decode('utf-8')
            
            print(f"🚀 Enviando buffer combinado: {len(combined_audio_bytes)} bytes de {len(self.audio_buffer)} chunks")
            
            # Limpiar buffer
            self.audio_buffer.clear()
            
            # Programa la ejecución del chunk combinado
            asyncio.run_coroutine_threadsafe(self._send_audio_chunk(combined_b64), self.loop)
            
        except Exception as e:
            print(f"❌ Error combinando buffer: {e}")
            self.audio_buffer.clear()

    async def _commit_audio(self, metadata: Optional[dict] = None):
        """
        Método privado asíncrono para hacer commit del buffer de audio.
        Cierra el buffer actual y solicita la transcripción.
        
        Args:
            metadata: Metadatos del mensaje (transmitter_id, group_id, etc)
        """
        # Verifica que el websocket esté conectado
        if not self.ws:
            print("❌ WS no conectado aún (commit)")
            return
        
        # Guarda los metadatos para usarlos después de la transcripción
        if metadata:
            self.current_message_metadata = metadata
        
        try:
            commit_message = {"type": "input_audio_buffer.commit"}
            print(f"📤 Enviando commit: {commit_message}")
            
            # Hace commit del buffer de audio acumulado
            await self.ws.send(json.dumps(commit_message))
            
            print("📨 Buffer cerrado, esperando transcripción...")
        except Exception as e:
            print(f"❌ Error committing audio buffer: {e}")
            self.socketio.emit("transcription_error", {"error": f"Error en commit: {e}"})

    def commit_audio(self, metadata: Optional[dict] = None):
        """
        Finaliza la grabación y envía cualquier chunk restante en el buffer
        """
        # Enviar chunks restantes en el buffer antes del commit
        if self.audio_buffer:
            print(f"📦 Enviando {len(self.audio_buffer)} chunks restantes antes del commit")
            self._send_buffered_audio()
        
        # Verifica que el event loop esté inicializado
        if not self.loop:
            print("Service loop not initialized yet (commit)")
            return
        
        # Programa la ejecución de _commit_audio en el event loop del servicio
        asyncio.run_coroutine_threadsafe(self._commit_audio(metadata), self.loop)

    async def listen(self):
        """
        Escucha continuamente los mensajes del websocket de OpenAI.
        Procesa las transcripciones de audio de los usuarios.
        """
        try:
            # Itera sobre cada mensaje recibido del websocket
            async for msg in self.ws:
                try:
                    # Parsea el mensaje JSON
                    data = json.loads(msg)
                    event_type = data.get("type")
                    
                    # Log todos los eventos recibidos para debug
                    print(f"� Evento OpenAI: {event_type}")
                    
                    # �👤 TRANSCRIPCIÓN DEL USUARIO COMPLETADA
                    # Cuando OpenAI termina de transcribir lo que dijo el usuario
                    if event_type == "conversation.item.input_audio_transcription.completed":
                        user_text = data.get("transcript")
                        print(f"✅ Usuario dijo: {user_text}")
                        
                        
                        try:
                            # Obtener metadata del mensaje
                            transmitter_id = self.current_message_metadata.get('transmitter_id')
                            group_id = self.current_message_metadata.get('group_id')
                            
                            if not transmitter_id or not group_id:
                                print("❌ Faltan metadatos del mensaje")
                                continue
                            
                            # Subir audio a Cloudinary
                            audio_url, duration = upload_audio_to_cloudinary(
                                self.audio_buffer,
                                transmitter_id,
                                group_id
                            )
                            
                            
                            # Crear objeto del mensaje para guardar en DB
                            message=Message(
                                group_id=group_id,
                                sender=transmitter_id,
                                type="audio",
                                text=user_text,
                                audio_url=audio_url,
                                duration=duration
                            )
                            
                            # Guardar mensaje en la base de datos
                            await message.insert()

                            # Emitir el mensaje a los clientes conectados
                            self.socketio.emit("new_message", {
                                "text": user_text,
                                "audio_url": audio_url,
                                "duration": duration,
                                "group_id": group_id,
                                "transmitter_id": transmitter_id
                            })
                            
                            # Limpiar el buffer de audio
                            self.audio_buffer = ""
                            self.current_message_metadata = {}
                            
                        except Exception as e:
                            print(f"❌ Error procesando mensaje de audio: {e}")
                            # Limpiar buffer aunque haya error
                            self.audio_buffer = ""
                            self.current_message_metadata = {}
                    
                    # Manejo de otros eventos importantes
                    elif event_type == "error":
                        error_msg = data.get("error", {}).get("message", "Error desconocido")
                        print(f"❌ Error OpenAI: {error_msg}")
                        self.socketio.emit("transcription_error", {"error": error_msg})
                    
                    elif event_type == "conversation.item.created":
                        print("📝 Item de conversación creado")
                    
                    elif event_type == "input_audio_buffer.committed":
                        print("✅ Buffer de audio confirmado")
                    
                    elif event_type == "conversation.item.input_audio_transcription.failed":
                        error_details = data.get("error", {})
                        error_msg = error_details.get("message", "Transcripción falló")
                        error_code = error_details.get("code", "unknown")
                        
                        print(f"❌ Transcripción falló: {error_msg}")
                        
                        # Manejo específico para rate limiting (429)
                        if "429" in error_msg or "Too Many Requests" in error_msg:
                            print("⚠️ Rate limit alcanzado. Activando pausa de 10 segundos")
                            
                            # Activar rate limiting por 10 segundos
                            self.is_rate_limited = True
                            self.rate_limit_until = time.time() + 10
                            
                            self.socketio.emit("transcription_error", {
                                "error": "Has excedido el límite de requests. El sistema pausará automáticamente por 10 segundos.",
                                "code": "rate_limit",
                                "retry_after": 10
                            })
                        else:
                            self.socketio.emit("transcription_error", {
                                "error": error_msg,
                                "code": error_code
                            })
                    
                    else:
                        # Log eventos no manejados para debug
                        print(f"🔍 Evento no manejado: {event_type}")
                    
                except Exception as e:
                    # Si hay error parseando un mensaje, continúa con el siguiente
                    print(f"Error parsing message: {e}")
                    continue
                    
        except Exception as e:
            # Error en el loop de escucha (puede ser desconexión)
            print(f"Listen loop error: {e}")
        finally:
            # Limpieza al cerrar la conexión
            try:
                # Intenta cerrar el websocket de forma limpia
                await self.ws.close()
            except Exception:
                pass
            
            # Marca el websocket como no conectado
            self.ws = None
            
            # Espera un segundo antes de reconectar
            await asyncio.sleep(1)
            
            # Programa una nueva tarea de reconexión con reintentos
            self.loop.create_task(self.connect_with_retries())

    def stop(self):
        """
        Detiene el servicio de forma limpia.
        Señaliza el evento de parada y detiene el event loop.
        """
        # Señaliza que el servicio debe detenerse
        self._stop_event.set()
        
        # Si el loop existe, lo detiene de forma thread-safe
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
    
    def get_conversation(self, group_id: int):
        """
        Obtiene los mensajes de una conversación específica.
        
        Args:
            group_id: ID del grupo a obtener
        
        Returns:
            Lista de mensajes en la conversación
        """
        # aca va la lógica para obtener los mensajes de la base de datos
        messages = Message.find(Message.group_id == group_id).sort(-Message.created_at)
        return messages
