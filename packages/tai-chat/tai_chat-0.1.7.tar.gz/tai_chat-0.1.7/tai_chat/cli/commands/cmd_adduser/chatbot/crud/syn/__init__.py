# Este archivo ha sido generado automáticamente por tai-sql
# No modifiques este archivo directamente

from __future__ import annotations
from typing import Optional
from .session_manager import SyncSessionManager
from .dtos import *
from .daos import *

class ChatbotSyncDBAPI:
    """
    API principal para operaciones de base de datos síncronas.
    
    Esta clase proporciona acceso centralizado a todas las operaciones CRUD
    con gestión automática de sesiones SQLAlchemy. Implementa el patrón
    de fachada para simplificar el acceso a los diferentes modelos de datos.
    
    Características principales:
    - Gestión automática del ciclo de vida de sesiones
    - Acceso unificado a todos los modelos DAO
    - Soporte para operaciones transaccionales
    - Context managers para manejo de transacciones
    
    Atributos:
        session_manager (SyncSessionManager): Gestor de sesiones SQLAlchemy
        usuario (UsuarioSyncDAO): Operaciones CRUD para Usuario
        chat (ChatSyncDAO): Operaciones CRUD para Chat
        mensaje (MensajeSyncDAO): Operaciones CRUD para Mensaje
        token_usage (TokenUsageSyncDAO): Operaciones CRUD para TokenUsage
        user_stats (UserStatsSyncDAO): Operaciones CRUD para UserStats
        token_consumption_stats (TokenConsumptionStatsSyncDAO): Operaciones CRUD para TokenConsumptionStats
        chat_activity (ChatActivitySyncDAO): Operaciones CRUD para ChatActivity
    
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

    _instance: Optional[ChatbotSyncDBAPI] = None

    def __new__(cls) -> ChatbotSyncDBAPI:
        """Implementación del patrón Singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializa la API con un gestor de sesiones síncrono"""
        if not self._initialized:
            self._session_manager = SyncSessionManager()
            self._initialized = True
    
    @property
    def session_manager(self) -> SyncSessionManager:
        """
        Acceso al gestor de sesiones.
        
        El SessionManager proporciona:
        - get_session(): Context manager para sesiones individuales
        
        Returns:
            SyncSessionManager: Instancia del gestor de sesiones
        """
        return self._session_manager
    
    @property
    def usuario(self) -> UsuarioSyncDAO:
        """
        Acceso a operaciones CRUD para el modelo Usuario.
        
        Operaciones disponibles:
        - `find`: Buscar un registro por filtros
        - `find_many`: Buscar múltiples registros
        - `create`: Crear un nuevo registro
        - `create_many`: Crear múltiples registros
        - `update`: Actualizar registro existente
        - `update_many`: Actualizar registros existentes
        - `upsert`: Inserta o actualiza un registro
        - `upsert_many`: Inserta o actualiza múltiples registros
        - `delete`: Eliminar un registro
        - `delete_many`: Eliminar varios registros
        
        Returns:
            UsuarioSyncDAO: Instancia DAO para Usuario
        """
        return UsuarioSyncDAO(self._session_manager)

    @property
    def chat(self) -> ChatSyncDAO:
        """
        Acceso a operaciones CRUD para el modelo Chat.
        
        Operaciones disponibles:
        - `find`: Buscar un registro por filtros
        - `find_many`: Buscar múltiples registros
        - `create`: Crear un nuevo registro
        - `create_many`: Crear múltiples registros
        - `update`: Actualizar registro existente
        - `update_many`: Actualizar registros existentes
        - `upsert`: Inserta o actualiza un registro
        - `upsert_many`: Inserta o actualiza múltiples registros
        - `delete`: Eliminar un registro
        - `delete_many`: Eliminar varios registros
        
        Returns:
            ChatSyncDAO: Instancia DAO para Chat
        """
        return ChatSyncDAO(self._session_manager)

    @property
    def mensaje(self) -> MensajeSyncDAO:
        """
        Acceso a operaciones CRUD para el modelo Mensaje.
        
        Operaciones disponibles:
        - `find`: Buscar un registro por filtros
        - `find_many`: Buscar múltiples registros
        - `create`: Crear un nuevo registro
        - `create_many`: Crear múltiples registros
        - `update`: Actualizar registro existente
        - `update_many`: Actualizar registros existentes
        - `upsert`: Inserta o actualiza un registro
        - `upsert_many`: Inserta o actualiza múltiples registros
        - `delete`: Eliminar un registro
        - `delete_many`: Eliminar varios registros
        
        Returns:
            MensajeSyncDAO: Instancia DAO para Mensaje
        """
        return MensajeSyncDAO(self._session_manager)

    @property
    def token_usage(self) -> TokenUsageSyncDAO:
        """
        Acceso a operaciones CRUD para el modelo TokenUsage.
        
        Operaciones disponibles:
        - `find`: Buscar un registro por filtros
        - `find_many`: Buscar múltiples registros
        - `create`: Crear un nuevo registro
        - `create_many`: Crear múltiples registros
        - `update`: Actualizar registro existente
        - `update_many`: Actualizar registros existentes
        - `upsert`: Inserta o actualiza un registro
        - `upsert_many`: Inserta o actualiza múltiples registros
        - `delete`: Eliminar un registro
        - `delete_many`: Eliminar varios registros
        
        Returns:
            TokenUsageSyncDAO: Instancia DAO para TokenUsage
        """
        return TokenUsageSyncDAO(self._session_manager)

    @property
    def user_stats(self) -> UserStatsSyncDAO:
        """
        Acceso a operaciones CRUD para el modelo UserStats.
        
        Operaciones disponibles:
        - `find`: Buscar un registro por filtros
        - `find_many`: Buscar múltiples registros
        - `create`: Crear un nuevo registro
        - `create_many`: Crear múltiples registros
        - `update`: Actualizar registro existente
        - `update_many`: Actualizar registros existentes
        - `upsert`: Inserta o actualiza un registro
        - `upsert_many`: Inserta o actualiza múltiples registros
        - `delete`: Eliminar un registro
        - `delete_many`: Eliminar varios registros
        
        Returns:
            UserStatsSyncDAO: Instancia DAO para UserStats
        """
        return UserStatsSyncDAO(self._session_manager)

    @property
    def token_consumption_stats(self) -> TokenConsumptionStatsSyncDAO:
        """
        Acceso a operaciones CRUD para el modelo TokenConsumptionStats.
        
        Operaciones disponibles:
        - `find`: Buscar un registro por filtros
        - `find_many`: Buscar múltiples registros
        - `create`: Crear un nuevo registro
        - `create_many`: Crear múltiples registros
        - `update`: Actualizar registro existente
        - `update_many`: Actualizar registros existentes
        - `upsert`: Inserta o actualiza un registro
        - `upsert_many`: Inserta o actualiza múltiples registros
        - `delete`: Eliminar un registro
        - `delete_many`: Eliminar varios registros
        
        Returns:
            TokenConsumptionStatsSyncDAO: Instancia DAO para TokenConsumptionStats
        """
        return TokenConsumptionStatsSyncDAO(self._session_manager)

    @property
    def chat_activity(self) -> ChatActivitySyncDAO:
        """
        Acceso a operaciones CRUD para el modelo ChatActivity.
        
        Operaciones disponibles:
        - `find`: Buscar un registro por filtros
        - `find_many`: Buscar múltiples registros
        - `create`: Crear un nuevo registro
        - `create_many`: Crear múltiples registros
        - `update`: Actualizar registro existente
        - `update_many`: Actualizar registros existentes
        - `upsert`: Inserta o actualiza un registro
        - `upsert_many`: Inserta o actualiza múltiples registros
        - `delete`: Eliminar un registro
        - `delete_many`: Eliminar varios registros
        
        Returns:
            ChatActivitySyncDAO: Instancia DAO para ChatActivity
        """
        return ChatActivitySyncDAO(self._session_manager)

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
chatbot_api = ChatbotSyncDBAPI()

# Exportar tanto la clase como la instancia
__all__ = [
    'ChatbotSyncDBAPI',
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