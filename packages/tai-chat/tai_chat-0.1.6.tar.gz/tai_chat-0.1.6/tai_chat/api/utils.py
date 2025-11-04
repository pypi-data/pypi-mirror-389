from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import BaseMessage
from tai_alphi import Alphi

from .database import (
    chatbot_api,
    MensajeCreate,
    MensajeRead,
    ChatUpdateValues
)

logger = Alphi.get_logger_by_name("tai-chatbot")

async def add_message(
    chat_id: str, 
    msg: BaseMessage
) -> Dict[str, bool | MensajeRead | str]:
    """
    Añadir mensaje al contexto y guardarlo en BD
    
    Args:
        chat_id: ID del chat
        msg: Mensaje a añadir (HumanMessage o AIMessage)
        
    Returns:
        Dict: Información del mensaje creado
    """
    try:
        
        # Crear mensaje en BD
        message = await chatbot_api.mensaje.create(MensajeCreate(content=msg.content, role=msg.type, chat_id=chat_id))
        
        # Actualizar timestamp del chat
        await chatbot_api.chat.update(chat_id, updated_values=ChatUpdateValues(updated_at=datetime.now()))
        
        return {
            "msg": message,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"[chatbot] Error añadiendo mensaje al chat {chat_id}: {e}")
        return {"success": False, "error": str(e)}