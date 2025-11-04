"""
chat-demo - Authentication Endpoints
Generado automáticamente por tai-api set-auth

Este módulo contiene los endpoints de login y logout con manejo de sesiones.
"""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from .jwt import JWTHandler
from .dependencies import get_current_user, CurrentUser
from ..database import ChatbotAsyncDBAPI, UsuarioUpdateValues
from ..resources import (
    APIResponse,
    InvalidCredentialsException,
    ConcurrentSessionDetectedException,
    DatabaseException
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])

class LoginRequest(BaseModel):
    """Modelo para datos de login"""
    username: str
    pwd: str

class LoginData(BaseModel):
    """Modelo para datos de respuesta de login"""
    access_token: str
    token_type: str = "bearer"
    user: dict  # Información básica del usuario
    session_id: str

class LogoutData(BaseModel):
    """Modelo para datos de respuesta de logout"""
    message: str = "Sesión cerrada exitosamente"

class UserInfoData(BaseModel):
    """Modelo para datos de información de usuario"""
    username: str


async def authenticate(
    username: str,
    pwd: str,
    api: ChatbotAsyncDBAPI,
    from_swagger: bool=False
) -> APIResponse[LoginData] | LoginData:
    """
    Función auxiliar que realiza la lógica de login compartida.
    
    Args:
        username: Nombre de usuario
        password: Contraseña
        api: DAO para acceso a datos
        
    Returns:
        APIResponse[LoginData]: Respuesta estándar con token y datos de usuario
        
    Raises:
        InvalidCredentialsException: Si credenciales son incorrectas
        DatabaseException: Si hay error en BD
    """
    try:
        # 1. Buscar usuario
        user = await api.usuario.find(
            username=username
        )
        
        if not user:
            raise InvalidCredentialsException()
        
        # 2. Verificar contraseña
        if user.password != pwd:
            raise InvalidCredentialsException()
        
        # 3. Generar nuevo session_id
        new_session_id = JWTHandler.generate_session_id()
        
        # 4. Actualizar session_id en BD
        await api.usuario.update(
            username=user.username,
            updated_values=UsuarioUpdateValues(
                session_id=new_session_id
            )
        )
        
        # Refrescar el objeto user
        user = await api.usuario.find(username=user.username)
        
        # 5. Generar token JWT
        token = JWTHandler.create_token(
            username=username,
            session_id=new_session_id
        )
        
        # 6. Preparar respuesta (sin datos sensibles)
        user_data = {
            "username": user.username,
            # Agregar otros campos públicos según necesites
        }
        
        login_data = LoginData(
            access_token=token,
            user=user_data,
            session_id=new_session_id
        )

        if from_swagger:
            return login_data
        
        return APIResponse.success(
            data=login_data,
            message="Autenticación exitosa"
        )
        
    except Exception as e:
        if isinstance(e, (InvalidCredentialsException, ConcurrentSessionDetectedException)):
            raise e
        raise DatabaseException(f"Error en login: {str(e)}")


@router.post("/login", response_model=APIResponse[LoginData])
async def login(
    credentials: LoginRequest,
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
):
    """
    Endpoint de autenticación de usuarios
    """
    return await authenticate(credentials.username, credentials.pwd, api)


@router.post("/docslogin", response_model=LoginData, include_in_schema=False)
async def docs_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
):
    """
    Endpoint de autenticación para la documentación de FastAPI (formulario)
    """
    return await authenticate(form_data.username, form_data.password, api, from_swagger=True)


@router.post("/logout", response_model=APIResponse[LogoutData])
async def logout(
    current_user: CurrentUser = Depends(get_current_user),
    api: ChatbotAsyncDBAPI = Depends(ChatbotAsyncDBAPI)
):
    """
    Endpoint para cerrar sesión.
    Invalida la sesión actual eliminando o cambiando el session_id
    
    Args:
        current_user: Usuario autenticado (obtenido de token)
        
    Returns:
        APIResponse[LogoutData]: Respuesta estándar de confirmación de logout
        
    Raises:
        DatabaseException: Si hay error al invalidar sesión
    """
    
    try:
        # Invalidar sesión actual
        await api.usuario.update(
            username=current_user.username,
            updated_values=UsuarioUpdateValues(
                session_id=None
            )
        )
        
        logout_data = LogoutData()
        return APIResponse.success(
            data=logout_data,
            message="Sesión cerrada exitosamente"
        )
        
    except Exception as e:
        raise DatabaseException(f"Error en logout: {str(e)}")


@router.get("/me", response_model=APIResponse[UserInfoData])
async def get_current_user_info(current_user: CurrentUser = Depends(get_current_user)):
    """
    Endpoint para obtener información del usuario actual.
    
    Útil para verificar si el token sigue siendo válido
    y obtener datos actualizados del usuario.
    
    Args:
        current_user: Usuario autenticado
        
    Returns:
        APIResponse[UserInfoData]: Respuesta estándar con información pública del usuario
    """
    
    user_info = UserInfoData(
        username=current_user.username,
    )
    
    return APIResponse.success(
        data=user_info,
        message="Información del usuario obtenida exitosamente"
    )