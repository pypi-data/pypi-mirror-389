"""Configuration management for YAML/JSON config files."""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from .exceptions import ConfigurationError

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize config manager.
        
        Args:
            config_path: Optional path to config file
        """
        self.config: Dict[str, Any] = {}
        if config_path:
            self.load(config_path)
    
    def load(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file.
        
        Args:
            config_path: Path to config file (YAML or JSON)
            
        Returns:
            Loaded configuration dictionary
            
        Raises:
            ConfigurationError: If file cannot be loaded or parsed
        """
        path = Path(config_path)
        if not path.exists():
            raise ConfigurationError(f"Config file not found: {config_path}")
        
        try:
            if path.suffix.lower() in ['.yaml', '.yml']:
                if not _YAML_AVAILABLE:
                    raise ConfigurationError(
                        "YAML support requires PyYAML. Install with: pip install pyyaml"
                    )
                import yaml
                with open(path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f) or {}
            elif path.suffix.lower() == '.json':
                with open(path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                raise ConfigurationError(
                    f"Unsupported config file format: {path.suffix}. "
                    "Supported: .yaml, .yml, .json"
                )
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            if _YAML_AVAILABLE:
                import yaml
                if isinstance(e, yaml.YAMLError):
                    raise ConfigurationError(f"Invalid YAML in config file: {e}")
            raise ConfigurationError(f"Error loading config file: {e}")
        
        return self.config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'logging.level')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def merge(self, overrides: Dict[str, Any]):
        """Merge override values into configuration.
        
        Args:
            overrides: Dictionary of override values
        """
        self._deep_merge(self.config, overrides)
    
    def _deep_merge(self, base: Dict, override: Dict):
        """Deep merge two dictionaries.
        
        Args:
            base: Base dictionary (modified in place)
            override: Override dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration.
        
        Returns:
            Complete configuration dictionary
        """
        return self.config.copy()
    
    def validate(self, schema: Optional[Dict[str, Any]] = None) -> bool:
        """Validate configuration against schema.
        
        Args:
            schema: Optional schema dictionary for validation
            
        Returns:
            True if valid
            
        Raises:
            ConfigurationError: If validation fails
        """
        if schema is None:
            return True
        
        # Basic validation - check required keys
        required_keys = schema.get('required', [])
        for key in required_keys:
            if self.get(key) is None:
                raise ConfigurationError(f"Required configuration key missing: {key}")
        
        return True


def load_config(config_path: Optional[str] = None) -> ConfigManager:
    """Load configuration from file.
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        ConfigManager instance
    """
    return ConfigManager(config_path)


# Federated tree configuration defaults
FEDERATED_CONFIG = {
    'mongodb_uri': 'mongodb://localhost:27017/',
    'redis_uri': 'redis://localhost:6379/',
    'neo4j_uri': 'bolt://localhost:7687',
    'change_threshold': 0.15,
    'conflict_threshold': 0.3,
    'merge_confidence_cap': [0.1, 0.7],
    'tree_collection': 'compression_trees'
}

# Federated API configuration defaults
FEDERATED_API_CONFIG = {
    'base_url': os.getenv('FEDERATED_API_URL', 'https://model-opt-api-production-06d6.up.railway.app'),
    'api_key': os.getenv('FEDERATED_API_KEY'),
    'timeout': float(os.getenv('FEDERATED_API_TIMEOUT', '30.0')),
    'retry_attempts': int(os.getenv('FEDERATED_API_RETRY_ATTEMPTS', '3')),
    'cache_ttl': int(os.getenv('FEDERATED_CACHE_TTL', '300')),
}

