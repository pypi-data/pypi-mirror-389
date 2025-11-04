# Este archivo ha sido generado automáticamente por tai-sql
# No modifiques este archivo directamente
from __future__ import annotations
from typing import (
    List,
    Optional,
    Dict,
    Any
)
from .models import *
from pydantic import (
    BaseModel,
    Field,
    ConfigDict
)
from tai_alphi import Alphi

from .utils import (
    should_include_relation,
    get_nested_includes
)
from datetime import datetime, date, time

# Logger
logger = Alphi.get_logger_by_name("tai-chatbot")

# General Enum class
class EnumModel:

    def __init__(self, name: str, values: List[str]):
        self.name = name
        self.values = values
    
    def find_many(self) -> List[str]:
        """
        Devuelve una lista de los valores del Enum.
        
        Returns:
            List[str]: Lista de valores del Enum
        """
        logger.info(f"Obteniendo valores del Enum '{self.name}' - {len(self.values)} valores disponibles")
        return self.values


class UsuarioRead(BaseModel):
    """
    Data Transfer Object de lectura para Usuario.
    
    Tabla que almacena información de los usuarios del chatbot
    
    Este modelo se utiliza como respuesta en endpoints de la API que devuelven
    información de usuario existentes en la base de datos.
    
    Campos de la tabla:
        - username (str): Nombre de usuario único
        - password (str): Contraseña encriptada
        - email (str, opcional): Correo electrónico del usuario
        - avatar (str, opcional): URL del avatar del usuario
        - session_id (str, opcional): ID de la sesión activa del usuario
        - created_at (datetime): Fecha de creación del usuario
        - updated_at (datetime): Fecha de última actualización
        - is_active (bool): Estado activo del usuario
    
    Relaciones disponibles (usar con parámetro 'includes'):
        - chats: Lista de Chat relacionados (one-to-many)
            Tabla que almacena las conversaciones del chatbot
    
    Uso del parámetro 'includes':
        Para cargar relaciones específicas, usa el parámetro 'includes' en la consulta:
        
        Ejemplos básicos:
        ```python
        # Solo datos básicos de Usuario
        Un registro > GET /usuario/{username}
        or
        Varios registros > GET /usuario
        
        # Incluir chats
        Un registro > GET /usuario/{username}?includes=chats
        or
        Varios registros > GET /usuario?includes=chats
        
        # Relaciones anidadas (hasta 5 niveles):
        # chats con sus propias relaciones
        Un registro > GET /usuario/{username}?includes=chats.{nested_relation}
        or
        Varios registros > GET /usuario?includes=chats.{nested_relation}
        ```
    
    Casos de uso típicos:
        - Consulta básica: Obtener usuario sin relaciones (rápido)
        - Con chats: Para mostrar usuario con todos sus chats
        - Consulta completa: Todas las relaciones para vistas detalladas
    
    
    Rendimiento:
        - Sin includes: Consulta rápida, solo tabla Usuario
        - Con chats: Carga múltiples registros de Chat
        - Máxima profundidad de anidación: 5 niveles
    """

    username: str = Field(
        description="Nombre de usuario único",
    )

    password: str = Field(
        description="Contraseña encriptada",
    )

    email: Optional[str] = Field(
        description="Correo electrónico del usuario",
    )

    avatar: Optional[str] = Field(
        description="URL del avatar del usuario",
    )

    session_id: Optional[str] = Field(
        description="ID de la sesión activa del usuario",
    )

    created_at: datetime = Field(
        description="Fecha de creación del usuario",
    )

    updated_at: datetime = Field(
        description="Fecha de última actualización",
    )

    is_active: bool = Field(
        description="Estado activo del usuario",
    )


    chats: Optional[List[ChatRead]] = Field(
        default=None,
        description="""
        Lista de Chat relacionados con este Usuario.
        
        Tabla que almacena las conversaciones del chatbot
        
        Para cargar esta relación, incluye 'chats' en el parámetro includes:
        - includes=chats → Carga Chats básicos
        - includes=chats.{nested} → Carga con relaciones anidadas
        
        Relación: Usuario 1:N Chat (un usuario puede tener múltiples chats)
        """
    )

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    @classmethod
    def from_instance(
        cls,
        instance: Usuario,
        includes: Optional[List[str]] = None,
        max_depth: int = 5
    ) -> UsuarioRead:
        """
        Crea un DTO desde una instancia del modelo SQLAlchemy con carga optimizada de relaciones.
        
        Args:
            instance: Instancia del modelo Usuario
            includes: Lista de relaciones a incluir (formato: 'relation' o 'relation.nested_relation')
            max_depth: Profundidad máxima de anidación para evitar recursión infinita
            
        Returns:
            UsuarioRead: Instancia del DTO
        """

        # Construir DTO base
        dto_data = {
            'username': instance.username,
            'password': instance.password,
            'email': instance.email,
            'avatar': instance.avatar,
            'session_id': instance.session_id,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
            'is_active': instance.is_active,
        }

        # Procesar relaciones con control de profundidad
        if includes is not None and max_depth > 0:
            # Relación 1:N - chats
            if should_include_relation('chats', includes):
                nested_includes = get_nested_includes('chats', includes)
                # Este check debería cumplirse siempre, es por seguridad
                if hasattr(instance, 'chats') and instance.chats is not None:
                    dto_data['chats'] = [
                        ChatRead.from_instance(
                            reg, 
                            nested_includes, 
                            max_depth - 1
                        ) 
                        for reg in instance.chats
                    ]

        return cls(**dto_data)

    @classmethod
    def from_created_instance(cls, instance: Usuario, included: set[str], excluded: str=None) -> UsuarioRead:
        """
        Crea un DTO desde una instancia del modelo SQLAlchemy
        
        Args:
            instance: Instancia del modelo Usuario
            
        Returns:
            UsuarioCreate: Instancia del DTO
        """

        # Construir DTO base
        dto_data = {
            'username': instance.username,
            'password': instance.password,
            'email': instance.email,
            'avatar': instance.avatar,
            'session_id': instance.session_id,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
            'is_active': instance.is_active,
        }


        # Evaluación lazy de relaciones costosas
        if 'chats' in included and not 'chats' == excluded and hasattr(instance, 'chats') and getattr(instance, 'chats') is not None:
            dto_data['chats'] = [
                ChatRead.from_created_instance(reg, included, 'usuario') 
                for reg in instance.chats
            ]

        return cls(**dto_data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UsuarioRead:
        """
        Crea un DTO desde un diccionario
        
        Args:
            data: Diccionario con los datos del DTO
            
        Returns:
            UsuarioRead: Instancia del DTO
        """
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class UsuarioCreate(BaseModel):
    """Data Transfer Object de escritura para Usuario. Define objetos para ser creados en la base de datos."""
    username: str
    password: str
    email: Optional[str] = None
    avatar: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True

    chats: Optional[List[ChatCreate]] = None

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    def to_instance(self) -> Usuario:
        """
        Crea una instancia del modelo SQLAlchemy desde el DTO
        
        Returns:
            Usuario: Instancia del modelo SQLAlchemy
        """

        model = Usuario(
            username=self.username,
            password=self.password,
            email=self.email,
            avatar=self.avatar,
            session_id=self.session_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_active=self.is_active,
        )
        
        # Evaluación lazy de relaciones costosas
        if self.chats is not None:
            chats = [Chat(**reg.to_dict()) for reg in self.chats]
            model.chats = chats

        return model
    
    @classmethod
    def from_instance(cls, instance: Usuario) -> UsuarioCreate:
        """
        Crea un DTO desde una instancia del modelo SQLAlchemy
        
        Args:
            instance: Instancia del modelo Usuario
            
        Returns:
            UsuarioCreate: Instancia del DTO
        """

        # Construir DTO base
        dto_data = {
            'username': instance.username,
            'password': instance.password,
            'email': instance.email,
            'avatar': instance.avatar,
            'session_id': instance.session_id,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
            'is_active': instance.is_active,
        }


        # Evaluación lazy de relaciones costosas
        if hasattr(instance, 'chats') and getattr(instance, 'chats') is not None:
            dto_data['chats'] = [
                ChatCreate.from_instance(reg) 
                for reg in instance.chats
            ]

        return cls(**dto_data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UsuarioRead:
        """
        Crea un DTO desde un diccionario
        
        Args:
            data: Diccionario con los datos del DTO
            
        Returns:
            UsuarioRead: Instancia del DTO
        """
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class UsuarioFilter(BaseModel):
    """Data Transfer Object de actualización para Usuario.
    Define los filtros que sirven para buscar registros en la DB."""
    username: str = None
    password: str = None
    email: str = None
    avatar: str = None
    session_id: str = None
    created_at: datetime = None
    updated_at: datetime = None
    is_active: bool = None

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_unset=True)


class UsuarioUpdateValues(BaseModel):
    """Data Transfer Object de actualización para Usuario.
    Define los valores que se modificarán en los registros correspondientes."""
    username: str = None
    password: str = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    is_active: bool = None

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_unset=True)


class UsuarioUpdate(BaseModel):
    """Data Transfer Object de actualización para Usuario."""
    filter: UsuarioFilter
    values: UsuarioUpdateValues

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )


class ChatRead(BaseModel):
    """
    Data Transfer Object de lectura para Chat.
    
    Tabla que almacena las conversaciones del chatbot
    
    Este modelo se utiliza como respuesta en endpoints de la API que devuelven
    información de chat existentes en la base de datos.
    
    Campos de la tabla:
        - id (int): UUID del chat
        - title (str): Título de la conversación
        - username (str): ID del usuario propietario del chat
        - created_at (datetime): Fecha de creación del chat
        - updated_at (datetime): Fecha de última actualización
        - is_active (bool): Estado activo del chat
    
    Relaciones disponibles (usar con parámetro 'includes'):
        - messages: Lista de Mensaje relacionados (one-to-many)
            Tabla que almacena los mensajes individuales de cada chat
        - usuario: Usuario relacionado (many-to-one)
            Tabla que almacena información de los usuarios del chatbot
    
    Uso del parámetro 'includes':
        Para cargar relaciones específicas, usa el parámetro 'includes' en la consulta:
        
        Ejemplos básicos:
        ```python
        # Solo datos básicos de Chat
        Un registro > GET /chat/{id}
        or
        Varios registros > GET /chat
        
        # Incluir messages
        Un registro > GET /chat/{id}?includes=messages
        or
        Varios registros > GET /chat?includes=messages
        
        # Incluir usuario
        Un registro > GET /chat/{id}?includes=usuario
        or
        Varios registros > GET /chat?includes=usuario
        
        # Múltiples relaciones en una sola consulta
        Un registro > GET /chat/{id}?includes=messages&includes=usuario
        or
        Varios registros > GET /chat?includes=messages&includes=usuario
        
        # Relaciones anidadas (hasta 5 niveles):
        # messages con sus propias relaciones
        Un registro > GET /chat/{id}?includes=messages.{nested_relation}
        or
        Varios registros > GET /chat?includes=messages.{nested_relation}
        # usuario con sus propias relaciones
        Un registro > GET /chat/{id}?includes=usuario.{nested_relation}
        or
        Varios registros > GET /chat?includes=usuario.{nested_relation}
        ```
    
    Casos de uso típicos:
        - Consulta básica: Obtener chat sin relaciones (rápido)
        - Con messages: Para mostrar chat con todos sus mensajes
        - Con usuario: Para mostrar chat con su usuario relacionado
        - Consulta completa: Todas las relaciones para vistas detalladas
    
    
    Rendimiento:
        - Sin includes: Consulta rápida, solo tabla Chat
        - Con messages: Carga múltiples registros de Mensaje
        - Con usuario: Una consulta adicional para Usuario
        - Máxima profundidad de anidación: 5 niveles
    """

    id: int = Field(
        description="UUID del chat",
    )

    title: str = Field(
        description="Título de la conversación",
    )

    username: str = Field(
        description="ID del usuario propietario del chat",
    )

    created_at: datetime = Field(
        description="Fecha de creación del chat",
    )

    updated_at: datetime = Field(
        description="Fecha de última actualización",
    )

    is_active: bool = Field(
        description="Estado activo del chat",
    )


    messages: Optional[List[MensajeRead]] = Field(
        default=None,
        description="""
        Lista de Mensaje relacionados con este Chat.
        
        Tabla que almacena los mensajes individuales de cada chat
        
        Para cargar esta relación, incluye 'messages' en el parámetro includes:
        - includes=messages → Carga Mensajes básicos
        - includes=messages.{nested} → Carga con relaciones anidadas
        
        Relación: Chat 1:N Mensaje (un chat puede tener múltiples mensajes)
        """
    )

    usuario: Optional[UsuarioRead] = Field(
        default=None,
        description="""
        Usuario relacionado con este Chat.
        
        Tabla que almacena información de los usuarios del chatbot
        
        Para cargar esta relación, incluye 'usuario' en el parámetro includes:
        - includes=usuario → Carga Usuario básico
        - includes=usuario.{nested} → Carga con relaciones anidadas
        
        Relación: Chat N:1 Usuario (múltiples chats pueden tener el mismo usuario)
        """
    )

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    @classmethod
    def from_instance(
        cls,
        instance: Chat,
        includes: Optional[List[str]] = None,
        max_depth: int = 5
    ) -> ChatRead:
        """
        Crea un DTO desde una instancia del modelo SQLAlchemy con carga optimizada de relaciones.
        
        Args:
            instance: Instancia del modelo Chat
            includes: Lista de relaciones a incluir (formato: 'relation' o 'relation.nested_relation')
            max_depth: Profundidad máxima de anidación para evitar recursión infinita
            
        Returns:
            ChatRead: Instancia del DTO
        """

        # Construir DTO base
        dto_data = {
            'id': instance.id,
            'title': instance.title,
            'username': instance.username,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
            'is_active': instance.is_active,
        }

        # Procesar relaciones con control de profundidad
        if includes is not None and max_depth > 0:
            # Relación 1:N - messages
            if should_include_relation('messages', includes):
                nested_includes = get_nested_includes('messages', includes)
                # Este check debería cumplirse siempre, es por seguridad
                if hasattr(instance, 'messages') and instance.messages is not None:
                    dto_data['messages'] = [
                        MensajeRead.from_instance(
                            reg, 
                            nested_includes, 
                            max_depth - 1
                        ) 
                        for reg in instance.messages
                    ]

            # Relación N:1 - usuario
            if should_include_relation('usuario', includes):
                nested_includes = get_nested_includes('usuario', includes)
                # Este check debería cumplirse siempre, es por seguridad
                if hasattr(instance, 'usuario') and instance.usuario is not None:
                    dto_data['usuario'] = UsuarioRead.from_instance(
                        instance.usuario, 
                        nested_includes, 
                        max_depth - 1
                    )

        return cls(**dto_data)

    @classmethod
    def from_created_instance(cls, instance: Chat, included: set[str], excluded: str=None) -> ChatRead:
        """
        Crea un DTO desde una instancia del modelo SQLAlchemy
        
        Args:
            instance: Instancia del modelo Chat
            
        Returns:
            ChatCreate: Instancia del DTO
        """

        # Construir DTO base
        dto_data = {
            'id': instance.id,
            'title': instance.title,
            'username': instance.username,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
            'is_active': instance.is_active,
        }


        # Evaluación lazy de relaciones costosas
        if 'messages' in included and not 'messages' == excluded and hasattr(instance, 'messages') and getattr(instance, 'messages') is not None:
            dto_data['messages'] = [
                MensajeRead.from_created_instance(reg, included, 'chat') 
                for reg in instance.messages
            ]
        if 'usuario' in included and not 'usuario' == excluded and hasattr(instance, 'usuario') and getattr(instance, 'usuario') is not None:
            dto_data['usuario'] = UsuarioRead.from_created_instance(
                instance.usuario, included, 'chats'
            )

        return cls(**dto_data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChatRead:
        """
        Crea un DTO desde un diccionario
        
        Args:
            data: Diccionario con los datos del DTO
            
        Returns:
            ChatRead: Instancia del DTO
        """
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class ChatCreate(BaseModel):
    """Data Transfer Object de escritura para Chat. Define objetos para ser creados en la base de datos."""
    title: str
    username: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True

    messages: Optional[List[MensajeCreate]] = None
    usuario: Optional[UsuarioCreate] = None

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    def to_instance(self) -> Chat:
        """
        Crea una instancia del modelo SQLAlchemy desde el DTO
        
        Returns:
            Chat: Instancia del modelo SQLAlchemy
        """

        model = Chat(
            title=self.title,
            username=self.username,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_active=self.is_active,
        )
        
        # Evaluación lazy de relaciones costosas
        if self.messages is not None:
            messages = [Mensaje(**reg.to_dict()) for reg in self.messages]
            model.messages = messages
        if self.usuario is not None:
            usuario = Usuario(**self.usuario.to_dict())
            model.usuario = usuario

        return model
    
    @classmethod
    def from_instance(cls, instance: Chat) -> ChatCreate:
        """
        Crea un DTO desde una instancia del modelo SQLAlchemy
        
        Args:
            instance: Instancia del modelo Chat
            
        Returns:
            ChatCreate: Instancia del DTO
        """

        # Construir DTO base
        dto_data = {
            'id': instance.id,
            'title': instance.title,
            'username': instance.username,
            'created_at': instance.created_at,
            'updated_at': instance.updated_at,
            'is_active': instance.is_active,
        }


        # Evaluación lazy de relaciones costosas
        if hasattr(instance, 'messages') and getattr(instance, 'messages') is not None:
            dto_data['messages'] = [
                MensajeCreate.from_instance(reg) 
                for reg in instance.messages
            ]
        if hasattr(instance, 'usuario') and getattr(instance, 'usuario') is not None:
            dto_data['usuario'] = UsuarioCreate.from_instance(
                instance.usuario
            )

        return cls(**dto_data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChatRead:
        """
        Crea un DTO desde un diccionario
        
        Args:
            data: Diccionario con los datos del DTO
            
        Returns:
            ChatRead: Instancia del DTO
        """
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class ChatFilter(BaseModel):
    """Data Transfer Object de actualización para Chat.
    Define los filtros que sirven para buscar registros en la DB."""
    title: str = None
    username: str = None
    created_at: datetime = None
    updated_at: datetime = None
    is_active: bool = None

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_unset=True)


class ChatUpdateValues(BaseModel):
    """Data Transfer Object de actualización para Chat.
    Define los valores que se modificarán en los registros correspondientes."""
    title: str = None
    username: str = None
    created_at: datetime = None
    updated_at: datetime = None
    is_active: bool = None

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_unset=True)


class ChatUpdate(BaseModel):
    """Data Transfer Object de actualización para Chat."""
    filter: ChatFilter
    values: ChatUpdateValues

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )


class MensajeRead(BaseModel):
    """
    Data Transfer Object de lectura para Mensaje.
    
    Tabla que almacena los mensajes individuales de cada chat
    
    Este modelo se utiliza como respuesta en endpoints de la API que devuelven
    información de mensaje existentes en la base de datos.
    
    Campos de la tabla:
        - id (int): UUID del mensaje
        - content (str): Contenido del mensaje
        - role (str): Rol del mensaje (user, assistant, system)
        - timestamp (datetime): Timestamp del mensaje
        - chat_id (int): ID del chat al que pertenece el mensaje
    
    Relaciones disponibles (usar con parámetro 'includes'):
        - token_usage: Lista de TokenUsage relacionados (one-to-many)
            Tabla que almacena el consumo de tokens para métricas y facturación
        - chat: Chat relacionado (many-to-one)
            Tabla que almacena las conversaciones del chatbot
    
    Uso del parámetro 'includes':
        Para cargar relaciones específicas, usa el parámetro 'includes' en la consulta:
        
        Ejemplos básicos:
        ```python
        # Solo datos básicos de Mensaje
        Un registro > GET /mensaje/{id}
        or
        Varios registros > GET /mensaje
        
        # Incluir token_usage
        Un registro > GET /mensaje/{id}?includes=token_usage
        or
        Varios registros > GET /mensaje?includes=token_usage
        
        # Incluir chat
        Un registro > GET /mensaje/{id}?includes=chat
        or
        Varios registros > GET /mensaje?includes=chat
        
        # Múltiples relaciones en una sola consulta
        Un registro > GET /mensaje/{id}?includes=token_usage&includes=chat
        or
        Varios registros > GET /mensaje?includes=token_usage&includes=chat
        
        # Relaciones anidadas (hasta 5 niveles):
        # token_usage con sus propias relaciones
        Un registro > GET /mensaje/{id}?includes=token_usage.{nested_relation}
        or
        Varios registros > GET /mensaje?includes=token_usage.{nested_relation}
        # chat con sus propias relaciones
        Un registro > GET /mensaje/{id}?includes=chat.{nested_relation}
        or
        Varios registros > GET /mensaje?includes=chat.{nested_relation}
        ```
    
    Casos de uso típicos:
        - Consulta básica: Obtener mensaje sin relaciones (rápido)
        - Con token_usage: Para mostrar mensaje con todos sus tokenusages
        - Con chat: Para mostrar mensaje con su chat relacionado
        - Consulta completa: Todas las relaciones para vistas detalladas
    
    
    Rendimiento:
        - Sin includes: Consulta rápida, solo tabla Mensaje
        - Con token_usage: Carga múltiples registros de TokenUsage
        - Con chat: Una consulta adicional para Chat
        - Máxima profundidad de anidación: 5 niveles
    """

    id: int = Field(
        description="UUID del mensaje",
    )

    content: str = Field(
        description="Contenido del mensaje",
    )

    role: str = Field(
        description="Rol del mensaje (user, assistant, system)",
    )

    timestamp: datetime = Field(
        description="Timestamp del mensaje",
    )

    chat_id: int = Field(
        description="ID del chat al que pertenece el mensaje",
    )


    token_usage: Optional[List[TokenUsageRead]] = Field(
        default=None,
        description="""
        Lista de TokenUsage relacionados con este Mensaje.
        
        Tabla que almacena el consumo de tokens para métricas y facturación
        
        Para cargar esta relación, incluye 'token_usage' en el parámetro includes:
        - includes=token_usage → Carga TokenUsages básicos
        - includes=token_usage.{nested} → Carga con relaciones anidadas
        
        Relación: Mensaje 1:N TokenUsage (un mensaje puede tener múltiples tokenusages)
        """
    )

    chat: Optional[ChatRead] = Field(
        default=None,
        description="""
        Chat relacionado con este Mensaje.
        
        Tabla que almacena las conversaciones del chatbot
        
        Para cargar esta relación, incluye 'chat' en el parámetro includes:
        - includes=chat → Carga Chat básico
        - includes=chat.{nested} → Carga con relaciones anidadas
        
        Relación: Mensaje N:1 Chat (múltiples mensajes pueden tener el mismo chat)
        """
    )

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    @classmethod
    def from_instance(
        cls,
        instance: Mensaje,
        includes: Optional[List[str]] = None,
        max_depth: int = 5
    ) -> MensajeRead:
        """
        Crea un DTO desde una instancia del modelo SQLAlchemy con carga optimizada de relaciones.
        
        Args:
            instance: Instancia del modelo Mensaje
            includes: Lista de relaciones a incluir (formato: 'relation' o 'relation.nested_relation')
            max_depth: Profundidad máxima de anidación para evitar recursión infinita
            
        Returns:
            MensajeRead: Instancia del DTO
        """

        # Construir DTO base
        dto_data = {
            'id': instance.id,
            'content': instance.content,
            'role': instance.role,
            'timestamp': instance.timestamp,
            'chat_id': instance.chat_id,
        }

        # Procesar relaciones con control de profundidad
        if includes is not None and max_depth > 0:
            # Relación 1:N - token_usage
            if should_include_relation('token_usage', includes):
                nested_includes = get_nested_includes('token_usage', includes)
                # Este check debería cumplirse siempre, es por seguridad
                if hasattr(instance, 'token_usage') and instance.token_usage is not None:
                    dto_data['token_usage'] = [
                        TokenUsageRead.from_instance(
                            reg, 
                            nested_includes, 
                            max_depth - 1
                        ) 
                        for reg in instance.token_usage
                    ]

            # Relación N:1 - chat
            if should_include_relation('chat', includes):
                nested_includes = get_nested_includes('chat', includes)
                # Este check debería cumplirse siempre, es por seguridad
                if hasattr(instance, 'chat') and instance.chat is not None:
                    dto_data['chat'] = ChatRead.from_instance(
                        instance.chat, 
                        nested_includes, 
                        max_depth - 1
                    )

        return cls(**dto_data)

    @classmethod
    def from_created_instance(cls, instance: Mensaje, included: set[str], excluded: str=None) -> MensajeRead:
        """
        Crea un DTO desde una instancia del modelo SQLAlchemy
        
        Args:
            instance: Instancia del modelo Mensaje
            
        Returns:
            MensajeCreate: Instancia del DTO
        """

        # Construir DTO base
        dto_data = {
            'id': instance.id,
            'content': instance.content,
            'role': instance.role,
            'timestamp': instance.timestamp,
            'chat_id': instance.chat_id,
        }


        # Evaluación lazy de relaciones costosas
        if 'token_usage' in included and not 'token_usage' == excluded and hasattr(instance, 'token_usage') and getattr(instance, 'token_usage') is not None:
            dto_data['token_usage'] = [
                TokenUsageRead.from_created_instance(reg, included, 'message') 
                for reg in instance.token_usage
            ]
        if 'chat' in included and not 'chat' == excluded and hasattr(instance, 'chat') and getattr(instance, 'chat') is not None:
            dto_data['chat'] = ChatRead.from_created_instance(
                instance.chat, included, 'messages'
            )

        return cls(**dto_data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MensajeRead:
        """
        Crea un DTO desde un diccionario
        
        Args:
            data: Diccionario con los datos del DTO
            
        Returns:
            MensajeRead: Instancia del DTO
        """
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class MensajeCreate(BaseModel):
    """Data Transfer Object de escritura para Mensaje. Define objetos para ser creados en la base de datos."""
    content: str
    role: str
    timestamp: datetime = Field(default_factory=datetime.now)
    chat_id: Optional[int] = None

    token_usage: Optional[List[TokenUsageCreate]] = None
    chat: Optional[ChatCreate] = None

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    def to_instance(self) -> Mensaje:
        """
        Crea una instancia del modelo SQLAlchemy desde el DTO
        
        Returns:
            Mensaje: Instancia del modelo SQLAlchemy
        """

        model = Mensaje(
            content=self.content,
            role=self.role,
            timestamp=self.timestamp,
            chat_id=self.chat_id,
        )
        
        # Evaluación lazy de relaciones costosas
        if self.token_usage is not None:
            token_usage = [TokenUsage(**reg.to_dict()) for reg in self.token_usage]
            model.token_usage = token_usage
        if self.chat is not None:
            chat = Chat(**self.chat.to_dict())
            model.chat = chat

        return model
    
    @classmethod
    def from_instance(cls, instance: Mensaje) -> MensajeCreate:
        """
        Crea un DTO desde una instancia del modelo SQLAlchemy
        
        Args:
            instance: Instancia del modelo Mensaje
            
        Returns:
            MensajeCreate: Instancia del DTO
        """

        # Construir DTO base
        dto_data = {
            'id': instance.id,
            'content': instance.content,
            'role': instance.role,
            'timestamp': instance.timestamp,
            'chat_id': instance.chat_id,
        }


        # Evaluación lazy de relaciones costosas
        if hasattr(instance, 'token_usage') and getattr(instance, 'token_usage') is not None:
            dto_data['token_usage'] = [
                TokenUsageCreate.from_instance(reg) 
                for reg in instance.token_usage
            ]
        if hasattr(instance, 'chat') and getattr(instance, 'chat') is not None:
            dto_data['chat'] = ChatCreate.from_instance(
                instance.chat
            )

        return cls(**dto_data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MensajeRead:
        """
        Crea un DTO desde un diccionario
        
        Args:
            data: Diccionario con los datos del DTO
            
        Returns:
            MensajeRead: Instancia del DTO
        """
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class MensajeFilter(BaseModel):
    """Data Transfer Object de actualización para Mensaje.
    Define los filtros que sirven para buscar registros en la DB."""
    content: str = None
    role: str = None
    timestamp: datetime = None
    chat_id: int = None

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_unset=True)


class MensajeUpdateValues(BaseModel):
    """Data Transfer Object de actualización para Mensaje.
    Define los valores que se modificarán en los registros correspondientes."""
    content: str = None
    role: str = None
    timestamp: datetime = None
    chat_id: int = None

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_unset=True)


class MensajeUpdate(BaseModel):
    """Data Transfer Object de actualización para Mensaje."""
    filter: MensajeFilter
    values: MensajeUpdateValues

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )


class TokenUsageRead(BaseModel):
    """
    Data Transfer Object de lectura para TokenUsage.
    
    Tabla que almacena el consumo de tokens para métricas y facturación
    
    Este modelo se utiliza como respuesta en endpoints de la API que devuelven
    información de token_usage existentes en la base de datos.
    
    Campos de la tabla:
        - id (int): Campo id de la tabla token_usage
        - prompt_tokens (int): Tokens consumidos en el prompt
        - completion_tokens (int): Tokens consumidos en la respuesta
        - total_tokens (int): Total de tokens consumidos
        - model_name (str): Nombre del modelo utilizado
        - provider (str): Proveedor del modelo (OpenAI, Anthropic, etc.)
        - cost_usd (float, opcional): Costo estimado en USD
        - timestamp (datetime): Timestamp del consumo
        - message_id (int): ID del mensaje asociado
    
    Relaciones disponibles (usar con parámetro 'includes'):
        - message: Mensaje relacionado (many-to-one)
            Tabla que almacena los mensajes individuales de cada chat
    
    Uso del parámetro 'includes':
        Para cargar relaciones específicas, usa el parámetro 'includes' en la consulta:
        
        Ejemplos básicos:
        ```python
        # Solo datos básicos de TokenUsage
        Un registro > GET /token_usage/{id}
        or
        Varios registros > GET /token_usage
        
        # Incluir message
        Un registro > GET /token_usage/{id}?includes=message
        or
        Varios registros > GET /token_usage?includes=message
        
        # Relaciones anidadas (hasta 5 niveles):
        # message con sus propias relaciones
        Un registro > GET /token_usage/{id}?includes=message.{nested_relation}
        or
        Varios registros > GET /token_usage?includes=message.{nested_relation}
        ```
    
    Casos de uso típicos:
        - Consulta básica: Obtener token_usage sin relaciones (rápido)
        - Con message: Para mostrar token_usage con su mensaje relacionado
        - Consulta completa: Todas las relaciones para vistas detalladas
    
    
    Rendimiento:
        - Sin includes: Consulta rápida, solo tabla TokenUsage
        - Con message: Una consulta adicional para Mensaje
        - Máxima profundidad de anidación: 5 niveles
    """

    id: int = Field(
        description="Campo id de la tabla token_usage",
    )

    prompt_tokens: int = Field(
        description="Tokens consumidos en el prompt",
    )

    completion_tokens: int = Field(
        description="Tokens consumidos en la respuesta",
    )

    total_tokens: int = Field(
        description="Total de tokens consumidos",
    )

    model_name: str = Field(
        description="Nombre del modelo utilizado",
    )

    provider: str = Field(
        description="Proveedor del modelo (OpenAI, Anthropic, etc.)",
    )

    cost_usd: Optional[float] = Field(
        description="Costo estimado en USD",
    )

    timestamp: datetime = Field(
        description="Timestamp del consumo",
    )

    message_id: int = Field(
        description="ID del mensaje asociado",
    )


    message: Optional[MensajeRead] = Field(
        default=None,
        description="""
        Mensaje relacionado con este TokenUsage.
        
        Tabla que almacena los mensajes individuales de cada chat
        
        Para cargar esta relación, incluye 'message' en el parámetro includes:
        - includes=message → Carga Mensaje básico
        - includes=message.{nested} → Carga con relaciones anidadas
        
        Relación: TokenUsage N:1 Mensaje (múltiples token_usages pueden tener el mismo mensaje)
        """
    )

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    @classmethod
    def from_instance(
        cls,
        instance: TokenUsage,
        includes: Optional[List[str]] = None,
        max_depth: int = 5
    ) -> TokenUsageRead:
        """
        Crea un DTO desde una instancia del modelo SQLAlchemy con carga optimizada de relaciones.
        
        Args:
            instance: Instancia del modelo TokenUsage
            includes: Lista de relaciones a incluir (formato: 'relation' o 'relation.nested_relation')
            max_depth: Profundidad máxima de anidación para evitar recursión infinita
            
        Returns:
            TokenUsageRead: Instancia del DTO
        """

        # Construir DTO base
        dto_data = {
            'id': instance.id,
            'prompt_tokens': instance.prompt_tokens,
            'completion_tokens': instance.completion_tokens,
            'total_tokens': instance.total_tokens,
            'model_name': instance.model_name,
            'provider': instance.provider,
            'cost_usd': instance.cost_usd,
            'timestamp': instance.timestamp,
            'message_id': instance.message_id,
        }

        # Procesar relaciones con control de profundidad
        if includes is not None and max_depth > 0:
            # Relación N:1 - message
            if should_include_relation('message', includes):
                nested_includes = get_nested_includes('message', includes)
                # Este check debería cumplirse siempre, es por seguridad
                if hasattr(instance, 'message') and instance.message is not None:
                    dto_data['message'] = MensajeRead.from_instance(
                        instance.message, 
                        nested_includes, 
                        max_depth - 1
                    )

        return cls(**dto_data)

    @classmethod
    def from_created_instance(cls, instance: TokenUsage, included: set[str], excluded: str=None) -> TokenUsageRead:
        """
        Crea un DTO desde una instancia del modelo SQLAlchemy
        
        Args:
            instance: Instancia del modelo TokenUsage
            
        Returns:
            TokenUsageCreate: Instancia del DTO
        """

        # Construir DTO base
        dto_data = {
            'id': instance.id,
            'prompt_tokens': instance.prompt_tokens,
            'completion_tokens': instance.completion_tokens,
            'total_tokens': instance.total_tokens,
            'model_name': instance.model_name,
            'provider': instance.provider,
            'cost_usd': instance.cost_usd,
            'timestamp': instance.timestamp,
            'message_id': instance.message_id,
        }


        # Evaluación lazy de relaciones costosas
        if 'message' in included and not 'message' == excluded and hasattr(instance, 'message') and getattr(instance, 'message') is not None:
            dto_data['message'] = MensajeRead.from_created_instance(
                instance.message, included, 'token_usage'
            )

        return cls(**dto_data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TokenUsageRead:
        """
        Crea un DTO desde un diccionario
        
        Args:
            data: Diccionario con los datos del DTO
            
        Returns:
            TokenUsageRead: Instancia del DTO
        """
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class TokenUsageCreate(BaseModel):
    """Data Transfer Object de escritura para TokenUsage. Define objetos para ser creados en la base de datos."""
    model_name: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    message_id: Optional[int] = None

    message: Optional[MensajeCreate] = None

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    def to_instance(self) -> TokenUsage:
        """
        Crea una instancia del modelo SQLAlchemy desde el DTO
        
        Returns:
            TokenUsage: Instancia del modelo SQLAlchemy
        """

        model = TokenUsage(
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            total_tokens=self.total_tokens,
            model_name=self.model_name,
            provider=self.provider,
            cost_usd=self.cost_usd,
            timestamp=self.timestamp,
            message_id=self.message_id,
        )
        
        # Evaluación lazy de relaciones costosas
        if self.message is not None:
            message = Mensaje(**self.message.to_dict())
            model.message = message

        return model
    
    @classmethod
    def from_instance(cls, instance: TokenUsage) -> TokenUsageCreate:
        """
        Crea un DTO desde una instancia del modelo SQLAlchemy
        
        Args:
            instance: Instancia del modelo TokenUsage
            
        Returns:
            TokenUsageCreate: Instancia del DTO
        """

        # Construir DTO base
        dto_data = {
            'id': instance.id,
            'prompt_tokens': instance.prompt_tokens,
            'completion_tokens': instance.completion_tokens,
            'total_tokens': instance.total_tokens,
            'model_name': instance.model_name,
            'provider': instance.provider,
            'cost_usd': instance.cost_usd,
            'timestamp': instance.timestamp,
            'message_id': instance.message_id,
        }


        # Evaluación lazy de relaciones costosas
        if hasattr(instance, 'message') and getattr(instance, 'message') is not None:
            dto_data['message'] = MensajeCreate.from_instance(
                instance.message
            )

        return cls(**dto_data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TokenUsageRead:
        """
        Crea un DTO desde un diccionario
        
        Args:
            data: Diccionario con los datos del DTO
            
        Returns:
            TokenUsageRead: Instancia del DTO
        """
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class TokenUsageFilter(BaseModel):
    """Data Transfer Object de actualización para TokenUsage.
    Define los filtros que sirven para buscar registros en la DB."""
    prompt_tokens: int = None
    completion_tokens: int = None
    total_tokens: int = None
    model_name: str = None
    provider: str = None
    cost_usd: float = None
    timestamp: datetime = None
    message_id: int = None

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_unset=True)


class TokenUsageUpdateValues(BaseModel):
    """Data Transfer Object de actualización para TokenUsage.
    Define los valores que se modificarán en los registros correspondientes."""
    prompt_tokens: int = None
    completion_tokens: int = None
    total_tokens: int = None
    model_name: str = None
    provider: str = None
    cost_usd: Optional[float] = None
    timestamp: datetime = None
    message_id: int = None

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_unset=True)


class TokenUsageUpdate(BaseModel):
    """Data Transfer Object de actualización para TokenUsage."""
    filter: TokenUsageFilter
    values: TokenUsageUpdateValues

    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )


class UserStatsRead(BaseModel):
    """
    Data Transfer Object de lectura para UserStats.
    
    Vista que muestra estadísticas de usuarios y sus chats
    
    Este modelo se utiliza como respuesta en endpoints de la API que devuelven
    información de user_stats existentes en la base de datos.
    
    Campos de la tabla:
        - username (str): Campo username de la tabla user_stats
        - email (str): Campo email de la tabla user_stats
        - total_chats (int): Campo total_chats de la tabla user_stats
        - active_chats (int): Campo active_chats de la tabla user_stats
        - total_messages (int): Campo total_messages de la tabla user_stats
        - created_at (datetime): Campo created_at de la tabla user_stats
        - last_activity (datetime, opcional): Campo last_activity de la tabla user_stats
    
    
    Rendimiento:
        - Sin includes: Consulta rápida, solo tabla UserStats
        - Máxima profundidad de anidación: 5 niveles
    """

    username: str = Field(
        description="Campo username de la tabla user_stats",
    )

    email: str = Field(
        description="Campo email de la tabla user_stats",
    )

    total_chats: int = Field(
        description="Campo total_chats de la tabla user_stats",
    )

    active_chats: int = Field(
        description="Campo active_chats de la tabla user_stats",
    )

    total_messages: int = Field(
        description="Campo total_messages de la tabla user_stats",
    )

    created_at: datetime = Field(
        description="Campo created_at de la tabla user_stats",
    )

    last_activity: Optional[datetime] = Field(
        description="Campo last_activity de la tabla user_stats",
    )


    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    @classmethod
    def from_instance(
        cls,
        instance: UserStats,
        includes: Optional[List[str]] = None,
        max_depth: int = 5
    ) -> UserStatsRead:
        """
        Crea un DTO desde una instancia del modelo SQLAlchemy con carga optimizada de relaciones.
        
        Args:
            instance: Instancia del modelo UserStats
            includes: Lista de relaciones a incluir (formato: 'relation' o 'relation.nested_relation')
            max_depth: Profundidad máxima de anidación para evitar recursión infinita
            
        Returns:
            UserStatsRead: Instancia del DTO
        """

        # Construir DTO base
        dto_data = {
            'username': instance.username,
            'email': instance.email,
            'total_chats': instance.total_chats,
            'active_chats': instance.active_chats,
            'total_messages': instance.total_messages,
            'created_at': instance.created_at,
            'last_activity': instance.last_activity,
        }

        return cls(**dto_data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UserStatsRead:
        """
        Crea un DTO desde un diccionario
        
        Args:
            data: Diccionario con los datos del DTO
            
        Returns:
            UserStatsRead: Instancia del DTO
        """
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class TokenConsumptionStatsRead(BaseModel):
    """
    Data Transfer Object de lectura para TokenConsumptionStats.
    
    Vista que muestra estadísticas de consumo de tokens por usuario y período
    
    Este modelo se utiliza como respuesta en endpoints de la API que devuelven
    información de token_consumption_stats existentes en la base de datos.
    
    Campos de la tabla:
        - username (str): Campo username de la tabla token_consumption_stats
        - date (datetime): Campo date de la tabla token_consumption_stats
        - total_prompt_tokens (int): Campo total_prompt_tokens de la tabla token_consumption_stats
        - total_completion_tokens (int): Campo total_completion_tokens de la tabla token_consumption_stats
        - total_tokens (int): Campo total_tokens de la tabla token_consumption_stats
        - total_cost_usd (float, opcional): Campo total_cost_usd de la tabla token_consumption_stats
        - chat_count (int): Campo chat_count de la tabla token_consumption_stats
        - most_used_model (str): Campo most_used_model de la tabla token_consumption_stats
        - most_used_provider (str): Campo most_used_provider de la tabla token_consumption_stats
    
    
    Rendimiento:
        - Sin includes: Consulta rápida, solo tabla TokenConsumptionStats
        - Máxima profundidad de anidación: 5 niveles
    """

    username: str = Field(
        description="Campo username de la tabla token_consumption_stats",
    )

    date: datetime = Field(
        description="Campo date de la tabla token_consumption_stats",
    )

    total_prompt_tokens: int = Field(
        description="Campo total_prompt_tokens de la tabla token_consumption_stats",
    )

    total_completion_tokens: int = Field(
        description="Campo total_completion_tokens de la tabla token_consumption_stats",
    )

    total_tokens: int = Field(
        description="Campo total_tokens de la tabla token_consumption_stats",
    )

    total_cost_usd: Optional[float] = Field(
        description="Campo total_cost_usd de la tabla token_consumption_stats",
    )

    chat_count: int = Field(
        description="Campo chat_count de la tabla token_consumption_stats",
    )

    most_used_model: str = Field(
        description="Campo most_used_model de la tabla token_consumption_stats",
    )

    most_used_provider: str = Field(
        description="Campo most_used_provider de la tabla token_consumption_stats",
    )


    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    @classmethod
    def from_instance(
        cls,
        instance: TokenConsumptionStats,
        includes: Optional[List[str]] = None,
        max_depth: int = 5
    ) -> TokenConsumptionStatsRead:
        """
        Crea un DTO desde una instancia del modelo SQLAlchemy con carga optimizada de relaciones.
        
        Args:
            instance: Instancia del modelo TokenConsumptionStats
            includes: Lista de relaciones a incluir (formato: 'relation' o 'relation.nested_relation')
            max_depth: Profundidad máxima de anidación para evitar recursión infinita
            
        Returns:
            TokenConsumptionStatsRead: Instancia del DTO
        """

        # Construir DTO base
        dto_data = {
            'username': instance.username,
            'date': instance.date,
            'total_prompt_tokens': instance.total_prompt_tokens,
            'total_completion_tokens': instance.total_completion_tokens,
            'total_tokens': instance.total_tokens,
            'total_cost_usd': instance.total_cost_usd,
            'chat_count': instance.chat_count,
            'most_used_model': instance.most_used_model,
            'most_used_provider': instance.most_used_provider,
        }

        return cls(**dto_data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TokenConsumptionStatsRead:
        """
        Crea un DTO desde un diccionario
        
        Args:
            data: Diccionario con los datos del DTO
            
        Returns:
            TokenConsumptionStatsRead: Instancia del DTO
        """
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class ChatActivityRead(BaseModel):
    """
    Data Transfer Object de lectura para ChatActivity.
    
    Vista que muestra la actividad reciente de chats
    
    Este modelo se utiliza como respuesta en endpoints de la API que devuelven
    información de chat_activity existentes en la base de datos.
    
    Campos de la tabla:
        - chat_id (str): Campo chat_id de la tabla chat_activity
        - chat_title (str): Campo chat_title de la tabla chat_activity
        - username (str): Campo username de la tabla chat_activity
        - message_count (int): Campo message_count de la tabla chat_activity
        - last_message_timestamp (datetime): Campo last_message_timestamp de la tabla chat_activity
        - total_tokens_consumed (int): Campo total_tokens_consumed de la tabla chat_activity
        - is_active (bool): Campo is_active de la tabla chat_activity
    
    
    Rendimiento:
        - Sin includes: Consulta rápida, solo tabla ChatActivity
        - Máxima profundidad de anidación: 5 niveles
    """

    chat_id: str = Field(
        description="Campo chat_id de la tabla chat_activity",
    )

    chat_title: str = Field(
        description="Campo chat_title de la tabla chat_activity",
    )

    username: str = Field(
        description="Campo username de la tabla chat_activity",
    )

    message_count: int = Field(
        description="Campo message_count de la tabla chat_activity",
    )

    last_message_timestamp: datetime = Field(
        description="Campo last_message_timestamp de la tabla chat_activity",
    )

    total_tokens_consumed: int = Field(
        description="Campo total_tokens_consumed de la tabla chat_activity",
    )

    is_active: bool = Field(
        description="Campo is_active de la tabla chat_activity",
    )


    model_config = ConfigDict(
        # Performance optimizations
        arbitrary_types_allowed=False,  # Más rápido al validar tipos estrictos
        use_enum_values=True,
        validate_assignment=True,  # Valida en cada asignación
        frozen=False,  # Si True, hace el objeto inmutable
        str_strip_whitespace=False,  # No procesa strings automáticamente
        validate_default=False,  # No valida valores por defecto
        extra="forbid",  # Más rápido que "allow" o "ignore"
        # Configuraciones adicionales de v2
        populate_by_name=True,  # Permite usar alias y nombres originales
        use_attribute_docstrings=True,  # Usa docstrings como descripciones
        validate_call=True,  # Valida llamadas a métodos
    )
    
    @classmethod
    def from_instance(
        cls,
        instance: ChatActivity,
        includes: Optional[List[str]] = None,
        max_depth: int = 5
    ) -> ChatActivityRead:
        """
        Crea un DTO desde una instancia del modelo SQLAlchemy con carga optimizada de relaciones.
        
        Args:
            instance: Instancia del modelo ChatActivity
            includes: Lista de relaciones a incluir (formato: 'relation' o 'relation.nested_relation')
            max_depth: Profundidad máxima de anidación para evitar recursión infinita
            
        Returns:
            ChatActivityRead: Instancia del DTO
        """

        # Construir DTO base
        dto_data = {
            'chat_id': instance.chat_id,
            'chat_title': instance.chat_title,
            'username': instance.username,
            'message_count': instance.message_count,
            'last_message_timestamp': instance.last_message_timestamp,
            'total_tokens_consumed': instance.total_tokens_consumed,
            'is_active': instance.is_active,
        }

        return cls(**dto_data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChatActivityRead:
        """
        Crea un DTO desde un diccionario
        
        Args:
            data: Diccionario con los datos del DTO
            
        Returns:
            ChatActivityRead: Instancia del DTO
        """
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


