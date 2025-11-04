"""
Gestor de conexiones WebSocket para chat streaming
"""
from __future__ import annotations
from typing import Dict, Set, Optional
from pydantic import BaseModel
from fastapi import WebSocket
import json
from datetime import datetime
import asyncio
import uuid
from tai_alphi import Alphi

from .resources.exceptions import APIException
from .config import ConnectionConfig

logger = Alphi.get_logger_by_name("tai-chatbot")

class Connection(BaseModel):
    """Modelo de conexión WebSocket"""
    websocket: WebSocket
    username: str
    chat_id: int
    connected_at: datetime
    
    class Config:
        arbitrary_types_allowed = True  # Permite tipos como WebSocket

class ConnectionManager:
    """Gestor de conexiones WebSocket para chat streaming"""
    
    def __init__(self, config: Optional[ConnectionConfig] = None):
        # Cargar configuración
        self.config = config or ConnectionConfig.load()
        
        # connection_id -> Connection
        self.connections: Dict[str, Connection] = {}
        # username -> Set[connection_id] 
        self.user_connections: Dict[str, Set[str]] = {}
        # chat_id -> Set[connection_id]
        self.chat_connections: Dict[int, Set[str]] = {}
        # connection_id -> last_activity
        self.last_activity: Dict[str, datetime] = {}
        
        # Iniciar tarea de limpieza
        self._cleanup_task = None
    
    def _check_connection_limit(self) -> bool:
        """Verificar si se puede aceptar una nueva conexión"""
        return len(self.connections) < self.config.max_concurrent_connections
    
    async def connect(
        self, 
        websocket: WebSocket, 
        username: str,
        chat_id: int
    ) -> str:
        """
        Conectar un nuevo WebSocket
        
        Args:
            websocket: Conexión WebSocket
            username: ID del usuario
            chat_id: ID del chat
            
        Returns:
            str: ID de conexión único
            
        Raises:
            Exception: Si se alcanza el límite de conexiones
        """
        # Verificar límite de conexiones
        if not self._check_connection_limit():
            await websocket.close(code=1008, reason="Límite de conexiones alcanzado")
            raise APIException(
                f"Límite de conexiones alcanzado",
                details={'max_concurrent_connections': self.config.max_concurrent_connections}
            )
        
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Registrar conexión
        self.connections[connection_id] = Connection(
            websocket=websocket,
            username=username,
            chat_id=chat_id,
            connected_at=now
        )
        
        # Registrar por usuario
        if username not in self.user_connections:
            self.user_connections[username] = set()
        self.user_connections[username].add(connection_id)
        
        # Registrar por chat
        if chat_id not in self.chat_connections:
            self.chat_connections[chat_id] = set()
        self.chat_connections[chat_id].add(connection_id)
        
        # Actualizar actividad
        self.last_activity[connection_id] = now
        
        logger.info(f"Nueva conexión WebSocket: {connection_id} (user: {username}, chat: {chat_id})")
        
        # Iniciar tarea de limpieza si no existe
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            pass
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """
        Desconectar un WebSocket
        
        Args:
            connection_id: ID de la conexión
        """
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        username = connection.username
        chat_id = connection.chat_id
        
        # Remover de registros
        del self.connections[connection_id]
        
        if connection_id in self.last_activity:
            del self.last_activity[connection_id]
        
        # Remover de usuario
        if username in self.user_connections:
            self.user_connections[username].discard(connection_id)
            if not self.user_connections[username]:
                del self.user_connections[username]
        
        # Remover de chat
        if chat_id in self.chat_connections:
            self.chat_connections[chat_id].discard(connection_id)
            if not self.chat_connections[chat_id]:
                del self.chat_connections[chat_id]
        
        logger.info(f"Conexión WebSocket desconectada: {connection_id}")
    
    async def send_to_connection(
        self, 
        connection_id: str, 
        data: Dict
    ) -> bool:
        """
        Enviar datos a una conexión específica
        
        Args:
            connection_id: ID de la conexión
            data: Datos a enviar
            
        Returns:
            bool: True si se envió correctamente
        """
        if connection_id not in self.connections:
            return False
        
        try:
            websocket = self.connections[connection_id].websocket
            await websocket.send_text(json.dumps(data))
            self.last_activity[connection_id] = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Error enviando a conexión {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False
    
    async def send_to_chat(self, chat_id: str, data: Dict) -> int:
        """
        Enviar datos a todas las conexiones de un chat
        
        Args:
            chat_id: ID del chat
            data: Datos a enviar
            
        Returns:
            int: Número de conexiones que recibieron el mensaje
        """
        if chat_id not in self.chat_connections:
            return 0
        
        sent_count = 0
        connections_to_remove = []
        
        for connection_id in self.chat_connections[chat_id].copy():
            success = await self.send_to_connection(connection_id, data)
            if success:
                sent_count += 1
            else:
                connections_to_remove.append(connection_id)
        
        # Limpiar conexiones fallidas
        for connection_id in connections_to_remove:
            await self.disconnect(connection_id)
        
        return sent_count
    
    async def send_to_user(self, username: str, data: Dict) -> int:
        """
        Enviar datos a todas las conexiones de un usuario
        
        Args:
            username: ID del usuario
            data: Datos a enviar
            
        Returns:
            int: Número de conexiones que recibieron el mensaje
        """
        if username not in self.user_connections:
            return 0
        
        sent_count = 0
        connections_to_remove = []
        
        for connection_id in self.user_connections[username].copy():
            success = await self.send_to_connection(connection_id, data)
            if success:
                sent_count += 1
            else:
                connections_to_remove.append(connection_id)
        
        # Limpiar conexiones fallidas
        for connection_id in connections_to_remove:
            await self.disconnect(connection_id)
        
        return sent_count
    
    def get_connection_info(self, connection_id: str) -> Optional[Connection]:
        """Obtener información de una conexión"""
        return self.connections.get(connection_id)
    
    def get_active_connections_count(self) -> int:
        """Obtener número total de conexiones activas"""
        return len(self.connections)
    
    def get_chat_connections_count(self, chat_id: str) -> int:
        """Obtener número de conexiones activas para un chat"""
        return len(self.chat_connections.get(chat_id, set()))
    
    def get_user_connections_count(self, username: str) -> int:
        """Obtener número de conexiones activas para un usuario"""
        return len(self.user_connections.get(username, set()))
    
    def get_config(self) -> ConnectionConfig:
        """Obtener la configuración actual"""
        return self.config
    
    def update_config(self, new_config: ConnectionConfig) -> None:
        """Actualizar la configuración"""
        self.config = new_config
        logger.info(f"Configuración WebSocket actualizada: timeout={self.config.websocket_timeout}s, max_connections={self.config.max_concurrent_connections}")
    
    def reload_config(self) -> None:
        """Recargar configuración desde .chatbotconfig"""
        new_config = ConnectionConfig.load()
        self.update_config(new_config)
    
    async def _periodic_cleanup(self):
        """Tarea periódica de limpieza de conexiones inactivas"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_stale_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en limpieza periódica: {e}")
    
    async def _cleanup_stale_connections(self):
        """Limpiar conexiones inactivas o cerradas"""
        now = datetime.now()
        timeout_seconds = self.config.websocket_timeout
        
        stale_connections = []
        
        for connection_id, last_activity in self.last_activity.items():
            # Verificar timeout
            if (now - last_activity).total_seconds() > timeout_seconds:
                stale_connections.append(connection_id)
                continue
            
            # Verificar si la conexión está cerrada
            if connection_id in self.connections:
                websocket = self.connections[connection_id].websocket
                try:
                    # Enviar ping para verificar conexión
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    stale_connections.append(connection_id)
        
        # Limpiar conexiones stale
        for connection_id in stale_connections:
            await self.disconnect(connection_id)
        
        if stale_connections:
            logger.info(f"Limpiadas {len(stale_connections)} conexiones inactivas")

# Cargar configuración global
websocket_config = ConnectionConfig.load()

# Instancia global del gestor de conexiones con configuración
connection_manager = ConnectionManager(config=websocket_config)
