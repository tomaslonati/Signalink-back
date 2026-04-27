#!/usr/bin/env python3
"""
Servicio alternativo usando OpenAI Whisper HTTP API en lugar de Realtime
"""
import os
import base64
import tempfile
import requests
from openai import OpenAI
from typing import Optional
from utils.cloudinary_handler import upload_audio_to_cloudinary
from schemas.Message import Message
import asyncio

class WhisperMessageService:
    """
    Servicio alternativo que usa OpenAI Whisper HTTP API
    Más estable que la API Realtime
    """
    
    def __init__(self, socketio: Optional[object] = None):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.socketio = socketio
        
        # Switch simple: qué servicio usar
        self.use_custom_service = os.getenv("USE_CUSTOM_WHISPER", "false").lower() == "true"
        self.custom_service_url = os.getenv("CUSTOM_WHISPER_URL", "")
        
        # Configurar cliente OpenAI (solo si no usamos el servicio custom)
        if not self.use_custom_service and self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
        
        # Buffer para acumular audio
        self.audio_buffer = []
        self.current_message_metadata = {}
        
        # Servicio inicializado

    def send_audio_chunk(self, audio_b64: str):
        """
        Acumula chunks de audio para procesar cuando termine la grabación
        
        Args:
            audio_b64: Audio codificado en base64
        """
        if not audio_b64:
            return
            
        self.audio_buffer.append(audio_b64)
        # Buffer actualizado

    def commit_audio(self, metadata: Optional[dict] = None):
        """
        Procesa todo el audio acumulado usando Whisper HTTP API
        
        Args:
            metadata: Metadatos del mensaje (transmitter_id, group_id, etc)
        """
        if not self.audio_buffer:
            return

        # Guardar metadatos para usar después de la transcripción
        if metadata:
            self.current_message_metadata = metadata
            print(f"💾 Metadatos guardados: {metadata}")
        try:
            # Combinar todos los chunks de audio
            combined_audio_bytes = b''
            for chunk_b64 in self.audio_buffer:
                try:
                    chunk_bytes = base64.b64decode(chunk_b64)
                    combined_audio_bytes += chunk_bytes
                except Exception as e:
                    continue

            if len(combined_audio_bytes) < 1000:  # Menos de 1KB
                self.audio_buffer.clear()
                return

            # Guardar temporalmente el audio para Whisper
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(combined_audio_bytes)
                temp_file_path = temp_file.name

            # Switch simple: usar tu servicio o OpenAI
            try:
                if self.use_custom_service:
                    # Usar TU servicio - pasar el archivo temporal, no los bytes
                    transcribed_text = self._transcribe_with_custom_service(temp_file_path)
                else:
                    # Usar OpenAI
                    transcribed_text = self._transcribe_with_openai(temp_file_path)

                # Usar los metadatos guardados o los pasados por parámetro
                metadata_to_use = metadata or self.current_message_metadata
                
                if metadata_to_use:
                    self._process_transcription(transcribed_text, metadata_to_use)
                else:
                    # Enviar transcripción básica sin metadatos
                    if self.socketio:
                        basic_response = {
                            "transcript": transcribed_text,
                            "text": transcribed_text,
                            "success": True,
                            "timestamp": self._get_timestamp()
                        }
                        self.socketio.emit("transcription_result", basic_response)

            except Exception as e:
                error_msg = f"Error en transcripción Whisper: {str(e)}"
                
                if self.socketio:
                    error_response = {
                        "error": error_msg,
                        "success": False,
                        "timestamp": self._get_timestamp()
                    }
                    self.socketio.emit("transcription_error", error_response)
                    print(f"📤 Error enviado al cliente: {error_msg}")
                else:
                    print("❌ SocketIO no disponible para enviar error")

            # Limpiar archivo temporal
            try:
                os.unlink(temp_file_path)
            except:
                pass

        except Exception as e:
            print(f"❌ Error general en commit_audio: {e}")
        finally:
            # Limpiar buffer
            self.audio_buffer.clear()
            self.current_message_metadata = {}

    def _process_transcription(self, transcribed_text: str, metadata: dict):
        """
        Procesa el texto transcrito y guarda el mensaje
        """
        try:
            transmitter_id = metadata.get('transmitter_id')
            receiver_id = metadata.get('receiver_id')
            group_id = metadata.get('group_id', receiver_id)  # Usar receiver_id como fallback

            if not transmitter_id:
                return

            # Emitir resultado de transcripción al frontend INMEDIATAMENTE
            response_data = {
                "transcript": transcribed_text,
                "text": transcribed_text,
                "transmitter_id": transmitter_id,
                "receiver_id": receiver_id,
                "group_id": group_id,
                "type": "audio_transcription",
                "success": True,
                "timestamp": self._get_timestamp()
            }

            if self.socketio:
                # Enviar múltiples eventos para asegurar que el frontend reciba
                self.socketio.emit("transcription_result", response_data)
                self.socketio.emit("new_message", response_data) 
                self.socketio.emit("audio_transcription_complete", response_data)

            # TODO: Opcional - subir audio a Cloudinary y guardar en DB
            # message = Message(...)
            # await message.insert()

        except Exception as e:
            # Enviar error al frontend
            if self.socketio:
                error_data = {
                    "error": str(e),
                    "success": False,
                    "timestamp": self._get_timestamp()
                }
                self.socketio.emit("transcription_error", error_data)

    def _transcribe_with_custom_service(self, audio_input) -> str:
        """
        Transcribir usando TU servicio personalizado
        Puede recibir bytes o ruta de archivo
        """
        import requests
        import os
        
        if not self.custom_service_url:
            raise Exception("URL del servicio personalizado no configurada")
        
        try:
            # Determinar si es bytes o ruta de archivo
            if isinstance(audio_input, bytes):
                # Crear archivo temporal para enviar
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_file.write(audio_input)
                    temp_file_path = temp_file.name
                temp_file_created = True
            elif isinstance(audio_input, str):
                temp_file_path = audio_input
                temp_file_created = False
            else:
                raise ValueError(f"Tipo de entrada inválido: {type(audio_input)}")
            
            # Enviar al servicio personalizado
            with open(temp_file_path, 'rb') as audio_file:
                files = {'audio': ('audio.wav', audio_file, 'audio/wav')}
                data = {'language': 'es'}
                
                response = requests.post(
                    self.custom_service_url,
                    files=files,
                    data=data,
                    timeout=40
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extraer texto de la respuesta
                    text = result.get('text', result.get('transcription', ''))
                    return text
                else:
                    error_msg = f"Error HTTP {response.status_code}: {response.text}"
                    raise Exception(error_msg)
                    
        except requests.exceptions.Timeout:
            raise Exception("Timeout conectando a tu servicio Whisper")
        except requests.exceptions.ConnectionError:
            raise Exception("Error de conexión a tu servicio Whisper")
        except Exception as e:
            raise e
        finally:
            # Limpiar archivo temporal solo si lo creamos nosotros
            if temp_file_created:
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

    def _transcribe_with_openai(self, temp_file_path: str) -> str:
        """
        Transcribir usando OpenAI Whisper
        """
        if not self.client:
            raise Exception("Cliente OpenAI no configurado")
            
        try:
            with open(temp_file_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="es"
                )
            
            return transcript.text
            
        except Exception as e:
            raise e

    def _get_timestamp(self):
        """Obtiene timestamp actual en formato ISO"""
        from datetime import datetime
        return datetime.now().isoformat()

    def create_text_message(self, transmitter_id: int, receiver_id: int, content: str):
        """
        Crear un mensaje de texto - versión síncrona adaptada de tercer_sprint
        
        Args:
            transmitter_id: ID del remitente
            receiver_id: ID del receptor (se usa como group_id para compatibilidad)
            content: Contenido del mensaje
        """
        try:
            # Usar receiver_id como group_id para compatibilidad
            group_id = receiver_id
            
            # Crear objeto del mensaje para guardar en DB
            message = Message(
                group_id=group_id,
                sender=transmitter_id,
                type="text",
                text=content
            )
            
            # TODO: En un entorno async, necesitaríamos await message.insert()
            # Por ahora, emitimos el mensaje sin guardar en DB
            
            # Emitir el mensaje a los clientes conectados
            if self.socketio:
                self.socketio.emit("new_message", {
                    "text": content,
                    "group_id": group_id,
                    "transmitter_id": transmitter_id
                })
            
            # Limpiar el buffer de audio y metadata
            self.audio_buffer = []
            self.current_message_metadata = {}
            
            # Retornar el mensaje serializado de forma compatible
            from src.utils.serializers import serialize_dict
            return serialize_dict({
                "id": None,  # No tenemos ID porque no guardamos en DB aún
                "group_id": group_id,
                "sender": transmitter_id,
                "type": "text", 
                "text": content,
                "created_at": self._get_timestamp()
            })
            
        except Exception as e:
            print(f"Error al crear mensaje de texto: {e}")
            raise e

    def get_conversation(self, group_id: int):
        """
        Placeholder - implementar si necesitas conversaciones
        """
        return {"messages": [], "total": 0}
    
    @staticmethod
    async def _generate_audio(text: str, voice_name: str = "Ava Song"):
        """LLama a Hume TTS y devuelve bytes del audio"""
        from hume import AsyncHumeClient
        from hume.tts import PostedUtterance, PostedUtteranceVoiceWithName
        client = AsyncHumeClient(api_key=os.getenv("HUME_API_KEY"))
        
        utterance = PostedUtterance(
            text=text,
            voice=PostedUtteranceVoiceWithName(name=voice_name, provider="HUME_AI")
        )

        response = await client.tts.synthesize_json(
            utterances=[utterance],
            num_generations=1,
            version="1"
        )

        gen = response.generations[0]
        audio_base64 = gen.audio
        return base64.b64decode(audio_base64)
    
    def generate_audio(self, text: str, voice_name: str = "Ava Song") -> bytes:
        """Versión síncrona que funciona con event loops existentes usando AsyncManager"""
        from src.utils.async_manager import run_async_safe

        # Pasar una callable que creará la corrutina dentro del thread del AsyncManager
        return run_async_safe(lambda: WhisperMessageService._generate_audio(text, voice_name))