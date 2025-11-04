# Este archivo ha sido generado automáticamente por tai-sql
# No modifiques este archivo directamente

from __future__ import annotations
from typing import List, Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime, date, time
from sqlalchemy import BigInteger, ForeignKeyConstraint
import os
from cryptography.fernet import Fernet
from sqlalchemy.ext.hybrid import hybrid_property
import base64


# Configuración de encriptación
_secret_key = os.getenv('SECRET_KEY')
if not _secret_key:
    raise ValueError(
        f"Variable de entorno 'SECRET_KEY' no encontrada para encriptación. "
        f"Por favor, configure la variable de entorno 'SECRET_KEY' en su sistema "
        f"con una clave secreta segura antes de ejecutar la aplicación. "
        f"Ejemplo: export SECRET_KEY='su-clave-secreta-de-32-caracteres-aqui'"
    )

# Generar clave Fernet desde la clave secreta
_fernet_key = base64.urlsafe_b64encode(_secret_key.encode()[:32].ljust(32, b'\0'))
_cipher = Fernet(_fernet_key)

def encrypt_value(value: str) -> str:
    """Encripta un valor string"""
    if value is None:
        return None
    return _cipher.encrypt(value.encode()).decode()

def decrypt_value(value: str) -> str:
    """Desencripta un valor string"""
    if value is None:
        return None
    return _cipher.decrypt(value.encode()).decode()


class Base(DeclarativeBase):
    pass

class Usuario(Base):
    __tablename__ = "usuario"

    def __init__(self, **kwargs):
        # Manejar columnas encriptadas especialmente
        if 'password' in kwargs:
            password_value = kwargs.pop('password')
            self.password = password_value

        super().__init__(**kwargs)

    username: Mapped[str] = mapped_column(primary_key=True)
    _password: Mapped[str] = mapped_column(name="password")
    
    @hybrid_property
    def password(self) -> str:
        """Propiedad encriptada para password"""
        if self._password is None:
            return None
        return decrypt_value(self._password)
    
    @password.setter
    def password(self, value: str):
        """Setter encriptado para password"""
        if value is None:
            self._password = None
        else:
            self._password = encrypt_value(str(value))
    
    email: Mapped[Optional[str]]
    avatar: Mapped[Optional[str]]
    session_id: Mapped[Optional[str]]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    chats: Mapped[List[Chat]] = relationship(back_populates="usuario")

    __table_args__ = {'schema': 'chatbot'}

class Chat(Base):
    __tablename__ = "chat"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str]
    username: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    messages: Mapped[List[Mensaje]] = relationship(back_populates="chat")
    usuario: Mapped[Usuario] = relationship(back_populates="chats")

    __table_args__ = (
        # Clave foránea simple: fk_chat_usuario
        ForeignKeyConstraint(
            # Columnas locales
            ['username'],
            # Columnas objetivo
            ['chatbot.usuario.username'],
            ondelete='CASCADE',
            onupdate='CASCADE'
        ),
        # Esquema de la tabla
        {'schema': 'chatbot'}
    )

class Mensaje(Base):
    __tablename__ = "mensaje"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    content: Mapped[str]
    role: Mapped[str]
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now)
    chat_id: Mapped[int] = mapped_column(BigInteger)
    
    token_usage: Mapped[List[TokenUsage]] = relationship(back_populates="message")
    chat: Mapped[Chat] = relationship(back_populates="messages")

    __table_args__ = (
        # Clave foránea simple: fk_mensaje_chat
        ForeignKeyConstraint(
            # Columnas locales
            ['chat_id'],
            # Columnas objetivo
            ['chatbot.chat.id'],
            ondelete='CASCADE',
            onupdate='CASCADE'
        ),
        # Esquema de la tabla
        {'schema': 'chatbot'}
    )

class TokenUsage(Base):
    __tablename__ = "token_usage"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    prompt_tokens: Mapped[int] = mapped_column(default=0)
    completion_tokens: Mapped[int] = mapped_column(default=0)
    total_tokens: Mapped[int] = mapped_column(default=0)
    model_name: Mapped[str]
    provider: Mapped[str]
    cost_usd: Mapped[Optional[float]]
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now)
    message_id: Mapped[int] = mapped_column(BigInteger)
    
    message: Mapped[Mensaje] = relationship(back_populates="token_usage")

    __table_args__ = (
        # Clave foránea simple: fk_token_usage_mensaje
        ForeignKeyConstraint(
            # Columnas locales
            ['message_id'],
            # Columnas objetivo
            ['chatbot.mensaje.id'],
            ondelete='CASCADE',
            onupdate='CASCADE'
        ),
        # Esquema de la tabla
        {'schema': 'chatbot'}
    )

class UserStats(Base):
    __tablename__ = "user_stats"

    is_view = True
    username: Mapped[str]
    email: Mapped[str]
    total_chats: Mapped[int]
    active_chats: Mapped[int]
    total_messages: Mapped[int]
    created_at: Mapped[datetime]
    last_activity: Mapped[Optional[datetime]]

    __table_args__ = {'schema': 'chatbot'}
    __mapper_args__ = {'primary_key': [
        'username',
        'email',
        'total_chats',
        'active_chats',
        'total_messages',
        'created_at',
        'last_activity',
    ]}

class TokenConsumptionStats(Base):
    __tablename__ = "token_consumption_stats"

    is_view = True
    username: Mapped[str]
    date: Mapped[datetime]
    total_prompt_tokens: Mapped[int]
    total_completion_tokens: Mapped[int]
    total_tokens: Mapped[int]
    total_cost_usd: Mapped[Optional[float]]
    chat_count: Mapped[int]
    most_used_model: Mapped[str]
    most_used_provider: Mapped[str]

    __table_args__ = {'schema': 'chatbot'}
    __mapper_args__ = {'primary_key': [
        'username',
        'date',
        'total_prompt_tokens',
        'total_completion_tokens',
        'total_tokens',
        'total_cost_usd',
        'chat_count',
        'most_used_model',
        'most_used_provider',
    ]}

class ChatActivity(Base):
    __tablename__ = "chat_activity"

    is_view = True
    chat_id: Mapped[str]
    chat_title: Mapped[str]
    username: Mapped[str]
    message_count: Mapped[int]
    last_message_timestamp: Mapped[datetime]
    total_tokens_consumed: Mapped[int]
    is_active: Mapped[bool]

    __table_args__ = {'schema': 'chatbot'}
    __mapper_args__ = {'primary_key': [
        'chat_id',
        'chat_title',
        'username',
        'message_count',
        'last_message_timestamp',
        'total_tokens_consumed',
        'is_active',
    ]}

