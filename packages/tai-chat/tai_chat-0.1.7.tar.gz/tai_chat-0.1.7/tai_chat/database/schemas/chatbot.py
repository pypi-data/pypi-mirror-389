# -*- coding: utf-8 -*-
"""
Fuente principal para la definición de esquemas y generación de modelos CRUD.
Usa el contenido de tai_sql para definir tablas, relaciones, vistas y generar automáticamente modelos y CRUDs.
Usa tai_sql.generators para generar modelos y CRUDs basados en las tablas definidas.
Ejecuta por consola tai_sql generate para generar los recursos definidos en este esquema.
"""
from __future__ import annotations
from tai_sql import *
from tai_sql.generators import *
from database.custom_generators import *

# Configurar el datasource
datasource(
    provider=env('CHATBOT_DATABASE_URL'), # Además de env, también puedes usar (para testing) connection_string y params
    schema='chatbot', # Esquema del datasource
)

# Configurar los generadores
generate(
    CustomModelsGenerator(
        output_dir='tai_chat/api/database' # Directorio donde se generarán los modelos
    ),
    ModelsGenerator('tai_chat/cli/commands/cmd_adduser'),
    CustomAsyncCRUDGenerator(
        output_dir='tai_chat/api/database',
        logger_name='tai-chatbot'
    ),
    CRUDGenerator('tai_chat/cli/commands/cmd_adduser', logger_name='tai-chatbot', models_import_path='...models'),
    CustomERDiagramGenerator(
        output_dir='tai_chat/api/database', # Directorio donde se generarán los diagramas
    )
)

# Definición de tablas y relaciones para TAI-CHAT

class Usuario(Table):
    """Tabla que almacena información de los usuarios del chatbot"""
    __tablename__ = "usuario"

    username: str = column(primary_key=True, description='Nombre de usuario único')
    password: str = column(encrypt=True, description='Contraseña encriptada')
    email: Optional[str] = column(description='Correo electrónico del usuario')
    avatar: Optional[str] = column(description='URL del avatar del usuario')
    session_id: Optional[str] = column(description='ID de la sesión activa del usuario')
    created_at: datetime = column(default=datetime.now, description='Fecha de creación del usuario')
    updated_at: datetime = column(default=datetime.now, description='Fecha de última actualización')
    is_active: bool = column(default=True, description='Estado activo del usuario')

    chats: List[Chat] # Relación one-to-many con la tabla Chat


class MessageRole(Enum):
    """Roles de los mensajes en el chat"""
    USER = 'usuario'
    ASSISTANT = 'asistente'
    SYSTEM = 'sistema'


class Chat(Table):
    """Tabla que almacena las conversaciones del chatbot"""
    __tablename__ = "chat"

    id: bigint = column(primary_key=True, autoincrement=True, description='UUID del chat')
    title: str = column(description='Título de la conversación')
    username: str = column(description='ID del usuario propietario del chat')
    created_at: datetime = column(default=datetime.now, description='Fecha de creación del chat')
    updated_at: datetime = column(default=datetime.now, description='Fecha de última actualización')
    is_active: bool = column(default=True, description='Estado activo del chat')

    messages: List[Mensaje] # Relación one-to-many con la tabla Mensaje
    
    usuario: Usuario = relation(fields=['username'], references=['username'], backref='chats') # Relación many-to-one con Usuario


class Mensaje(Table):
    """Tabla que almacena los mensajes individuales de cada chat"""
    __tablename__ = "mensaje"

    id: bigint = column(primary_key=True, autoincrement=True, description='UUID del mensaje')
    content: str = column(description='Contenido del mensaje')
    role: MessageRole = column(description='Rol del mensaje (user, assistant, system)')
    timestamp: datetime = column(default=datetime.now, description='Timestamp del mensaje')
    chat_id: bigint = column(description='ID del chat al que pertenece el mensaje')

    token_usage: List[TokenUsage] # Relación one-to-many con la tabla TokenUsage

    chat: Chat = relation(fields=['chat_id'], references=['id'], backref='messages') # Relación many-to-one con Chat


class TokenUsage(Table):
    """Tabla que almacena el consumo de tokens para métricas y facturación"""
    __tablename__ = "token_usage"

    id: bigint = column(primary_key=True, autoincrement=True)
    prompt_tokens: int = column(default=0, description='Tokens consumidos en el prompt')
    completion_tokens: int = column(default=0, description='Tokens consumidos en la respuesta')
    total_tokens: int = column(default=0, description='Total de tokens consumidos')
    model_name: str = column(description='Nombre del modelo utilizado')
    provider: str = column(description='Proveedor del modelo (OpenAI, Anthropic, etc.)')
    cost_usd: Optional[float] = column(description='Costo estimado en USD')
    timestamp: datetime = column(default=datetime.now, description='Timestamp del consumo')
    message_id: bigint = column(description='ID del mensaje asociado')

    message: Mensaje = relation(fields=['message_id'], references=['id'], backref='token_usage') # Relación one-to-one con Mensaje


# Definición de vistas

class UserStats(View):
    """Vista que muestra estadísticas de usuarios y sus chats"""
    __tablename__ = "user_stats"
    __query__ = query('user_stats.sql') # Esto es necesario para usar tai-sql push

    username: str
    email: str
    total_chats: int
    active_chats: int
    total_messages: int
    created_at: datetime
    last_activity: Optional[datetime]


class TokenConsumptionStats(View):
    """Vista que muestra estadísticas de consumo de tokens por usuario y período"""
    __tablename__ = "token_consumption_stats"
    __query__ = query('token_consumption_stats.sql')

    username: str
    date: datetime
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_cost_usd: Optional[float]
    chat_count: int
    most_used_model: str
    most_used_provider: str


class ChatActivity(View):
    """Vista que muestra la actividad reciente de chats"""
    __tablename__ = "chat_activity"
    __query__ = query('chat_activity.sql')

    chat_id: str
    chat_title: str
    username: str
    message_count: int
    last_message_timestamp: datetime
    total_tokens_consumed: int
    is_active: bool
    