"""Configuration manager for EDA Rule Engine"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """Manages project configuration"""
    
    def __init__(self, config_file: str = ".eda-config.yaml"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                return {}
        return {}
    
    def _save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def init_project(self, project_name: str, database_type: str):
        """Initialize a new project configuration"""
        self.config = {
            'project': {
                'name': project_name,
                'version': '1.0.0',
                'created_at': str(Path().cwd()),
                'default_database_type': database_type
            },
            'databases': {},
            'settings': {
                'max_workers': 4,
                'query_timeout': 300,
                'result_cache_ttl': 3600,
                'log_level': 'INFO'
            }
        }
        self._save_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save_config()
    
    def get_project_name(self) -> Optional[str]:
        """Get project name"""
        return self.get('project.name')
    
    def get_default_database_type(self) -> str:
        """Get default database type"""
        return self.get('project.default_database_type', 'postgresql')