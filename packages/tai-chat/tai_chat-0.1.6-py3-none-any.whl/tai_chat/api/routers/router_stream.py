"""
Router de chat streaming con WebSocket
"""
from datetime import datetime
import json
import asyncio
from tai_alphi import Alphi
from langchain_core.messages import HumanMessage
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query

from api.auth import get_current_user, JWTHandler
from api.resources import (
    RecordNotFoundException,
    APIException,
    APIResponse
)
from ..database import chatbot_api, UsuarioRead

from ..utils import add_message
from ..types import (
    StreamMessageRequest,
    StreamMessageResponse,
    StreamingStatus,
    WebsocketMessageType
)
from ..llm import llm_manager
from ..websockets import connection_manager

logger = Alphi.get_logger_by_name("tai-api")

# Router
streaming_router = APIRouter(
    prefix="/streaming",
    tags=["Streaming"]
)
        
@streaming_router.post("/chat/send", response_model=APIResponse[StreamMessageResponse])
async def send_message_to_stream(
    input_msg: StreamMessageRequest,
    current_user: UsuarioRead = Depends(get_current_user)
) -> APIResponse[StreamMessageResponse]:
    """
    Enviar mensaje y iniciar streaming de respuesta
    
    Este endpoint:
    1. Valida el chat y permisos
    2. Guarda el mensaje del usuario
    3. Notifica via WebSocket que el streaming comenzó
    4. Retorna inmediatamente mientras el streaming continúa en background
    """
    try:
        
        # 1. Validar que el chat existe y pertenece al usuario
        chat = await chatbot_api.chat.find(id=input_msg.chat_id)
        if not chat:
            raise RecordNotFoundException(resource="Chat")
        
        if chat.username != current_user.username:
            raise APIException(message="No tienes permisos para este chat")
        
        msg = HumanMessage(content=input_msg.content)
        
        response = await add_message(chat_id=chat.id, msg=msg)

        if not response.get("success"):
            raise APIException(
                message="Error guardando el mensaje del usuario",
                details={"error": response.get("error")}
            )
        
        # 3. Notificar inicio de streaming via WebSocket
        connections_notified = await connection_manager.send_to_chat(
            chat.id, {"type": WebsocketMessageType.MESSAGE_RECEIVED.value}
        )
        
        # 4. Iniciar streaming en background
        asyncio.create_task(llm_manager.streaming_response(msg, chat.id))
        
        response_data = StreamMessageResponse(
            user_id=current_user.username,
            msg_id=response.get('msg').id,
            connections_notified=connections_notified,
            chat_id=chat.id
        )
        
        return APIResponse.success(
            data=response_data,
            message="Mensaje enviado, streaming iniciado"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en send_message_to_stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@streaming_router.websocket("/ws/chat/{chat_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket, 
    chat_id: int,
    token: str = Query(...)
):
    """
    Endpoint WebSocket para recibir streaming de respuestas del chat
    """
    connection_id = None
    
    try:
        # Validar token JWT
        try:
            payload = JWTHandler.decode_token(token)
            if not payload:
                await websocket.close(code=4001, reason="Token inválido")
                return
            
            # Verificar que el usuario existe en BD
            user = await chatbot_api.usuario.find(username=payload.username)
            if not user:
                await websocket.close(code=4001, reason="Usuario no encontrado")
                return
                
            user_id = payload.username
        except Exception as e:
            logger.error(f"Error validando token WebSocket: {e}")
            await websocket.close(code=4001, reason="Token inválido")
            return
        
        # Validar que el chat existe
        chat = await chatbot_api.chat.find(chat_id)
        if not chat:
            await websocket.close(code=4004, reason="Chat no encontrado")
            return
            
        # Validar permisos del chat
        if chat.username != user_id:
            await websocket.close(code=4003, reason="Sin permisos para este chat")
            return
        
        # Conectar WebSocket
        connection_id = await connection_manager.connect(websocket, user_id, chat_id)
        
        # Enviar confirmación de conexión
        await connection_manager.send_to_connection(
            connection_id,
            {
                "type": WebsocketMessageType.CONNECTION_ESTABLISHED.value,
                "meta": {
                    "chat_id": chat_id,
                    "connection_id": connection_id
                }
            }
        )
        
        # Mantener conexión viva
        while True:
            try:
                # Esperar mensajes del cliente (ej: ping, cancel, etc.)
                message = await websocket.receive_text()
                data: dict = json.loads(message)
                
                if data.get("type") == "ping":
                    await connection_manager.send_to_connection(
                        connection_id,
                        {"type": WebsocketMessageType.PONG.value, "meta": {"timestamp": datetime.now().isoformat()}}
                    )
                elif data.get("type") == "cancel_stream":
                    # TODO: Implementar cancelación de streaming
                    logger.info(f"Streaming cancelado por usuario en chat {chat_id}")
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error en WebSocket para chat {chat_id}: {e}")
                break
    
    except Exception as e:
        logger.error(f"Error en conexión WebSocket: {e}")
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close(code=4000, reason="Error interno")
    
    finally:
        if connection_id:
            await connection_manager.disconnect(connection_id)


@streaming_router.delete("/chat/context/{chat_id}", response_model=APIResponse[bool])
async def clear_chat_context(
    chat_id: int,
    current_user: UsuarioRead = Depends(get_current_user)
) -> APIResponse[int]:
    """
    Limpiar contexto de un chat (elimina mensajes previos)
    
    Esto no elimina el chat ni los mensajes, solo el contexto guardado en la base de datos
    """
    # Validar que el chat existe y pertenece al usuario
    chat = await chatbot_api.chat.find(id=chat_id)
    if not chat:
        raise RecordNotFoundException(resource="Chat")
    
    if chat.username != current_user.username:
        raise APIException(message="No tienes permisos para este chat")
    
    # Limpiar contexto en la base de datos
    await llm_manager.delete_context(thread_id=str(chat.id))
    
    logger.info(f"Contexto del chat {chat.id} limpiado por usuario {current_user.username}")
    return APIResponse.success(
        data=True,
        message=f"Contexto del chat {chat.id} limpiado exitosamente"
    )

@streaming_router.get("/status", response_model=APIResponse[StreamingStatus])
async def get_streaming_status() -> APIResponse[StreamingStatus]:
    """Obtener estado del sistema de streaming"""
    status_data = StreamingStatus(
        status="active",
        message="Sistema de streaming operativo",
        connections=connection_manager.get_active_connections_count()
    )
    
    return APIResponse.success(
        data=status_data,
        message="Estado del sistema de streaming obtenido exitosamente"
    )

@streaming_router.get("/chat/{chat_id}/status", response_model=APIResponse[StreamingStatus])
async def get_chat_streaming_status(
    chat_id: int,
    current_user: UsuarioRead = Depends(get_current_user)
) -> APIResponse[StreamingStatus]:
    """Obtener estado de streaming para un chat específico"""
    
    # Validar permisos
    chat = await chatbot_api.chat.find(chat_id)
    if not chat:
        raise RecordNotFoundException(resource="Chat")
    
    if chat.username != current_user.username:
        raise APIException(message="No tienes permisos para este chat")
    
    status_data = StreamingStatus(
        status="active",
        message=f"Chat {chat_id} disponible para streaming",
        connections=connection_manager.get_chat_connections_count(chat_id),
        chat_id=chat_id
    )
    
    return APIResponse.success(
        data=status_data,
        message="Estado del chat obtenido exitosamente"
    )