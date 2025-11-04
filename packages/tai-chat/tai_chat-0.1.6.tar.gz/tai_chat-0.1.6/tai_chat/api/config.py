"""
Configuración del sistema
"""
from __future__ import annotations
import json
from typing import Literal, Optional, Dict, Any, List, ClassVar
from pydantic_settings import BaseSettings
from pydantic import Field, BaseModel
from pathlib import Path
from tai_alphi import Alphi

logger = Alphi.get_logger_by_name("tai-chatbot")

class ConfigUtils(BaseSettings):

    @staticmethod
    def config_path() -> Path:
        """Obtener la ruta del archivo de configuración"""
        return Path(__file__).parent / ".config.json"
    
    @classmethod
    def load_file(cls) -> Dict[str, Any]:
        """Cargar configuración desde .config.json"""
        config_path = cls.config_path()
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"[chatbot-config] Error cargando .config.json: {e}")
                return {}
        else:
            logger.error(f"[chatbot-config] Archivo .config.json no encontrado en {config_path}")
            return {}


class LLMConfig(ConfigUtils):
    """Configuración del sistema LLM"""

    _instance: ClassVar[Optional[LLMConfig]] = None  # Singleton instance

    # Proveedor activo
    provider: Literal["openai", "azure-openai", "anthropic", "gemini"] = Field(
        default="openai",
        description="Proveedor de LLM activo"
    )
    # Configuración modelo
    api_key: Optional[str] = Field(
        default=None,
        description="API Key"
    )
    model: str = Field(
        default="gpt-4o",
        description="Modelo a usar"
    )
    prompt: List[str] = Field(
        default=["You are a helpful assistant."],
        description="Prompt del sistema"
    )
    endpoint: Optional[str] = Field(
        default=None,
        description="Endpoint para proveedores cloud"
    )
    
    # Configuración general
    max_tokens: int = Field(
        default=2048,
        description="Máximo número de tokens en respuesta"
    )
    temperature: float = Field(
        default=0.7,
        description="Temperatura para generación (0.0-1.0)"
    )
    
    # Configuración de memoria
    max_context_tokens: int = Field(
        default=4000,
        description="Máximo de tokens para contexto de conversación"
    )
    context_database_url: Optional[str] = Field(
        default=None,
        description="URL de la base de datos para almacenar contexto (si aplica)"
    )
    
    model_config = {
        "case_sensitive": False
    }

    @classmethod
    def load(cls) -> LLMConfig:
        """Crear instancia de LLMConfig con valores del .config.json"""
        if cls._instance is not None:
            return cls._instance  # Retornar instancia singleton si ya existe
        
        chatbot_config = cls.load_file()
        
        # Combinar configuración de llm y connections
        config_data = {}
        
        # Cargar configuración LLM
        if "llm" in chatbot_config:
            config_data.update(chatbot_config["llm"])
        
        # Crear instancia con los valores del config
        cls._instance = cls(**config_data)
        return cls._instance
    
    def save(self) -> None:
        """Guardar configuración actual al archivo .config.json"""
        config_path = self.config_path()
        
        # Separar configuración en las dos claves
        config_data = {
            "llm": {
                "provider": self.provider,
                "model": self.model,
                "endpoint": self.endpoint,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "max_context_tokens": self.max_context_tokens
            }
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
        except OSError as e:
            print(f"Error guardando .config.json: {e}")
    
    def reload(self) -> LLMConfig:
        """Recargar configuración desde .config.json y actualizar la instancia actual"""
        new_config = self.load()
        
        # Actualizar todos los campos de la instancia actual
        for field_name, field_value in new_config.model_dump().items():
            setattr(self, field_name, field_value)
        
        return self
    
class ConnectionConfig(ConfigUtils):
    """Configuración de conexiones WebSocket"""
    _instance: ClassVar[Optional[ConnectionConfig]] = None  # Singleton instance

    websocket_timeout: int = Field(
        default=300,  # 5 minutos
        description="Timeout para conexiones WebSocket en segundos"
    )
    max_concurrent_connections: int = Field(
        default=100,
        description="Máximo número de conexiones WebSocket concurrentes"
    )
    cleanup_interval: int = Field(
        default=900, # 15 minutos
        description="Frecuencia de limpieza de conexiones inactivas en segundos"
    )
    
    @classmethod
    def load(cls) -> ConnectionConfig:
        """Cargar configuración desde .config.json"""
        if cls._instance is not None:
            return cls._instance  # Retornar instancia singleton si ya existe
        
        chatbot_config = cls.load_file()
        
        # Combinar configuración de llm y connections
        config_data = {}
        
        # Cargar configuración LLM
        if "websockets" in chatbot_config:
            config_data.update(chatbot_config["websockets"])
        
        # Crear instancia con los valores del config
        cls._instance = cls(**config_data)
        return cls._instance

class Config(BaseModel):
    llm: LLMConfig = Field(
        default_factory=LLMConfig.load,
        description="Configuración del LLM"
    )
    websockets: ConnectionConfig = Field(
        default_factory=ConnectionConfig.load,
        description="Configuración de conexiones WebSocket"
    )