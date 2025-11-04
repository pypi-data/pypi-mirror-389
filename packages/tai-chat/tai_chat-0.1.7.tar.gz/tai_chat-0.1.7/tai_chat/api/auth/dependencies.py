"""
chat-demo - Authentication Dependencies
Generado automáticamente por tai-api set-auth

Este módulo contiene las dependencias de FastAPI para autenticación,
incluyendo get_current_user y validación de sesiones.
"""

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

from .jwt import JWTHandler, TokenPayload
from ..database import ChatbotAsyncDBAPI, UsuarioRead
from ..resources import (
    SessionInvalidatedException,
    RecordNotFoundException
)

# Configurar OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/docslogin")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
) -> UsuarioRead:
    """
    Dependencia de FastAPI para obtener el usuario actual autenticado.
    
    Esta función:
    1. Recibe el token automáticamente via OAuth2PasswordBearer
    2. Valida y decodifica el token JWT
    3. Verifica que el usuario existe en la base de datos
    4. Valida que el session_id del token coincida con el de la BD    
    Args:
        token: Token JWT extraído automáticamente del header Authorization
        
    Returns:
        UsuarioRead: Usuario autenticado
        
    Raises:
        InvalidTokenException: Si el token es inválido
        SessionInvalidatedException: Si la sesión fue invalidada
        RecordNotFoundException: Si el usuario no existe
    """
    
    # 1. Decodificar y validar token JWT
    payload: TokenPayload = JWTHandler.decode_token(token)
    
    # 2. Buscar usuario en la base de datos
    user = await api.usuario.find(
        username=payload.username
    )
    
    if not user:
        raise RecordNotFoundException("Usuario no encontrado")
    
    # 3. Validar session_id si está configurado
    
    if user.session_id != payload.session_id:
        raise SessionInvalidatedException()
    
    return user

# Alias para uso más conveniente
CurrentUser = UsuarioRead