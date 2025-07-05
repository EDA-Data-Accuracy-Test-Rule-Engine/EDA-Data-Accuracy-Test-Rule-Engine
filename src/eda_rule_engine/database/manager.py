"""Database connection manager for EDA Rule Engine"""

import yaml
import os
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and configurations"""
    
    def __init__(self, config_file: str = ".eda-config.yaml"):
        self.config_file = config_file
        self.connections: Dict[str, Dict] = {}
        self._engines: Dict[str, Engine] = {}
        self._load_config()
    
    def _load_config(self):
        """Load database configurations from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = yaml.safe_load(f) or {}
                    self.connections = config.get('databases', {})
            except Exception as e:
                logger.warning(f"Could not load config file: {e}")
                self.connections = {}
        else:
            self.connections = {}
    
    def _save_config(self):
        """Save current configurations to file"""
        config = {'databases': self.connections}
        
        # Load existing config to preserve other settings
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    existing_config = yaml.safe_load(f) or {}
                    existing_config.update(config)
                    config = existing_config
            except Exception:
                pass
        
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    
    def add_connection(
        self, 
        name: str, 
        db_type: str, 
        host: str, 
        port: int, 
        database: str, 
        username: Optional[str] = None, 
        password: Optional[str] = None
    ):
        """Add a new database connection"""
        
        # Validate database type
        supported_types = ['postgresql', 'mysql', 'sqlite']
        if db_type not in supported_types:
            raise ValueError(f"Unsupported database type: {db_type}. Supported: {supported_types}")
        
        connection_config = {
            'type': db_type,
            'host': host,
            'port': port,
            'database': database,
            'username': username,
            'password': password  # Note: In production, use secure storage
        }
        
        self.connections[name] = connection_config
        self._save_config()
        
        # Clear cached engine if exists
        if name in self._engines:
            self._engines[name].dispose()
            del self._engines[name]
    
    def remove_connection(self, name: str):
        """Remove a database connection"""
        if name in self.connections:
            del self.connections[name]
            self._save_config()
            
            if name in self._engines:
                self._engines[name].dispose()
                del self._engines[name]
        else:
            raise ValueError(f"Connection '{name}' not found")
    
    def list_connections(self) -> List[Dict]:
        """List all configured connections"""
        return [
            {
                'name': name,
                'type': config['type'],
                'host': config['host'],
                'database': config['database']
            }
            for name, config in self.connections.items()
        ]
    
    def get_engine(self, name: str) -> Engine:
        """Get SQLAlchemy engine for a connection"""
        if name not in self.connections:
            raise ValueError(f"Connection '{name}' not found")
        
        if name not in self._engines:
            self._engines[name] = self._create_engine(self.connections[name])
        
        return self._engines[name]
    
    def _create_engine(self, config: Dict) -> Engine:
        """Create SQLAlchemy engine from config"""
        db_type = config['type']
        
        if db_type == 'postgresql':
            url = f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        elif db_type == 'mysql':
            url = f"mysql+pymysql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        elif db_type == 'sqlite':
            url = f"sqlite:///{config['database']}"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        return create_engine(url, pool_pre_ping=True)
    
    def test_connection(self, name: str) -> bool:
        """Test if a database connection is working"""
        try:
            engine = self.get_engine(name)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Connection test failed for '{name}': {e}")
            return False
    
    def execute_query(self, name: str, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a query and return results"""
        try:
            engine = self.get_engine(name)
            with engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                return [dict(row._mapping) for row in result.fetchall()]
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def get_table_info(self, name: str, table_name: str) -> Dict:
        """Get information about a table"""
        db_type = self.connections[name]['type']
        
        if db_type == 'postgresql':
            query = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """
        elif db_type == 'mysql':
            query = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """
        else:  # sqlite
            query = f"PRAGMA table_info({table_name})"
        
        try:
            columns = self.execute_query(name, query, {'table_name': table_name})
            return {
                'table_name': table_name,
                'columns': columns
            }
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {'table_name': table_name, 'columns': []}
    
    def close_all_connections(self):
        """Close all database connections"""
        for engine in self._engines.values():
            engine.dispose()
        self._engines.clear()