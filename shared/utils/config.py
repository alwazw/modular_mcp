"""
Configuration management for the Multi-Agent MCP System
"""

import os
import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = "sqlite:///multi_agent_mcp.db"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30

@dataclass
class RedisConfig:
    """Redis configuration"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 10

@dataclass
class AgentConfig:
    """Individual agent configuration"""
    name: str
    enabled: bool = True
    max_workers: int = 4
    timeout: int = 300
    retry_attempts: int = 3
    log_level: str = "INFO"

@dataclass
class ScrapingConfig:
    """Web scraping configuration"""
    user_agent: str = "Multi-Agent-MCP-Bot/1.0"
    request_delay: float = 1.0
    max_retries: int = 3
    timeout: int = 30
    respect_robots_txt: bool = True
    max_pages_per_site: int = 100

@dataclass
class KnowledgeConfig:
    """Knowledge base configuration"""
    embedding_model: str = "text-embedding-ada-002"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_tokens: int = 8000
    similarity_threshold: float = 0.7

@dataclass
class TransformationConfig:
    """Data transformation configuration"""
    ai_model: str = "gpt-4"
    confidence_threshold: float = 0.8
    max_field_mappings: int = 50
    learning_rate: float = 0.1

@dataclass
class SystemConfig:
    """Main system configuration"""
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    secret_key: str = "your-secret-key-here"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Component configurations
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    scraping: ScrapingConfig = ScrapingConfig()
    knowledge: KnowledgeConfig = KnowledgeConfig()
    transformation: TransformationConfig = TransformationConfig()
    
    # Agent configurations
    agents: Dict[str, AgentConfig] = None
    
    def __post_init__(self):
        if self.agents is None:
            self.agents = {
                "agent1_scraper": AgentConfig("Web Scraper & Data Collector"),
                "agent2_knowledge": AgentConfig("Knowledge Base Creator"),
                "agent3_database": AgentConfig("Database Manager"),
                "agent4_transformer": AgentConfig("Intelligent Data Transformer")
            }

class ConfigManager:
    """Manages system configuration from multiple sources"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._find_config_file()
        self.config = SystemConfig()
        self._load_config()
    
    def _find_config_file(self) -> Optional[str]:
        """Find configuration file in standard locations"""
        possible_locations = [
            "config.yaml",
            "config.yml",
            "config.json",
            "/etc/multi_agent_mcp/config.yaml",
            os.path.expanduser("~/.multi_agent_mcp/config.yaml")
        ]
        
        for location in possible_locations:
            if os.path.exists(location):
                return location
        
        return None
    
    def _load_config(self):
        """Load configuration from file and environment variables"""
        # Load from file if exists
        if self.config_file and os.path.exists(self.config_file):
            self._load_from_file()
        
        # Override with environment variables
        self._load_from_env()
    
    def _load_from_file(self):
        """Load configuration from YAML or JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                if self.config_file.endswith(('.yaml', '.yml')):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            self._update_config_from_dict(data)
            
        except Exception as e:
            print(f"Error loading config file {self.config_file}: {e}")
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'MCP_ENVIRONMENT': 'environment',
            'MCP_DEBUG': 'debug',
            'MCP_LOG_LEVEL': 'log_level',
            'MCP_SECRET_KEY': 'secret_key',
            'MCP_API_HOST': 'api_host',
            'MCP_API_PORT': 'api_port',
            
            # Database
            'MCP_DATABASE_URL': 'database.url',
            'MCP_DATABASE_ECHO': 'database.echo',
            
            # Redis
            'MCP_REDIS_HOST': 'redis.host',
            'MCP_REDIS_PORT': 'redis.port',
            'MCP_REDIS_DB': 'redis.db',
            'MCP_REDIS_PASSWORD': 'redis.password',
            
            # OpenAI
            'OPENAI_API_KEY': 'openai_api_key',
            'OPENAI_API_BASE': 'openai_api_base',
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_config(config_path, value)
    
    def _update_config_from_dict(self, data: Dict[str, Any]):
        """Update configuration from dictionary"""
        for key, value in data.items():
            if hasattr(self.config, key):
                if isinstance(value, dict) and hasattr(getattr(self.config, key), '__dict__'):
                    # Update nested configuration object
                    nested_config = getattr(self.config, key)
                    for nested_key, nested_value in value.items():
                        if hasattr(nested_config, nested_key):
                            setattr(nested_config, nested_key, nested_value)
                else:
                    setattr(self.config, key, value)
    
    def _set_nested_config(self, path: str, value: str):
        """Set nested configuration value from dot-separated path"""
        parts = path.split('.')
        obj = self.config
        
        # Navigate to the parent object
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return
        
        # Set the final value with type conversion
        final_key = parts[-1]
        if hasattr(obj, final_key):
            current_value = getattr(obj, final_key)
            
            # Convert string value to appropriate type
            if isinstance(current_value, bool):
                value = value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(current_value, int):
                value = int(value)
            elif isinstance(current_value, float):
                value = float(value)
            
            setattr(obj, final_key, value)
    
    def get_config(self) -> SystemConfig:
        """Get the current configuration"""
        return self.config
    
    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get configuration for a specific agent"""
        return self.config.agents.get(agent_id)
    
    def save_config(self, file_path: Optional[str] = None):
        """Save current configuration to file"""
        if file_path is None:
            file_path = self.config_file or "config.yaml"
        
        config_dict = self._config_to_dict()
        
        try:
            with open(file_path, 'w') as f:
                if file_path.endswith(('.yaml', '.yml')):
                    yaml.dump(config_dict, f, default_flow_style=False)
                else:
                    json.dump(config_dict, f, indent=2)
        except Exception as e:
            print(f"Error saving config to {file_path}: {e}")
    
    def _config_to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        def obj_to_dict(obj):
            if hasattr(obj, '__dict__'):
                return {k: obj_to_dict(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, dict):
                return {k: obj_to_dict(v) for k, v in obj.items()}
            else:
                return obj
        
        return obj_to_dict(self.config)
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate database URL
        if not self.config.database.url:
            errors.append("Database URL is required")
        
        # Validate Redis configuration
        if not self.config.redis.host:
            errors.append("Redis host is required")
        
        if not (1 <= self.config.redis.port <= 65535):
            errors.append("Redis port must be between 1 and 65535")
        
        # Validate API configuration
        if not (1 <= self.config.api_port <= 65535):
            errors.append("API port must be between 1 and 65535")
        
        # Validate agent configurations
        for agent_id, agent_config in self.config.agents.items():
            if not agent_config.name:
                errors.append(f"Agent {agent_id} must have a name")
            
            if agent_config.max_workers < 1:
                errors.append(f"Agent {agent_id} must have at least 1 worker")
        
        return errors

# Global configuration instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_config() -> SystemConfig:
    """Get the current system configuration"""
    return get_config_manager().get_config()

def get_agent_config(agent_id: str) -> Optional[AgentConfig]:
    """Get configuration for a specific agent"""
    return get_config_manager().get_agent_config(agent_id)

# Environment-specific configuration helpers
def is_development() -> bool:
    """Check if running in development environment"""
    return get_config().environment == "development"

def is_production() -> bool:
    """Check if running in production environment"""
    return get_config().environment == "production"

def get_database_url() -> str:
    """Get the database URL"""
    return get_config().database.url

def get_redis_config() -> RedisConfig:
    """Get Redis configuration"""
    return get_config().redis

