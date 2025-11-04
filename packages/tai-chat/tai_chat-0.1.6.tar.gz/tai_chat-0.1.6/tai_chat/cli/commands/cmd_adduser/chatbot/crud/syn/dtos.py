# Este archivo ha sido generado automáticamente por tai-sql
# No modifiques este archivo directamente
from __future__ import annotations
from typing import (
    List,
    Optional,
    Dict,
    Literal,
    Any,
    TYPE_CHECKING
)
from ...models import *
from pydantic import (
    BaseModel,
    Field,
    ConfigDict
)

from tai_alphi import Alphi

from .utils import (
    should_include_relation,
    get_nested_includes,
)

if TYPE_CHECKING:
    from pandas import DataFrame, Series  # type: ignore[import-untyped]
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
            chats = [reg.to_instance() for reg in self.chats]
            model.chats = chats

        return model
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UsuarioCreate:
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

class UsuarioDataFrameValidator:
    """ Validador de DataFrame para el modelo Usuario """

    def validate_dataframe_schema(
        self, 
        df: DataFrame, 
        ignore_extra_columns: bool, 
        fill_missing_nullable: bool
    ) -> None:
        """
        Valida que el esquema del DataFrame sea compatible con el modelo.
        
        Args:
            df: DataFrame a validar
            ignore_extra_columns: Si ignorar columnas extra
            fill_missing_nullable: Si llenar columnas nullable faltantes
            
        Raises:
            ValueError: Si el esquema no es compatible
        """
        # Definir columnas del modelo
        model_columns = {
            'username': {
                'type': 'str',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'password': {
                'type': 'str',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'email': {
                'type': 'str',
                'nullable': True,
                'primary_key': False,
                'autoincrement': False
            },
            'avatar': {
                'type': 'str',
                'nullable': True,
                'primary_key': False,
                'autoincrement': False
            },
            'session_id': {
                'type': 'str',
                'nullable': True,
                'primary_key': False,
                'autoincrement': False
            },
            'created_at': {
                'type': 'datetime',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'updated_at': {
                'type': 'datetime',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'is_active': {
                'type': 'bool',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            }
        }
        
        df_columns = set(df.columns)
        required_columns = set(model_columns.keys())
        
        # Verificar columnas extra
        extra_columns = df_columns - required_columns
        if extra_columns and not ignore_extra_columns:
            raise ValueError(
                f"DataFrame contiene columnas no definidas en el modelo: {list(extra_columns)}\n"
                f"Usa ignore_extra_columns=True para ignorarlas o elimínalas del DataFrame"
            )
        
        # Verificar columnas faltantes
        missing_columns = required_columns - df_columns
        
        # Filtrar columnas que pueden faltar
        critical_missing = []
        for col in missing_columns:
            col_info = model_columns[col]
            # Las columnas críticas son las que no son nullable, no son auto-increment y no son PK auto
            if (not col_info['nullable'] and 
                not col_info['autoincrement'] and 
                not (col_info['primary_key'] and col_info['autoincrement'])):
                critical_missing.append(col)
        
        if critical_missing:
            raise ValueError(
                f"DataFrame falta columnas requeridas (NOT NULL): {critical_missing}\n"
                f"Estas columnas son obligatorias y deben estar presentes en el DataFrame"
            )
        
        # Advertir sobre columnas nullable faltantes
        nullable_missing = [col for col in missing_columns if col not in critical_missing]
        if nullable_missing and not fill_missing_nullable:
            import warnings
            warnings.warn(
                f"DataFrame falta columnas nullable: {nullable_missing}\n"
                f"Usa fill_missing_nullable=True para llenarlas automáticamente con None"
            )
    
    def validate_dataframe_types(self, df: "DataFrame") -> None:
        """
        Valida que los tipos de datos del DataFrame sean compatibles.
        
        Args:
            df: DataFrame a validar
            
        Raises:
            TypeError: Si los tipos no son compatibles
        """
        
        # Mapeo de tipos SQLAlchemy a tipos pandas compatibles
        type_compatibility = {
            'username': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'password': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'email': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'avatar': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'session_id': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'created_at': {
                'sqlalchemy_type': 'datetime',
                'compatible_pandas_types': [
                    'datetime64[ns]', 'object'
                ]
            },
            'updated_at': {
                'sqlalchemy_type': 'datetime',
                'compatible_pandas_types': [
                    'datetime64[ns]', 'object'
                ]
            },
            'is_active': {
                'sqlalchemy_type': 'bool',
                'compatible_pandas_types': [
                    'bool', 'boolean', 'object'
                ]
            }
        }
        
        type_errors = []
        
        for column in df.columns:
            if column in type_compatibility:
                df_dtype = str(df[column].dtype)
                compatible_types = type_compatibility[column]['compatible_pandas_types']
                sqlalchemy_type = type_compatibility[column]['sqlalchemy_type']
                
                if df_dtype not in compatible_types:
                    # Verificar si puede ser convertido
                    if self.can_convert_type(df[column], sqlalchemy_type):
                        continue
                    
                    type_errors.append(
                        f"Columna '{column}': tipo '{df_dtype}' no compatible con '{sqlalchemy_type}'. "
                        f"Tipos aceptados: {compatible_types}"
                    )
        
        if type_errors:
            raise TypeError(
                "Errores de tipo de datos encontrados:\n" + 
                "\n".join(f"  - {error}" for error in type_errors) +
                "\n\nConsidera convertir los tipos antes de la inserción."
            )
    
    def can_convert_type(self, series: "Series", target_sqlalchemy_type: str) -> bool:
        """
        Verifica si una serie puede ser convertida al tipo SQLAlchemy objetivo.
        
        Args:
            series: Serie de pandas a verificar
            target_sqlalchemy_type: Tipo SQLAlchemy objetivo
            
        Returns:
            bool: True si puede ser convertida
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas no está instalado. Para usar from_df(), instala pandas:\n"
                "pip install pandas\n"
                "o si usas poetry:\n"
                "poetry add pandas"
            )
        
        try:
            # Probar conversión en una muestra pequeña
            sample = series.dropna().head(10)
            if sample.empty:
                return True
            
            if 'int' in target_sqlalchemy_type:
                pd.to_numeric(sample, errors='raise')
            elif 'float' in target_sqlalchemy_type or 'Numeric' in target_sqlalchemy_type:
                pd.to_numeric(sample, errors='raise')
            elif 'bool' in target_sqlalchemy_type:
                # Verificar valores booleanos válidos
                valid_bool_values = {True, False, 1, 0, '1', '0', 'true', 'false', 'True', 'False'}
                if not all(val in valid_bool_values for val in sample.unique()):
                    return False
            elif 'datetime' in target_sqlalchemy_type or 'date' in target_sqlalchemy_type:
                pd.to_datetime(sample, errors='raise')
            
            return True
        except:
            return False
    
    def prepare_dataframe_for_insertion(
        self, 
        df: "DataFrame", 
        ignore_extra_columns: bool, 
        fill_missing_nullable: bool
    ) -> "DataFrame":
        """
        Prepara el DataFrame para inserción en la base de datos.
        
        Args:
            df: DataFrame original
            ignore_extra_columns: Si ignorar columnas extra
            fill_missing_nullable: Si llenar columnas faltantes nullable
            
        Returns:
            DataFrame preparado para inserción
        """
        try:
            import pandas as pd
            import numpy as np
        except ImportError:
            return df
        
        # Crear copia para no modificar el original
        cleaned_df = df.copy()
        
        # Definir columnas del modelo
        model_columns = {
            'username': {
                'nullable': False,
                'autoincrement': False
            },
            'password': {
                'nullable': False,
                'autoincrement': False
            },
            'email': {
                'nullable': True,
                'autoincrement': False
            },
            'avatar': {
                'nullable': True,
                'autoincrement': False
            },
            'session_id': {
                'nullable': True,
                'autoincrement': False
            },
            'created_at': {
                'nullable': False,
                'autoincrement': False
            },
            'updated_at': {
                'nullable': False,
                'autoincrement': False
            },
            'is_active': {
                'nullable': False,
                'autoincrement': False
            }
        }
        
        # Eliminar columnas extra si se solicita
        if ignore_extra_columns:
            extra_columns = set(cleaned_df.columns) - set(model_columns.keys())
            if extra_columns:
                cleaned_df = cleaned_df.drop(columns=list(extra_columns))
        
        # Agregar columnas nullable faltantes si se solicita
        if fill_missing_nullable:
            for col_name, col_info in model_columns.items():
                if (col_name not in cleaned_df.columns and 
                    col_info['nullable'] and 
                    not col_info['autoincrement']):
                    cleaned_df[col_name] = None
        
        # Eliminar columnas autoincrement (la BD las manejará)
        autoincrement_columns = [
            col for col, info in model_columns.items() 
            if info['autoincrement'] and col in cleaned_df.columns
        ]
        if autoincrement_columns:
            cleaned_df = cleaned_df.drop(columns=autoincrement_columns)
        
        # Reordenar columnas según el modelo (las que existan)
        model_column_order = [col for col in model_columns.keys() if col in cleaned_df.columns]
        cleaned_df = cleaned_df[model_column_order]
        
        return cleaned_df
    
    def clean_records_data(self, records_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Limpia los datos de registros para inserción en BD.
        
        Args:
            records_data: Lista de diccionarios con datos de registros
            
        Returns:
            Lista de diccionarios limpiados
        """
        try:
            import pandas as pd
        except ImportError:
            return records_data
        
        cleaned_records = []
        
        for record in records_data:
            cleaned_record = {}
            for key, value in record.items():
                # Manejar valores NaN y NaT de pandas
                if pd.isna(value):
                    cleaned_record[key] = None
                # Manejar tipos numpy
                elif hasattr(value, 'item'):  # numpy scalars
                    cleaned_record[key] = value.item()
                else:
                    cleaned_record[key] = value
            
            cleaned_records.append(cleaned_record)
        
        return cleaned_records

        
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
            messages = [reg.to_instance() for reg in self.messages]
            model.messages = messages
        if self.usuario is not None:
            usuario = self.usuario.to_instance()
            model.usuario = usuario

        return model
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChatCreate:
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

class ChatDataFrameValidator:
    """ Validador de DataFrame para el modelo Chat """

    def validate_dataframe_schema(
        self, 
        df: DataFrame, 
        ignore_extra_columns: bool, 
        fill_missing_nullable: bool
    ) -> None:
        """
        Valida que el esquema del DataFrame sea compatible con el modelo.
        
        Args:
            df: DataFrame a validar
            ignore_extra_columns: Si ignorar columnas extra
            fill_missing_nullable: Si llenar columnas nullable faltantes
            
        Raises:
            ValueError: Si el esquema no es compatible
        """
        # Definir columnas del modelo
        model_columns = {
            'id': {
                'type': 'int',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'title': {
                'type': 'str',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'username': {
                'type': 'str',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'created_at': {
                'type': 'datetime',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'updated_at': {
                'type': 'datetime',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'is_active': {
                'type': 'bool',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            }
        }
        
        df_columns = set(df.columns)
        required_columns = set(model_columns.keys())
        
        # Verificar columnas extra
        extra_columns = df_columns - required_columns
        if extra_columns and not ignore_extra_columns:
            raise ValueError(
                f"DataFrame contiene columnas no definidas en el modelo: {list(extra_columns)}\n"
                f"Usa ignore_extra_columns=True para ignorarlas o elimínalas del DataFrame"
            )
        
        # Verificar columnas faltantes
        missing_columns = required_columns - df_columns
        
        # Filtrar columnas que pueden faltar
        critical_missing = []
        for col in missing_columns:
            col_info = model_columns[col]
            # Las columnas críticas son las que no son nullable, no son auto-increment y no son PK auto
            if (not col_info['nullable'] and 
                not col_info['autoincrement'] and 
                not (col_info['primary_key'] and col_info['autoincrement'])):
                critical_missing.append(col)
        
        if critical_missing:
            raise ValueError(
                f"DataFrame falta columnas requeridas (NOT NULL): {critical_missing}\n"
                f"Estas columnas son obligatorias y deben estar presentes en el DataFrame"
            )
        
        # Advertir sobre columnas nullable faltantes
        nullable_missing = [col for col in missing_columns if col not in critical_missing]
        if nullable_missing and not fill_missing_nullable:
            import warnings
            warnings.warn(
                f"DataFrame falta columnas nullable: {nullable_missing}\n"
                f"Usa fill_missing_nullable=True para llenarlas automáticamente con None"
            )
    
    def validate_dataframe_types(self, df: "DataFrame") -> None:
        """
        Valida que los tipos de datos del DataFrame sean compatibles.
        
        Args:
            df: DataFrame a validar
            
        Raises:
            TypeError: Si los tipos no son compatibles
        """
        
        # Mapeo de tipos SQLAlchemy a tipos pandas compatibles
        type_compatibility = {
            'id': {
                'sqlalchemy_type': 'int',
                'compatible_pandas_types': [
                    'int64', 'Int64', 'int32', 'Int32', 'int16', 'Int16', 'int8', 'Int8', 'object'
                ]
            },
            'title': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'username': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'created_at': {
                'sqlalchemy_type': 'datetime',
                'compatible_pandas_types': [
                    'datetime64[ns]', 'object'
                ]
            },
            'updated_at': {
                'sqlalchemy_type': 'datetime',
                'compatible_pandas_types': [
                    'datetime64[ns]', 'object'
                ]
            },
            'is_active': {
                'sqlalchemy_type': 'bool',
                'compatible_pandas_types': [
                    'bool', 'boolean', 'object'
                ]
            }
        }
        
        type_errors = []
        
        for column in df.columns:
            if column in type_compatibility:
                df_dtype = str(df[column].dtype)
                compatible_types = type_compatibility[column]['compatible_pandas_types']
                sqlalchemy_type = type_compatibility[column]['sqlalchemy_type']
                
                if df_dtype not in compatible_types:
                    # Verificar si puede ser convertido
                    if self.can_convert_type(df[column], sqlalchemy_type):
                        continue
                    
                    type_errors.append(
                        f"Columna '{column}': tipo '{df_dtype}' no compatible con '{sqlalchemy_type}'. "
                        f"Tipos aceptados: {compatible_types}"
                    )
        
        if type_errors:
            raise TypeError(
                "Errores de tipo de datos encontrados:\n" + 
                "\n".join(f"  - {error}" for error in type_errors) +
                "\n\nConsidera convertir los tipos antes de la inserción."
            )
    
    def can_convert_type(self, series: "Series", target_sqlalchemy_type: str) -> bool:
        """
        Verifica si una serie puede ser convertida al tipo SQLAlchemy objetivo.
        
        Args:
            series: Serie de pandas a verificar
            target_sqlalchemy_type: Tipo SQLAlchemy objetivo
            
        Returns:
            bool: True si puede ser convertida
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas no está instalado. Para usar from_df(), instala pandas:\n"
                "pip install pandas\n"
                "o si usas poetry:\n"
                "poetry add pandas"
            )
        
        try:
            # Probar conversión en una muestra pequeña
            sample = series.dropna().head(10)
            if sample.empty:
                return True
            
            if 'int' in target_sqlalchemy_type:
                pd.to_numeric(sample, errors='raise')
            elif 'float' in target_sqlalchemy_type or 'Numeric' in target_sqlalchemy_type:
                pd.to_numeric(sample, errors='raise')
            elif 'bool' in target_sqlalchemy_type:
                # Verificar valores booleanos válidos
                valid_bool_values = {True, False, 1, 0, '1', '0', 'true', 'false', 'True', 'False'}
                if not all(val in valid_bool_values for val in sample.unique()):
                    return False
            elif 'datetime' in target_sqlalchemy_type or 'date' in target_sqlalchemy_type:
                pd.to_datetime(sample, errors='raise')
            
            return True
        except:
            return False
    
    def prepare_dataframe_for_insertion(
        self, 
        df: "DataFrame", 
        ignore_extra_columns: bool, 
        fill_missing_nullable: bool
    ) -> "DataFrame":
        """
        Prepara el DataFrame para inserción en la base de datos.
        
        Args:
            df: DataFrame original
            ignore_extra_columns: Si ignorar columnas extra
            fill_missing_nullable: Si llenar columnas faltantes nullable
            
        Returns:
            DataFrame preparado para inserción
        """
        try:
            import pandas as pd
            import numpy as np
        except ImportError:
            return df
        
        # Crear copia para no modificar el original
        cleaned_df = df.copy()
        
        # Definir columnas del modelo
        model_columns = {
            'id': {
                'nullable': False,
                'autoincrement': False
            },
            'title': {
                'nullable': False,
                'autoincrement': False
            },
            'username': {
                'nullable': False,
                'autoincrement': False
            },
            'created_at': {
                'nullable': False,
                'autoincrement': False
            },
            'updated_at': {
                'nullable': False,
                'autoincrement': False
            },
            'is_active': {
                'nullable': False,
                'autoincrement': False
            }
        }
        
        # Eliminar columnas extra si se solicita
        if ignore_extra_columns:
            extra_columns = set(cleaned_df.columns) - set(model_columns.keys())
            if extra_columns:
                cleaned_df = cleaned_df.drop(columns=list(extra_columns))
        
        # Agregar columnas nullable faltantes si se solicita
        if fill_missing_nullable:
            for col_name, col_info in model_columns.items():
                if (col_name not in cleaned_df.columns and 
                    col_info['nullable'] and 
                    not col_info['autoincrement']):
                    cleaned_df[col_name] = None
        
        # Eliminar columnas autoincrement (la BD las manejará)
        autoincrement_columns = [
            col for col, info in model_columns.items() 
            if info['autoincrement'] and col in cleaned_df.columns
        ]
        if autoincrement_columns:
            cleaned_df = cleaned_df.drop(columns=autoincrement_columns)
        
        # Reordenar columnas según el modelo (las que existan)
        model_column_order = [col for col in model_columns.keys() if col in cleaned_df.columns]
        cleaned_df = cleaned_df[model_column_order]
        
        return cleaned_df
    
    def clean_records_data(self, records_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Limpia los datos de registros para inserción en BD.
        
        Args:
            records_data: Lista de diccionarios con datos de registros
            
        Returns:
            Lista de diccionarios limpiados
        """
        try:
            import pandas as pd
        except ImportError:
            return records_data
        
        cleaned_records = []
        
        for record in records_data:
            cleaned_record = {}
            for key, value in record.items():
                # Manejar valores NaN y NaT de pandas
                if pd.isna(value):
                    cleaned_record[key] = None
                # Manejar tipos numpy
                elif hasattr(value, 'item'):  # numpy scalars
                    cleaned_record[key] = value.item()
                else:
                    cleaned_record[key] = value
            
            cleaned_records.append(cleaned_record)
        
        return cleaned_records

        
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
            token_usage = [reg.to_instance() for reg in self.token_usage]
            model.token_usage = token_usage
        if self.chat is not None:
            chat = self.chat.to_instance()
            model.chat = chat

        return model
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MensajeCreate:
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

class MensajeDataFrameValidator:
    """ Validador de DataFrame para el modelo Mensaje """

    def validate_dataframe_schema(
        self, 
        df: DataFrame, 
        ignore_extra_columns: bool, 
        fill_missing_nullable: bool
    ) -> None:
        """
        Valida que el esquema del DataFrame sea compatible con el modelo.
        
        Args:
            df: DataFrame a validar
            ignore_extra_columns: Si ignorar columnas extra
            fill_missing_nullable: Si llenar columnas nullable faltantes
            
        Raises:
            ValueError: Si el esquema no es compatible
        """
        # Definir columnas del modelo
        model_columns = {
            'id': {
                'type': 'int',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'content': {
                'type': 'str',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'role': {
                'type': 'str',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'timestamp': {
                'type': 'datetime',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'chat_id': {
                'type': 'int',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            }
        }
        
        df_columns = set(df.columns)
        required_columns = set(model_columns.keys())
        
        # Verificar columnas extra
        extra_columns = df_columns - required_columns
        if extra_columns and not ignore_extra_columns:
            raise ValueError(
                f"DataFrame contiene columnas no definidas en el modelo: {list(extra_columns)}\n"
                f"Usa ignore_extra_columns=True para ignorarlas o elimínalas del DataFrame"
            )
        
        # Verificar columnas faltantes
        missing_columns = required_columns - df_columns
        
        # Filtrar columnas que pueden faltar
        critical_missing = []
        for col in missing_columns:
            col_info = model_columns[col]
            # Las columnas críticas son las que no son nullable, no son auto-increment y no son PK auto
            if (not col_info['nullable'] and 
                not col_info['autoincrement'] and 
                not (col_info['primary_key'] and col_info['autoincrement'])):
                critical_missing.append(col)
        
        if critical_missing:
            raise ValueError(
                f"DataFrame falta columnas requeridas (NOT NULL): {critical_missing}\n"
                f"Estas columnas son obligatorias y deben estar presentes en el DataFrame"
            )
        
        # Advertir sobre columnas nullable faltantes
        nullable_missing = [col for col in missing_columns if col not in critical_missing]
        if nullable_missing and not fill_missing_nullable:
            import warnings
            warnings.warn(
                f"DataFrame falta columnas nullable: {nullable_missing}\n"
                f"Usa fill_missing_nullable=True para llenarlas automáticamente con None"
            )
    
    def validate_dataframe_types(self, df: "DataFrame") -> None:
        """
        Valida que los tipos de datos del DataFrame sean compatibles.
        
        Args:
            df: DataFrame a validar
            
        Raises:
            TypeError: Si los tipos no son compatibles
        """
        
        # Mapeo de tipos SQLAlchemy a tipos pandas compatibles
        type_compatibility = {
            'id': {
                'sqlalchemy_type': 'int',
                'compatible_pandas_types': [
                    'int64', 'Int64', 'int32', 'Int32', 'int16', 'Int16', 'int8', 'Int8', 'object'
                ]
            },
            'content': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'role': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'timestamp': {
                'sqlalchemy_type': 'datetime',
                'compatible_pandas_types': [
                    'datetime64[ns]', 'object'
                ]
            },
            'chat_id': {
                'sqlalchemy_type': 'int',
                'compatible_pandas_types': [
                    'int64', 'Int64', 'int32', 'Int32', 'int16', 'Int16', 'int8', 'Int8', 'object'
                ]
            }
        }
        
        type_errors = []
        
        for column in df.columns:
            if column in type_compatibility:
                df_dtype = str(df[column].dtype)
                compatible_types = type_compatibility[column]['compatible_pandas_types']
                sqlalchemy_type = type_compatibility[column]['sqlalchemy_type']
                
                if df_dtype not in compatible_types:
                    # Verificar si puede ser convertido
                    if self.can_convert_type(df[column], sqlalchemy_type):
                        continue
                    
                    type_errors.append(
                        f"Columna '{column}': tipo '{df_dtype}' no compatible con '{sqlalchemy_type}'. "
                        f"Tipos aceptados: {compatible_types}"
                    )
        
        if type_errors:
            raise TypeError(
                "Errores de tipo de datos encontrados:\n" + 
                "\n".join(f"  - {error}" for error in type_errors) +
                "\n\nConsidera convertir los tipos antes de la inserción."
            )
    
    def can_convert_type(self, series: "Series", target_sqlalchemy_type: str) -> bool:
        """
        Verifica si una serie puede ser convertida al tipo SQLAlchemy objetivo.
        
        Args:
            series: Serie de pandas a verificar
            target_sqlalchemy_type: Tipo SQLAlchemy objetivo
            
        Returns:
            bool: True si puede ser convertida
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas no está instalado. Para usar from_df(), instala pandas:\n"
                "pip install pandas\n"
                "o si usas poetry:\n"
                "poetry add pandas"
            )
        
        try:
            # Probar conversión en una muestra pequeña
            sample = series.dropna().head(10)
            if sample.empty:
                return True
            
            if 'int' in target_sqlalchemy_type:
                pd.to_numeric(sample, errors='raise')
            elif 'float' in target_sqlalchemy_type or 'Numeric' in target_sqlalchemy_type:
                pd.to_numeric(sample, errors='raise')
            elif 'bool' in target_sqlalchemy_type:
                # Verificar valores booleanos válidos
                valid_bool_values = {True, False, 1, 0, '1', '0', 'true', 'false', 'True', 'False'}
                if not all(val in valid_bool_values for val in sample.unique()):
                    return False
            elif 'datetime' in target_sqlalchemy_type or 'date' in target_sqlalchemy_type:
                pd.to_datetime(sample, errors='raise')
            
            return True
        except:
            return False
    
    def prepare_dataframe_for_insertion(
        self, 
        df: "DataFrame", 
        ignore_extra_columns: bool, 
        fill_missing_nullable: bool
    ) -> "DataFrame":
        """
        Prepara el DataFrame para inserción en la base de datos.
        
        Args:
            df: DataFrame original
            ignore_extra_columns: Si ignorar columnas extra
            fill_missing_nullable: Si llenar columnas faltantes nullable
            
        Returns:
            DataFrame preparado para inserción
        """
        try:
            import pandas as pd
            import numpy as np
        except ImportError:
            return df
        
        # Crear copia para no modificar el original
        cleaned_df = df.copy()
        
        # Definir columnas del modelo
        model_columns = {
            'id': {
                'nullable': False,
                'autoincrement': False
            },
            'content': {
                'nullable': False,
                'autoincrement': False
            },
            'role': {
                'nullable': False,
                'autoincrement': False
            },
            'timestamp': {
                'nullable': False,
                'autoincrement': False
            },
            'chat_id': {
                'nullable': False,
                'autoincrement': False
            }
        }
        
        # Eliminar columnas extra si se solicita
        if ignore_extra_columns:
            extra_columns = set(cleaned_df.columns) - set(model_columns.keys())
            if extra_columns:
                cleaned_df = cleaned_df.drop(columns=list(extra_columns))
        
        # Agregar columnas nullable faltantes si se solicita
        if fill_missing_nullable:
            for col_name, col_info in model_columns.items():
                if (col_name not in cleaned_df.columns and 
                    col_info['nullable'] and 
                    not col_info['autoincrement']):
                    cleaned_df[col_name] = None
        
        # Eliminar columnas autoincrement (la BD las manejará)
        autoincrement_columns = [
            col for col, info in model_columns.items() 
            if info['autoincrement'] and col in cleaned_df.columns
        ]
        if autoincrement_columns:
            cleaned_df = cleaned_df.drop(columns=autoincrement_columns)
        
        # Reordenar columnas según el modelo (las que existan)
        model_column_order = [col for col in model_columns.keys() if col in cleaned_df.columns]
        cleaned_df = cleaned_df[model_column_order]
        
        return cleaned_df
    
    def clean_records_data(self, records_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Limpia los datos de registros para inserción en BD.
        
        Args:
            records_data: Lista de diccionarios con datos de registros
            
        Returns:
            Lista de diccionarios limpiados
        """
        try:
            import pandas as pd
        except ImportError:
            return records_data
        
        cleaned_records = []
        
        for record in records_data:
            cleaned_record = {}
            for key, value in record.items():
                # Manejar valores NaN y NaT de pandas
                if pd.isna(value):
                    cleaned_record[key] = None
                # Manejar tipos numpy
                elif hasattr(value, 'item'):  # numpy scalars
                    cleaned_record[key] = value.item()
                else:
                    cleaned_record[key] = value
            
            cleaned_records.append(cleaned_record)
        
        return cleaned_records

        
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
            message = self.message.to_instance()
            model.message = message

        return model
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TokenUsageCreate:
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

class TokenUsageDataFrameValidator:
    """ Validador de DataFrame para el modelo TokenUsage """

    def validate_dataframe_schema(
        self, 
        df: DataFrame, 
        ignore_extra_columns: bool, 
        fill_missing_nullable: bool
    ) -> None:
        """
        Valida que el esquema del DataFrame sea compatible con el modelo.
        
        Args:
            df: DataFrame a validar
            ignore_extra_columns: Si ignorar columnas extra
            fill_missing_nullable: Si llenar columnas nullable faltantes
            
        Raises:
            ValueError: Si el esquema no es compatible
        """
        # Definir columnas del modelo
        model_columns = {
            'id': {
                'type': 'int',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'prompt_tokens': {
                'type': 'int',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'completion_tokens': {
                'type': 'int',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'total_tokens': {
                'type': 'int',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'model_name': {
                'type': 'str',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'provider': {
                'type': 'str',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'cost_usd': {
                'type': 'float',
                'nullable': True,
                'primary_key': False,
                'autoincrement': False
            },
            'timestamp': {
                'type': 'datetime',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'message_id': {
                'type': 'int',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            }
        }
        
        df_columns = set(df.columns)
        required_columns = set(model_columns.keys())
        
        # Verificar columnas extra
        extra_columns = df_columns - required_columns
        if extra_columns and not ignore_extra_columns:
            raise ValueError(
                f"DataFrame contiene columnas no definidas en el modelo: {list(extra_columns)}\n"
                f"Usa ignore_extra_columns=True para ignorarlas o elimínalas del DataFrame"
            )
        
        # Verificar columnas faltantes
        missing_columns = required_columns - df_columns
        
        # Filtrar columnas que pueden faltar
        critical_missing = []
        for col in missing_columns:
            col_info = model_columns[col]
            # Las columnas críticas son las que no son nullable, no son auto-increment y no son PK auto
            if (not col_info['nullable'] and 
                not col_info['autoincrement'] and 
                not (col_info['primary_key'] and col_info['autoincrement'])):
                critical_missing.append(col)
        
        if critical_missing:
            raise ValueError(
                f"DataFrame falta columnas requeridas (NOT NULL): {critical_missing}\n"
                f"Estas columnas son obligatorias y deben estar presentes en el DataFrame"
            )
        
        # Advertir sobre columnas nullable faltantes
        nullable_missing = [col for col in missing_columns if col not in critical_missing]
        if nullable_missing and not fill_missing_nullable:
            import warnings
            warnings.warn(
                f"DataFrame falta columnas nullable: {nullable_missing}\n"
                f"Usa fill_missing_nullable=True para llenarlas automáticamente con None"
            )
    
    def validate_dataframe_types(self, df: "DataFrame") -> None:
        """
        Valida que los tipos de datos del DataFrame sean compatibles.
        
        Args:
            df: DataFrame a validar
            
        Raises:
            TypeError: Si los tipos no son compatibles
        """
        
        # Mapeo de tipos SQLAlchemy a tipos pandas compatibles
        type_compatibility = {
            'id': {
                'sqlalchemy_type': 'int',
                'compatible_pandas_types': [
                    'int64', 'Int64', 'int32', 'Int32', 'int16', 'Int16', 'int8', 'Int8', 'object'
                ]
            },
            'prompt_tokens': {
                'sqlalchemy_type': 'int',
                'compatible_pandas_types': [
                    'int64', 'Int64', 'int32', 'Int32', 'int16', 'Int16', 'int8', 'Int8', 'object'
                ]
            },
            'completion_tokens': {
                'sqlalchemy_type': 'int',
                'compatible_pandas_types': [
                    'int64', 'Int64', 'int32', 'Int32', 'int16', 'Int16', 'int8', 'Int8', 'object'
                ]
            },
            'total_tokens': {
                'sqlalchemy_type': 'int',
                'compatible_pandas_types': [
                    'int64', 'Int64', 'int32', 'Int32', 'int16', 'Int16', 'int8', 'Int8', 'object'
                ]
            },
            'model_name': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'provider': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'cost_usd': {
                'sqlalchemy_type': 'float',
                'compatible_pandas_types': [
                    'float64', 'float32', 'int64', 'Int64', 'object'
                ]
            },
            'timestamp': {
                'sqlalchemy_type': 'datetime',
                'compatible_pandas_types': [
                    'datetime64[ns]', 'object'
                ]
            },
            'message_id': {
                'sqlalchemy_type': 'int',
                'compatible_pandas_types': [
                    'int64', 'Int64', 'int32', 'Int32', 'int16', 'Int16', 'int8', 'Int8', 'object'
                ]
            }
        }
        
        type_errors = []
        
        for column in df.columns:
            if column in type_compatibility:
                df_dtype = str(df[column].dtype)
                compatible_types = type_compatibility[column]['compatible_pandas_types']
                sqlalchemy_type = type_compatibility[column]['sqlalchemy_type']
                
                if df_dtype not in compatible_types:
                    # Verificar si puede ser convertido
                    if self.can_convert_type(df[column], sqlalchemy_type):
                        continue
                    
                    type_errors.append(
                        f"Columna '{column}': tipo '{df_dtype}' no compatible con '{sqlalchemy_type}'. "
                        f"Tipos aceptados: {compatible_types}"
                    )
        
        if type_errors:
            raise TypeError(
                "Errores de tipo de datos encontrados:\n" + 
                "\n".join(f"  - {error}" for error in type_errors) +
                "\n\nConsidera convertir los tipos antes de la inserción."
            )
    
    def can_convert_type(self, series: "Series", target_sqlalchemy_type: str) -> bool:
        """
        Verifica si una serie puede ser convertida al tipo SQLAlchemy objetivo.
        
        Args:
            series: Serie de pandas a verificar
            target_sqlalchemy_type: Tipo SQLAlchemy objetivo
            
        Returns:
            bool: True si puede ser convertida
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas no está instalado. Para usar from_df(), instala pandas:\n"
                "pip install pandas\n"
                "o si usas poetry:\n"
                "poetry add pandas"
            )
        
        try:
            # Probar conversión en una muestra pequeña
            sample = series.dropna().head(10)
            if sample.empty:
                return True
            
            if 'int' in target_sqlalchemy_type:
                pd.to_numeric(sample, errors='raise')
            elif 'float' in target_sqlalchemy_type or 'Numeric' in target_sqlalchemy_type:
                pd.to_numeric(sample, errors='raise')
            elif 'bool' in target_sqlalchemy_type:
                # Verificar valores booleanos válidos
                valid_bool_values = {True, False, 1, 0, '1', '0', 'true', 'false', 'True', 'False'}
                if not all(val in valid_bool_values for val in sample.unique()):
                    return False
            elif 'datetime' in target_sqlalchemy_type or 'date' in target_sqlalchemy_type:
                pd.to_datetime(sample, errors='raise')
            
            return True
        except:
            return False
    
    def prepare_dataframe_for_insertion(
        self, 
        df: "DataFrame", 
        ignore_extra_columns: bool, 
        fill_missing_nullable: bool
    ) -> "DataFrame":
        """
        Prepara el DataFrame para inserción en la base de datos.
        
        Args:
            df: DataFrame original
            ignore_extra_columns: Si ignorar columnas extra
            fill_missing_nullable: Si llenar columnas faltantes nullable
            
        Returns:
            DataFrame preparado para inserción
        """
        try:
            import pandas as pd
            import numpy as np
        except ImportError:
            return df
        
        # Crear copia para no modificar el original
        cleaned_df = df.copy()
        
        # Definir columnas del modelo
        model_columns = {
            'id': {
                'nullable': False,
                'autoincrement': False
            },
            'prompt_tokens': {
                'nullable': False,
                'autoincrement': False
            },
            'completion_tokens': {
                'nullable': False,
                'autoincrement': False
            },
            'total_tokens': {
                'nullable': False,
                'autoincrement': False
            },
            'model_name': {
                'nullable': False,
                'autoincrement': False
            },
            'provider': {
                'nullable': False,
                'autoincrement': False
            },
            'cost_usd': {
                'nullable': True,
                'autoincrement': False
            },
            'timestamp': {
                'nullable': False,
                'autoincrement': False
            },
            'message_id': {
                'nullable': False,
                'autoincrement': False
            }
        }
        
        # Eliminar columnas extra si se solicita
        if ignore_extra_columns:
            extra_columns = set(cleaned_df.columns) - set(model_columns.keys())
            if extra_columns:
                cleaned_df = cleaned_df.drop(columns=list(extra_columns))
        
        # Agregar columnas nullable faltantes si se solicita
        if fill_missing_nullable:
            for col_name, col_info in model_columns.items():
                if (col_name not in cleaned_df.columns and 
                    col_info['nullable'] and 
                    not col_info['autoincrement']):
                    cleaned_df[col_name] = None
        
        # Eliminar columnas autoincrement (la BD las manejará)
        autoincrement_columns = [
            col for col, info in model_columns.items() 
            if info['autoincrement'] and col in cleaned_df.columns
        ]
        if autoincrement_columns:
            cleaned_df = cleaned_df.drop(columns=autoincrement_columns)
        
        # Reordenar columnas según el modelo (las que existan)
        model_column_order = [col for col in model_columns.keys() if col in cleaned_df.columns]
        cleaned_df = cleaned_df[model_column_order]
        
        return cleaned_df
    
    def clean_records_data(self, records_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Limpia los datos de registros para inserción en BD.
        
        Args:
            records_data: Lista de diccionarios con datos de registros
            
        Returns:
            Lista de diccionarios limpiados
        """
        try:
            import pandas as pd
        except ImportError:
            return records_data
        
        cleaned_records = []
        
        for record in records_data:
            cleaned_record = {}
            for key, value in record.items():
                # Manejar valores NaN y NaT de pandas
                if pd.isna(value):
                    cleaned_record[key] = None
                # Manejar tipos numpy
                elif hasattr(value, 'item'):  # numpy scalars
                    cleaned_record[key] = value.item()
                else:
                    cleaned_record[key] = value
            
            cleaned_records.append(cleaned_record)
        
        return cleaned_records

        
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



class UserStatsDataFrameValidator:
    """ Validador de DataFrame para el modelo UserStats """

    def validate_dataframe_schema(
        self, 
        df: DataFrame, 
        ignore_extra_columns: bool, 
        fill_missing_nullable: bool
    ) -> None:
        """
        Valida que el esquema del DataFrame sea compatible con el modelo.
        
        Args:
            df: DataFrame a validar
            ignore_extra_columns: Si ignorar columnas extra
            fill_missing_nullable: Si llenar columnas nullable faltantes
            
        Raises:
            ValueError: Si el esquema no es compatible
        """
        # Definir columnas del modelo
        model_columns = {
            'username': {
                'type': 'str',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'email': {
                'type': 'str',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'total_chats': {
                'type': 'int',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'active_chats': {
                'type': 'int',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'total_messages': {
                'type': 'int',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'created_at': {
                'type': 'datetime',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'last_activity': {
                'type': 'datetime',
                'nullable': True,
                'primary_key': False,
                'autoincrement': False
            }
        }
        
        df_columns = set(df.columns)
        required_columns = set(model_columns.keys())
        
        # Verificar columnas extra
        extra_columns = df_columns - required_columns
        if extra_columns and not ignore_extra_columns:
            raise ValueError(
                f"DataFrame contiene columnas no definidas en el modelo: {list(extra_columns)}\n"
                f"Usa ignore_extra_columns=True para ignorarlas o elimínalas del DataFrame"
            )
        
        # Verificar columnas faltantes
        missing_columns = required_columns - df_columns
        
        # Filtrar columnas que pueden faltar
        critical_missing = []
        for col in missing_columns:
            col_info = model_columns[col]
            # Las columnas críticas son las que no son nullable, no son auto-increment y no son PK auto
            if (not col_info['nullable'] and 
                not col_info['autoincrement'] and 
                not (col_info['primary_key'] and col_info['autoincrement'])):
                critical_missing.append(col)
        
        if critical_missing:
            raise ValueError(
                f"DataFrame falta columnas requeridas (NOT NULL): {critical_missing}\n"
                f"Estas columnas son obligatorias y deben estar presentes en el DataFrame"
            )
        
        # Advertir sobre columnas nullable faltantes
        nullable_missing = [col for col in missing_columns if col not in critical_missing]
        if nullable_missing and not fill_missing_nullable:
            import warnings
            warnings.warn(
                f"DataFrame falta columnas nullable: {nullable_missing}\n"
                f"Usa fill_missing_nullable=True para llenarlas automáticamente con None"
            )
    
    def validate_dataframe_types(self, df: "DataFrame") -> None:
        """
        Valida que los tipos de datos del DataFrame sean compatibles.
        
        Args:
            df: DataFrame a validar
            
        Raises:
            TypeError: Si los tipos no son compatibles
        """
        
        # Mapeo de tipos SQLAlchemy a tipos pandas compatibles
        type_compatibility = {
            'username': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'email': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'total_chats': {
                'sqlalchemy_type': 'int',
                'compatible_pandas_types': [
                    'int64', 'Int64', 'int32', 'Int32', 'int16', 'Int16', 'int8', 'Int8', 'object'
                ]
            },
            'active_chats': {
                'sqlalchemy_type': 'int',
                'compatible_pandas_types': [
                    'int64', 'Int64', 'int32', 'Int32', 'int16', 'Int16', 'int8', 'Int8', 'object'
                ]
            },
            'total_messages': {
                'sqlalchemy_type': 'int',
                'compatible_pandas_types': [
                    'int64', 'Int64', 'int32', 'Int32', 'int16', 'Int16', 'int8', 'Int8', 'object'
                ]
            },
            'created_at': {
                'sqlalchemy_type': 'datetime',
                'compatible_pandas_types': [
                    'datetime64[ns]', 'object'
                ]
            },
            'last_activity': {
                'sqlalchemy_type': 'datetime',
                'compatible_pandas_types': [
                    'datetime64[ns]', 'object'
                ]
            }
        }
        
        type_errors = []
        
        for column in df.columns:
            if column in type_compatibility:
                df_dtype = str(df[column].dtype)
                compatible_types = type_compatibility[column]['compatible_pandas_types']
                sqlalchemy_type = type_compatibility[column]['sqlalchemy_type']
                
                if df_dtype not in compatible_types:
                    # Verificar si puede ser convertido
                    if self.can_convert_type(df[column], sqlalchemy_type):
                        continue
                    
                    type_errors.append(
                        f"Columna '{column}': tipo '{df_dtype}' no compatible con '{sqlalchemy_type}'. "
                        f"Tipos aceptados: {compatible_types}"
                    )
        
        if type_errors:
            raise TypeError(
                "Errores de tipo de datos encontrados:\n" + 
                "\n".join(f"  - {error}" for error in type_errors) +
                "\n\nConsidera convertir los tipos antes de la inserción."
            )
    
    def can_convert_type(self, series: "Series", target_sqlalchemy_type: str) -> bool:
        """
        Verifica si una serie puede ser convertida al tipo SQLAlchemy objetivo.
        
        Args:
            series: Serie de pandas a verificar
            target_sqlalchemy_type: Tipo SQLAlchemy objetivo
            
        Returns:
            bool: True si puede ser convertida
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas no está instalado. Para usar from_df(), instala pandas:\n"
                "pip install pandas\n"
                "o si usas poetry:\n"
                "poetry add pandas"
            )
        
        try:
            # Probar conversión en una muestra pequeña
            sample = series.dropna().head(10)
            if sample.empty:
                return True
            
            if 'int' in target_sqlalchemy_type:
                pd.to_numeric(sample, errors='raise')
            elif 'float' in target_sqlalchemy_type or 'Numeric' in target_sqlalchemy_type:
                pd.to_numeric(sample, errors='raise')
            elif 'bool' in target_sqlalchemy_type:
                # Verificar valores booleanos válidos
                valid_bool_values = {True, False, 1, 0, '1', '0', 'true', 'false', 'True', 'False'}
                if not all(val in valid_bool_values for val in sample.unique()):
                    return False
            elif 'datetime' in target_sqlalchemy_type or 'date' in target_sqlalchemy_type:
                pd.to_datetime(sample, errors='raise')
            
            return True
        except:
            return False
    
    def prepare_dataframe_for_insertion(
        self, 
        df: "DataFrame", 
        ignore_extra_columns: bool, 
        fill_missing_nullable: bool
    ) -> "DataFrame":
        """
        Prepara el DataFrame para inserción en la base de datos.
        
        Args:
            df: DataFrame original
            ignore_extra_columns: Si ignorar columnas extra
            fill_missing_nullable: Si llenar columnas faltantes nullable
            
        Returns:
            DataFrame preparado para inserción
        """
        try:
            import pandas as pd
            import numpy as np
        except ImportError:
            return df
        
        # Crear copia para no modificar el original
        cleaned_df = df.copy()
        
        # Definir columnas del modelo
        model_columns = {
            'username': {
                'nullable': False,
                'autoincrement': False
            },
            'email': {
                'nullable': False,
                'autoincrement': False
            },
            'total_chats': {
                'nullable': False,
                'autoincrement': False
            },
            'active_chats': {
                'nullable': False,
                'autoincrement': False
            },
            'total_messages': {
                'nullable': False,
                'autoincrement': False
            },
            'created_at': {
                'nullable': False,
                'autoincrement': False
            },
            'last_activity': {
                'nullable': True,
                'autoincrement': False
            }
        }
        
        # Eliminar columnas extra si se solicita
        if ignore_extra_columns:
            extra_columns = set(cleaned_df.columns) - set(model_columns.keys())
            if extra_columns:
                cleaned_df = cleaned_df.drop(columns=list(extra_columns))
        
        # Agregar columnas nullable faltantes si se solicita
        if fill_missing_nullable:
            for col_name, col_info in model_columns.items():
                if (col_name not in cleaned_df.columns and 
                    col_info['nullable'] and 
                    not col_info['autoincrement']):
                    cleaned_df[col_name] = None
        
        # Eliminar columnas autoincrement (la BD las manejará)
        autoincrement_columns = [
            col for col, info in model_columns.items() 
            if info['autoincrement'] and col in cleaned_df.columns
        ]
        if autoincrement_columns:
            cleaned_df = cleaned_df.drop(columns=autoincrement_columns)
        
        # Reordenar columnas según el modelo (las que existan)
        model_column_order = [col for col in model_columns.keys() if col in cleaned_df.columns]
        cleaned_df = cleaned_df[model_column_order]
        
        return cleaned_df
    
    def clean_records_data(self, records_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Limpia los datos de registros para inserción en BD.
        
        Args:
            records_data: Lista de diccionarios con datos de registros
            
        Returns:
            Lista de diccionarios limpiados
        """
        try:
            import pandas as pd
        except ImportError:
            return records_data
        
        cleaned_records = []
        
        for record in records_data:
            cleaned_record = {}
            for key, value in record.items():
                # Manejar valores NaN y NaT de pandas
                if pd.isna(value):
                    cleaned_record[key] = None
                # Manejar tipos numpy
                elif hasattr(value, 'item'):  # numpy scalars
                    cleaned_record[key] = value.item()
                else:
                    cleaned_record[key] = value
            
            cleaned_records.append(cleaned_record)
        
        return cleaned_records

        
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



class TokenConsumptionStatsDataFrameValidator:
    """ Validador de DataFrame para el modelo TokenConsumptionStats """

    def validate_dataframe_schema(
        self, 
        df: DataFrame, 
        ignore_extra_columns: bool, 
        fill_missing_nullable: bool
    ) -> None:
        """
        Valida que el esquema del DataFrame sea compatible con el modelo.
        
        Args:
            df: DataFrame a validar
            ignore_extra_columns: Si ignorar columnas extra
            fill_missing_nullable: Si llenar columnas nullable faltantes
            
        Raises:
            ValueError: Si el esquema no es compatible
        """
        # Definir columnas del modelo
        model_columns = {
            'username': {
                'type': 'str',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'date': {
                'type': 'datetime',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'total_prompt_tokens': {
                'type': 'int',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'total_completion_tokens': {
                'type': 'int',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'total_tokens': {
                'type': 'int',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'total_cost_usd': {
                'type': 'float',
                'nullable': True,
                'primary_key': False,
                'autoincrement': False
            },
            'chat_count': {
                'type': 'int',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'most_used_model': {
                'type': 'str',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'most_used_provider': {
                'type': 'str',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            }
        }
        
        df_columns = set(df.columns)
        required_columns = set(model_columns.keys())
        
        # Verificar columnas extra
        extra_columns = df_columns - required_columns
        if extra_columns and not ignore_extra_columns:
            raise ValueError(
                f"DataFrame contiene columnas no definidas en el modelo: {list(extra_columns)}\n"
                f"Usa ignore_extra_columns=True para ignorarlas o elimínalas del DataFrame"
            )
        
        # Verificar columnas faltantes
        missing_columns = required_columns - df_columns
        
        # Filtrar columnas que pueden faltar
        critical_missing = []
        for col in missing_columns:
            col_info = model_columns[col]
            # Las columnas críticas son las que no son nullable, no son auto-increment y no son PK auto
            if (not col_info['nullable'] and 
                not col_info['autoincrement'] and 
                not (col_info['primary_key'] and col_info['autoincrement'])):
                critical_missing.append(col)
        
        if critical_missing:
            raise ValueError(
                f"DataFrame falta columnas requeridas (NOT NULL): {critical_missing}\n"
                f"Estas columnas son obligatorias y deben estar presentes en el DataFrame"
            )
        
        # Advertir sobre columnas nullable faltantes
        nullable_missing = [col for col in missing_columns if col not in critical_missing]
        if nullable_missing and not fill_missing_nullable:
            import warnings
            warnings.warn(
                f"DataFrame falta columnas nullable: {nullable_missing}\n"
                f"Usa fill_missing_nullable=True para llenarlas automáticamente con None"
            )
    
    def validate_dataframe_types(self, df: "DataFrame") -> None:
        """
        Valida que los tipos de datos del DataFrame sean compatibles.
        
        Args:
            df: DataFrame a validar
            
        Raises:
            TypeError: Si los tipos no son compatibles
        """
        
        # Mapeo de tipos SQLAlchemy a tipos pandas compatibles
        type_compatibility = {
            'username': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'date': {
                'sqlalchemy_type': 'datetime',
                'compatible_pandas_types': [
                    'datetime64[ns]', 'object'
                ]
            },
            'total_prompt_tokens': {
                'sqlalchemy_type': 'int',
                'compatible_pandas_types': [
                    'int64', 'Int64', 'int32', 'Int32', 'int16', 'Int16', 'int8', 'Int8', 'object'
                ]
            },
            'total_completion_tokens': {
                'sqlalchemy_type': 'int',
                'compatible_pandas_types': [
                    'int64', 'Int64', 'int32', 'Int32', 'int16', 'Int16', 'int8', 'Int8', 'object'
                ]
            },
            'total_tokens': {
                'sqlalchemy_type': 'int',
                'compatible_pandas_types': [
                    'int64', 'Int64', 'int32', 'Int32', 'int16', 'Int16', 'int8', 'Int8', 'object'
                ]
            },
            'total_cost_usd': {
                'sqlalchemy_type': 'float',
                'compatible_pandas_types': [
                    'float64', 'float32', 'int64', 'Int64', 'object'
                ]
            },
            'chat_count': {
                'sqlalchemy_type': 'int',
                'compatible_pandas_types': [
                    'int64', 'Int64', 'int32', 'Int32', 'int16', 'Int16', 'int8', 'Int8', 'object'
                ]
            },
            'most_used_model': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'most_used_provider': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            }
        }
        
        type_errors = []
        
        for column in df.columns:
            if column in type_compatibility:
                df_dtype = str(df[column].dtype)
                compatible_types = type_compatibility[column]['compatible_pandas_types']
                sqlalchemy_type = type_compatibility[column]['sqlalchemy_type']
                
                if df_dtype not in compatible_types:
                    # Verificar si puede ser convertido
                    if self.can_convert_type(df[column], sqlalchemy_type):
                        continue
                    
                    type_errors.append(
                        f"Columna '{column}': tipo '{df_dtype}' no compatible con '{sqlalchemy_type}'. "
                        f"Tipos aceptados: {compatible_types}"
                    )
        
        if type_errors:
            raise TypeError(
                "Errores de tipo de datos encontrados:\n" + 
                "\n".join(f"  - {error}" for error in type_errors) +
                "\n\nConsidera convertir los tipos antes de la inserción."
            )
    
    def can_convert_type(self, series: "Series", target_sqlalchemy_type: str) -> bool:
        """
        Verifica si una serie puede ser convertida al tipo SQLAlchemy objetivo.
        
        Args:
            series: Serie de pandas a verificar
            target_sqlalchemy_type: Tipo SQLAlchemy objetivo
            
        Returns:
            bool: True si puede ser convertida
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas no está instalado. Para usar from_df(), instala pandas:\n"
                "pip install pandas\n"
                "o si usas poetry:\n"
                "poetry add pandas"
            )
        
        try:
            # Probar conversión en una muestra pequeña
            sample = series.dropna().head(10)
            if sample.empty:
                return True
            
            if 'int' in target_sqlalchemy_type:
                pd.to_numeric(sample, errors='raise')
            elif 'float' in target_sqlalchemy_type or 'Numeric' in target_sqlalchemy_type:
                pd.to_numeric(sample, errors='raise')
            elif 'bool' in target_sqlalchemy_type:
                # Verificar valores booleanos válidos
                valid_bool_values = {True, False, 1, 0, '1', '0', 'true', 'false', 'True', 'False'}
                if not all(val in valid_bool_values for val in sample.unique()):
                    return False
            elif 'datetime' in target_sqlalchemy_type or 'date' in target_sqlalchemy_type:
                pd.to_datetime(sample, errors='raise')
            
            return True
        except:
            return False
    
    def prepare_dataframe_for_insertion(
        self, 
        df: "DataFrame", 
        ignore_extra_columns: bool, 
        fill_missing_nullable: bool
    ) -> "DataFrame":
        """
        Prepara el DataFrame para inserción en la base de datos.
        
        Args:
            df: DataFrame original
            ignore_extra_columns: Si ignorar columnas extra
            fill_missing_nullable: Si llenar columnas faltantes nullable
            
        Returns:
            DataFrame preparado para inserción
        """
        try:
            import pandas as pd
            import numpy as np
        except ImportError:
            return df
        
        # Crear copia para no modificar el original
        cleaned_df = df.copy()
        
        # Definir columnas del modelo
        model_columns = {
            'username': {
                'nullable': False,
                'autoincrement': False
            },
            'date': {
                'nullable': False,
                'autoincrement': False
            },
            'total_prompt_tokens': {
                'nullable': False,
                'autoincrement': False
            },
            'total_completion_tokens': {
                'nullable': False,
                'autoincrement': False
            },
            'total_tokens': {
                'nullable': False,
                'autoincrement': False
            },
            'total_cost_usd': {
                'nullable': True,
                'autoincrement': False
            },
            'chat_count': {
                'nullable': False,
                'autoincrement': False
            },
            'most_used_model': {
                'nullable': False,
                'autoincrement': False
            },
            'most_used_provider': {
                'nullable': False,
                'autoincrement': False
            }
        }
        
        # Eliminar columnas extra si se solicita
        if ignore_extra_columns:
            extra_columns = set(cleaned_df.columns) - set(model_columns.keys())
            if extra_columns:
                cleaned_df = cleaned_df.drop(columns=list(extra_columns))
        
        # Agregar columnas nullable faltantes si se solicita
        if fill_missing_nullable:
            for col_name, col_info in model_columns.items():
                if (col_name not in cleaned_df.columns and 
                    col_info['nullable'] and 
                    not col_info['autoincrement']):
                    cleaned_df[col_name] = None
        
        # Eliminar columnas autoincrement (la BD las manejará)
        autoincrement_columns = [
            col for col, info in model_columns.items() 
            if info['autoincrement'] and col in cleaned_df.columns
        ]
        if autoincrement_columns:
            cleaned_df = cleaned_df.drop(columns=autoincrement_columns)
        
        # Reordenar columnas según el modelo (las que existan)
        model_column_order = [col for col in model_columns.keys() if col in cleaned_df.columns]
        cleaned_df = cleaned_df[model_column_order]
        
        return cleaned_df
    
    def clean_records_data(self, records_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Limpia los datos de registros para inserción en BD.
        
        Args:
            records_data: Lista de diccionarios con datos de registros
            
        Returns:
            Lista de diccionarios limpiados
        """
        try:
            import pandas as pd
        except ImportError:
            return records_data
        
        cleaned_records = []
        
        for record in records_data:
            cleaned_record = {}
            for key, value in record.items():
                # Manejar valores NaN y NaT de pandas
                if pd.isna(value):
                    cleaned_record[key] = None
                # Manejar tipos numpy
                elif hasattr(value, 'item'):  # numpy scalars
                    cleaned_record[key] = value.item()
                else:
                    cleaned_record[key] = value
            
            cleaned_records.append(cleaned_record)
        
        return cleaned_records

        
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



class ChatActivityDataFrameValidator:
    """ Validador de DataFrame para el modelo ChatActivity """

    def validate_dataframe_schema(
        self, 
        df: DataFrame, 
        ignore_extra_columns: bool, 
        fill_missing_nullable: bool
    ) -> None:
        """
        Valida que el esquema del DataFrame sea compatible con el modelo.
        
        Args:
            df: DataFrame a validar
            ignore_extra_columns: Si ignorar columnas extra
            fill_missing_nullable: Si llenar columnas nullable faltantes
            
        Raises:
            ValueError: Si el esquema no es compatible
        """
        # Definir columnas del modelo
        model_columns = {
            'chat_id': {
                'type': 'str',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'chat_title': {
                'type': 'str',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'username': {
                'type': 'str',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'message_count': {
                'type': 'int',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'last_message_timestamp': {
                'type': 'datetime',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'total_tokens_consumed': {
                'type': 'int',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            },
            'is_active': {
                'type': 'bool',
                'nullable': False,
                'primary_key': False,
                'autoincrement': False
            }
        }
        
        df_columns = set(df.columns)
        required_columns = set(model_columns.keys())
        
        # Verificar columnas extra
        extra_columns = df_columns - required_columns
        if extra_columns and not ignore_extra_columns:
            raise ValueError(
                f"DataFrame contiene columnas no definidas en el modelo: {list(extra_columns)}\n"
                f"Usa ignore_extra_columns=True para ignorarlas o elimínalas del DataFrame"
            )
        
        # Verificar columnas faltantes
        missing_columns = required_columns - df_columns
        
        # Filtrar columnas que pueden faltar
        critical_missing = []
        for col in missing_columns:
            col_info = model_columns[col]
            # Las columnas críticas son las que no son nullable, no son auto-increment y no son PK auto
            if (not col_info['nullable'] and 
                not col_info['autoincrement'] and 
                not (col_info['primary_key'] and col_info['autoincrement'])):
                critical_missing.append(col)
        
        if critical_missing:
            raise ValueError(
                f"DataFrame falta columnas requeridas (NOT NULL): {critical_missing}\n"
                f"Estas columnas son obligatorias y deben estar presentes en el DataFrame"
            )
        
        # Advertir sobre columnas nullable faltantes
        nullable_missing = [col for col in missing_columns if col not in critical_missing]
        if nullable_missing and not fill_missing_nullable:
            import warnings
            warnings.warn(
                f"DataFrame falta columnas nullable: {nullable_missing}\n"
                f"Usa fill_missing_nullable=True para llenarlas automáticamente con None"
            )
    
    def validate_dataframe_types(self, df: "DataFrame") -> None:
        """
        Valida que los tipos de datos del DataFrame sean compatibles.
        
        Args:
            df: DataFrame a validar
            
        Raises:
            TypeError: Si los tipos no son compatibles
        """
        
        # Mapeo de tipos SQLAlchemy a tipos pandas compatibles
        type_compatibility = {
            'chat_id': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'chat_title': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'username': {
                'sqlalchemy_type': 'str',
                'compatible_pandas_types': [
                    'object', 'string', 'category'
                ]
            },
            'message_count': {
                'sqlalchemy_type': 'int',
                'compatible_pandas_types': [
                    'int64', 'Int64', 'int32', 'Int32', 'int16', 'Int16', 'int8', 'Int8', 'object'
                ]
            },
            'last_message_timestamp': {
                'sqlalchemy_type': 'datetime',
                'compatible_pandas_types': [
                    'datetime64[ns]', 'object'
                ]
            },
            'total_tokens_consumed': {
                'sqlalchemy_type': 'int',
                'compatible_pandas_types': [
                    'int64', 'Int64', 'int32', 'Int32', 'int16', 'Int16', 'int8', 'Int8', 'object'
                ]
            },
            'is_active': {
                'sqlalchemy_type': 'bool',
                'compatible_pandas_types': [
                    'bool', 'boolean', 'object'
                ]
            }
        }
        
        type_errors = []
        
        for column in df.columns:
            if column in type_compatibility:
                df_dtype = str(df[column].dtype)
                compatible_types = type_compatibility[column]['compatible_pandas_types']
                sqlalchemy_type = type_compatibility[column]['sqlalchemy_type']
                
                if df_dtype not in compatible_types:
                    # Verificar si puede ser convertido
                    if self.can_convert_type(df[column], sqlalchemy_type):
                        continue
                    
                    type_errors.append(
                        f"Columna '{column}': tipo '{df_dtype}' no compatible con '{sqlalchemy_type}'. "
                        f"Tipos aceptados: {compatible_types}"
                    )
        
        if type_errors:
            raise TypeError(
                "Errores de tipo de datos encontrados:\n" + 
                "\n".join(f"  - {error}" for error in type_errors) +
                "\n\nConsidera convertir los tipos antes de la inserción."
            )
    
    def can_convert_type(self, series: "Series", target_sqlalchemy_type: str) -> bool:
        """
        Verifica si una serie puede ser convertida al tipo SQLAlchemy objetivo.
        
        Args:
            series: Serie de pandas a verificar
            target_sqlalchemy_type: Tipo SQLAlchemy objetivo
            
        Returns:
            bool: True si puede ser convertida
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas no está instalado. Para usar from_df(), instala pandas:\n"
                "pip install pandas\n"
                "o si usas poetry:\n"
                "poetry add pandas"
            )
        
        try:
            # Probar conversión en una muestra pequeña
            sample = series.dropna().head(10)
            if sample.empty:
                return True
            
            if 'int' in target_sqlalchemy_type:
                pd.to_numeric(sample, errors='raise')
            elif 'float' in target_sqlalchemy_type or 'Numeric' in target_sqlalchemy_type:
                pd.to_numeric(sample, errors='raise')
            elif 'bool' in target_sqlalchemy_type:
                # Verificar valores booleanos válidos
                valid_bool_values = {True, False, 1, 0, '1', '0', 'true', 'false', 'True', 'False'}
                if not all(val in valid_bool_values for val in sample.unique()):
                    return False
            elif 'datetime' in target_sqlalchemy_type or 'date' in target_sqlalchemy_type:
                pd.to_datetime(sample, errors='raise')
            
            return True
        except:
            return False
    
    def prepare_dataframe_for_insertion(
        self, 
        df: "DataFrame", 
        ignore_extra_columns: bool, 
        fill_missing_nullable: bool
    ) -> "DataFrame":
        """
        Prepara el DataFrame para inserción en la base de datos.
        
        Args:
            df: DataFrame original
            ignore_extra_columns: Si ignorar columnas extra
            fill_missing_nullable: Si llenar columnas faltantes nullable
            
        Returns:
            DataFrame preparado para inserción
        """
        try:
            import pandas as pd
            import numpy as np
        except ImportError:
            return df
        
        # Crear copia para no modificar el original
        cleaned_df = df.copy()
        
        # Definir columnas del modelo
        model_columns = {
            'chat_id': {
                'nullable': False,
                'autoincrement': False
            },
            'chat_title': {
                'nullable': False,
                'autoincrement': False
            },
            'username': {
                'nullable': False,
                'autoincrement': False
            },
            'message_count': {
                'nullable': False,
                'autoincrement': False
            },
            'last_message_timestamp': {
                'nullable': False,
                'autoincrement': False
            },
            'total_tokens_consumed': {
                'nullable': False,
                'autoincrement': False
            },
            'is_active': {
                'nullable': False,
                'autoincrement': False
            }
        }
        
        # Eliminar columnas extra si se solicita
        if ignore_extra_columns:
            extra_columns = set(cleaned_df.columns) - set(model_columns.keys())
            if extra_columns:
                cleaned_df = cleaned_df.drop(columns=list(extra_columns))
        
        # Agregar columnas nullable faltantes si se solicita
        if fill_missing_nullable:
            for col_name, col_info in model_columns.items():
                if (col_name not in cleaned_df.columns and 
                    col_info['nullable'] and 
                    not col_info['autoincrement']):
                    cleaned_df[col_name] = None
        
        # Eliminar columnas autoincrement (la BD las manejará)
        autoincrement_columns = [
            col for col, info in model_columns.items() 
            if info['autoincrement'] and col in cleaned_df.columns
        ]
        if autoincrement_columns:
            cleaned_df = cleaned_df.drop(columns=autoincrement_columns)
        
        # Reordenar columnas según el modelo (las que existan)
        model_column_order = [col for col in model_columns.keys() if col in cleaned_df.columns]
        cleaned_df = cleaned_df[model_column_order]
        
        return cleaned_df
    
    def clean_records_data(self, records_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Limpia los datos de registros para inserción en BD.
        
        Args:
            records_data: Lista de diccionarios con datos de registros
            
        Returns:
            Lista de diccionarios limpiados
        """
        try:
            import pandas as pd
        except ImportError:
            return records_data
        
        cleaned_records = []
        
        for record in records_data:
            cleaned_record = {}
            for key, value in record.items():
                # Manejar valores NaN y NaT de pandas
                if pd.isna(value):
                    cleaned_record[key] = None
                # Manejar tipos numpy
                elif hasattr(value, 'item'):  # numpy scalars
                    cleaned_record[key] = value.item()
                else:
                    cleaned_record[key] = value
            
            cleaned_records.append(cleaned_record)
        
        return cleaned_records

        
