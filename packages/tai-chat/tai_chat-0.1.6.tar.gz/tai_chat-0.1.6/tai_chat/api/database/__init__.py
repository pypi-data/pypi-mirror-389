# Este archivo ha sido generado automáticamente por tai-sql
# No modifiques este archivo directamente

from __future__ import annotations
from typing import Optional
from .session_manager import AsyncSessionManager
from .dtos import *
from .daos import *

class ChatbotAsyncDBAPI:
    """
    API principal para operaciones de base de datos asíncronas.
    
    Esta clase proporciona acceso centralizado a todas las operaciones DAO
    con gestión automática de sesiones SQLAlchemy. Implementa el patrón
    de fachada para simplificar el acceso a los diferentes modelos de datos.
    
    Características principales:
    - Gestión automática del ciclo de vida de sesiones
    - Acceso unificado a todos los modelos DAO
    - Soporte para operaciones transaccionales
    - Context managers para manejo de transacciones
    
    Atributos:
        session_manager (AsyncSessionManager): Gestor de sesiones SQLAlchemy
        usuario (UsuarioAsyncDAO): Operaciones DAO para Usuario
        chat (ChatAsyncDAO): Operaciones DAO para Chat
        mensaje (MensajeAsyncDAO): Operaciones DAO para Mensaje
        token_usage (TokenUsageAsyncDAO): Operaciones DAO para TokenUsage
        user_stats (UserStatsAsyncDAO): Operaciones DAO para UserStats
        token_consumption_stats (TokenConsumptionStatsAsyncDAO): Operaciones DAO para TokenConsumptionStats
        chat_activity (ChatActivityAsyncDAO): Operaciones DAO para ChatActivity
    
    Ejemplos de uso:
        ```python
        # Operaciones simples
        user = db_api.user.create(name="Juan", email="juan@email.com")
        found_user = db_api.user.find(email="juan@email.com")
        
        # Operaciones transaccionales
        with db_api.session_manager.get_session() as session:
            user = db_api.user.create(name="Ana", session=session)
            post = db_api.post.create(title="Post", author_id=user.id, session=session)
        ```
    """

    _instance: Optional[ChatbotAsyncDBAPI] = None

    def __new__(cls) -> ChatbotAsyncDBAPI:
        """Implementación del patrón Singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializa la API con un gestor de sesiones síncrono"""
        if not self._initialized:
            self._session_manager = AsyncSessionManager()
            self._initialized = True
    
    @property
    def session_manager(self) -> AsyncSessionManager:
        """
        Acceso al gestor de sesiones.
        
        El SessionManager proporciona:
        - get_session(): Context manager para sesiones individuales
        
        Returns:
            SyncSessionManager: Instancia del gestor de sesiones
        """
        return self._session_manager
    
    @property
    def usuario(self) -> UsuarioAsyncDAO:
        """
        Acceso a operaciones DAO para el modelo Usuario.
        
        Operaciones disponibles:
        - `find`: Buscar un registro por filtros
        - `find_many`: Buscar múltiples registros con paginación
        - `create`: Crear un nuevo registro
        - `create_many`: Crear múltiples registros
        - `update`: Actualizar registro existente
        - `update_many`: Actualizar registros existentes
        - `upsert`: Inserta o actualiza un registro
        - `upsert_many`: Inserta o actualiza múltiples registros
        - `delete`: Eliminar un registro
        - `delete_many`: Eliminar varios registros
        
        Returns:
            UsuarioAsyncDAO: Instancia DAO para Usuario
        """
        return UsuarioAsyncDAO(self._session_manager)

    @property
    def chat(self) -> ChatAsyncDAO:
        """
        Acceso a operaciones DAO para el modelo Chat.
        
        Operaciones disponibles:
        - `find`: Buscar un registro por filtros
        - `find_many`: Buscar múltiples registros con paginación
        - `create`: Crear un nuevo registro
        - `create_many`: Crear múltiples registros
        - `update`: Actualizar registro existente
        - `update_many`: Actualizar registros existentes
        - `upsert`: Inserta o actualiza un registro
        - `upsert_many`: Inserta o actualiza múltiples registros
        - `delete`: Eliminar un registro
        - `delete_many`: Eliminar varios registros
        
        Returns:
            ChatAsyncDAO: Instancia DAO para Chat
        """
        return ChatAsyncDAO(self._session_manager)

    @property
    def mensaje(self) -> MensajeAsyncDAO:
        """
        Acceso a operaciones DAO para el modelo Mensaje.
        
        Operaciones disponibles:
        - `find`: Buscar un registro por filtros
        - `find_many`: Buscar múltiples registros con paginación
        - `create`: Crear un nuevo registro
        - `create_many`: Crear múltiples registros
        - `update`: Actualizar registro existente
        - `update_many`: Actualizar registros existentes
        - `upsert`: Inserta o actualiza un registro
        - `upsert_many`: Inserta o actualiza múltiples registros
        - `delete`: Eliminar un registro
        - `delete_many`: Eliminar varios registros
        
        Returns:
            MensajeAsyncDAO: Instancia DAO para Mensaje
        """
        return MensajeAsyncDAO(self._session_manager)

    @property
    def token_usage(self) -> TokenUsageAsyncDAO:
        """
        Acceso a operaciones DAO para el modelo TokenUsage.
        
        Operaciones disponibles:
        - `find`: Buscar un registro por filtros
        - `find_many`: Buscar múltiples registros con paginación
        - `create`: Crear un nuevo registro
        - `create_many`: Crear múltiples registros
        - `update`: Actualizar registro existente
        - `update_many`: Actualizar registros existentes
        - `upsert`: Inserta o actualiza un registro
        - `upsert_many`: Inserta o actualiza múltiples registros
        - `delete`: Eliminar un registro
        - `delete_many`: Eliminar varios registros
        
        Returns:
            TokenUsageAsyncDAO: Instancia DAO para TokenUsage
        """
        return TokenUsageAsyncDAO(self._session_manager)

    @property
    def user_stats(self) -> UserStatsAsyncDAO:
        """
        Acceso a operaciones DAO para el modelo UserStats.
        
        Operaciones disponibles:
        - `find`: Buscar un registro por filtros
        - `find_many`: Buscar múltiples registros con paginación
        - `create`: Crear un nuevo registro
        - `create_many`: Crear múltiples registros
        - `update`: Actualizar registro existente
        - `update_many`: Actualizar registros existentes
        - `upsert`: Inserta o actualiza un registro
        - `upsert_many`: Inserta o actualiza múltiples registros
        - `delete`: Eliminar un registro
        - `delete_many`: Eliminar varios registros
        
        Returns:
            UserStatsAsyncDAO: Instancia DAO para UserStats
        """
        return UserStatsAsyncDAO(self._session_manager)

    @property
    def token_consumption_stats(self) -> TokenConsumptionStatsAsyncDAO:
        """
        Acceso a operaciones DAO para el modelo TokenConsumptionStats.
        
        Operaciones disponibles:
        - `find`: Buscar un registro por filtros
        - `find_many`: Buscar múltiples registros con paginación
        - `create`: Crear un nuevo registro
        - `create_many`: Crear múltiples registros
        - `update`: Actualizar registro existente
        - `update_many`: Actualizar registros existentes
        - `upsert`: Inserta o actualiza un registro
        - `upsert_many`: Inserta o actualiza múltiples registros
        - `delete`: Eliminar un registro
        - `delete_many`: Eliminar varios registros
        
        Returns:
            TokenConsumptionStatsAsyncDAO: Instancia DAO para TokenConsumptionStats
        """
        return TokenConsumptionStatsAsyncDAO(self._session_manager)

    @property
    def chat_activity(self) -> ChatActivityAsyncDAO:
        """
        Acceso a operaciones DAO para el modelo ChatActivity.
        
        Operaciones disponibles:
        - `find`: Buscar un registro por filtros
        - `find_many`: Buscar múltiples registros con paginación
        - `create`: Crear un nuevo registro
        - `create_many`: Crear múltiples registros
        - `update`: Actualizar registro existente
        - `update_many`: Actualizar registros existentes
        - `upsert`: Inserta o actualiza un registro
        - `upsert_many`: Inserta o actualiza múltiples registros
        - `delete`: Eliminar un registro
        - `delete_many`: Eliminar varios registros
        
        Returns:
            ChatActivityAsyncDAO: Instancia DAO para ChatActivity
        """
        return ChatActivityAsyncDAO(self._session_manager)

    @property
    def message_role(self) -> EnumModel:
        """
        Acceso a operaciones para el Enum message_role.
        
        Operaciones disponibles:
        - `find_many`: Devuelve la lista de posibilidades
        
        Returns:
            EnumModel: Instancia para message_role
        """
        return EnumModel(name="message_role", values=['usuario', 'asistente', 'sistema'])

# Instancia global para fácil acceso
chatbot_api = ChatbotAsyncDBAPI()

# Exportar tanto la clase como la instancia
__all__ = [
    'ChatbotAsyncDBAPI',
    'chatbot_api',
    'UsuarioRead',
    'UsuarioCreate',
    'UsuarioFilter',
    'UsuarioUpdate',
    'UsuarioUpdateValues',
    'ChatRead',
    'ChatCreate',
    'ChatFilter',
    'ChatUpdate',
    'ChatUpdateValues',
    'MensajeRead',
    'MensajeCreate',
    'MensajeFilter',
    'MensajeUpdate',
    'MensajeUpdateValues',
    'TokenUsageRead',
    'TokenUsageCreate',
    'TokenUsageFilter',
    'TokenUsageUpdate',
    'TokenUsageUpdateValues',
    'UserStatsRead',
    'TokenConsumptionStatsRead',
    'ChatActivityRead',
]