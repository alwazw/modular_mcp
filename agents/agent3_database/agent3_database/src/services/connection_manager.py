"""
Connection Manager Service for Agent 3: Database Manager
"""

import os
import sqlite3
import base64
from datetime import datetime
from typing import Dict, Any, Optional, List
try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None
from src.models.database import db, DatabaseConnection

class ConnectionManager:
    """Service for managing database connections"""
    
    def __init__(self):
        # Initialize encryption key (in production, this should be from environment)
        self.encryption_key = self._get_or_create_encryption_key()
        if Fernet is not None:
            self.cipher_suite = Fernet(self.encryption_key)
        else:
            self.cipher_suite = None
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for password encryption"""
        key_env = os.getenv('DB_ENCRYPTION_KEY')
        if key_env:
            return key_env.encode()
        else:
            # Generate a new key (in production, this should be stored securely)
            if Fernet is None:
                return b'dummy_key_for_development_only_not_secure'
            return Fernet.generate_key()
    
    def encrypt_password(self, password: str) -> str:
        """Encrypt a password"""
        try:
            if not password:
                return ""
            
            encrypted_password = self.cipher_suite.encrypt(password.encode())
            return base64.b64encode(encrypted_password).decode()
            
        except Exception as e:
            print(f"Error encrypting password: {e}")
            return ""
    
    def decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt a password"""
        try:
            if not encrypted_password:
                return ""
            
            encrypted_bytes = base64.b64decode(encrypted_password.encode())
            decrypted_password = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_password.decode()
            
        except Exception as e:
            print(f"Error decrypting password: {e}")
            return ""
    
    def build_connection_string(self, connection: DatabaseConnection, password: str = None) -> str:
        """Build connection string for database"""
        try:
            if connection.db_type == 'sqlite':
                # SQLite connection string
                if connection.database_name:
                    return f"sqlite:///{connection.database_name}"
                elif connection.host:
                    return f"sqlite:///{connection.host}"
                else:
                    return "sqlite:///default.db"
            
            elif connection.db_type == 'postgresql':
                # PostgreSQL connection string
                password_part = f":{password}" if password else ""
                port_part = f":{connection.port}" if connection.port else ":5432"
                return f"postgresql://{connection.username}{password_part}@{connection.host}{port_part}/{connection.database_name}"
            
            elif connection.db_type == 'mysql':
                # MySQL connection string
                password_part = f":{password}" if password else ""
                port_part = f":{connection.port}" if connection.port else ":3306"
                return f"mysql://{connection.username}{password_part}@{connection.host}{port_part}/{connection.database_name}"
            
            elif connection.db_type == 'mongodb':
                # MongoDB connection string
                password_part = f":{password}" if password else ""
                port_part = f":{connection.port}" if connection.port else ":27017"
                return f"mongodb://{connection.username}{password_part}@{connection.host}{port_part}/{connection.database_name}"
            
            else:
                return ""
                
        except Exception as e:
            print(f"Error building connection string: {e}")
            return ""
    
    def test_connection(self, connection_id: str) -> Dict[str, Any]:
        """Test database connection"""
        try:
            connection = DatabaseConnection.query.filter_by(connection_id=connection_id).first()
            if not connection:
                return {'success': False, 'message': 'Connection not found'}
            
            # Test based on database type
            if connection.db_type == 'sqlite':
                return self._test_sqlite_connection(connection)
            elif connection.db_type == 'postgresql':
                return self._test_postgresql_connection(connection)
            elif connection.db_type == 'mysql':
                return self._test_mysql_connection(connection)
            elif connection.db_type == 'mongodb':
                return self._test_mongodb_connection(connection)
            else:
                return {'success': False, 'message': f'Unsupported database type: {connection.db_type}'}
                
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _test_sqlite_connection(self, connection: DatabaseConnection) -> Dict[str, Any]:
        """Test SQLite connection"""
        try:
            # For SQLite, we'll use the database_name as the file path
            db_path = connection.database_name or 'test.db'
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
            
            # Test connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Test query
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            # Get database info
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'success': True,
                'message': 'Connection successful',
                'database_info': {
                    'database_path': db_path,
                    'table_count': table_count,
                    'database_size_bytes': os.path.getsize(db_path) if os.path.exists(db_path) else 0
                }
            }
            
        except Exception as e:
            return {'success': False, 'message': f'SQLite connection failed: {str(e)}'}
    
    def _test_postgresql_connection(self, connection: DatabaseConnection) -> Dict[str, Any]:
        """Test PostgreSQL connection"""
        try:
            # This would require psycopg2 or similar library
            # For now, return a placeholder
            return {
                'success': False,
                'message': 'PostgreSQL testing not implemented yet. Install psycopg2 library.'
            }
            
        except Exception as e:
            return {'success': False, 'message': f'PostgreSQL connection failed: {str(e)}'}
    
    def _test_mysql_connection(self, connection: DatabaseConnection) -> Dict[str, Any]:
        """Test MySQL connection"""
        try:
            # This would require mysql-connector-python or similar library
            # For now, return a placeholder
            return {
                'success': False,
                'message': 'MySQL testing not implemented yet. Install mysql-connector-python library.'
            }
            
        except Exception as e:
            return {'success': False, 'message': f'MySQL connection failed: {str(e)}'}
    
    def _test_mongodb_connection(self, connection: DatabaseConnection) -> Dict[str, Any]:
        """Test MongoDB connection"""
        try:
            # This would require pymongo library
            # For now, return a placeholder
            return {
                'success': False,
                'message': 'MongoDB testing not implemented yet. Install pymongo library.'
            }
            
        except Exception as e:
            return {'success': False, 'message': f'MongoDB connection failed: {str(e)}'}
    
    def get_connection_pool_status(self) -> Dict[str, Any]:
        """Get status of connection pool"""
        try:
            active_connections = DatabaseConnection.query.filter_by(is_active=True).all()
            
            pool_status = {
                'total_connections': len(active_connections),
                'connections_by_type': {},
                'recent_activity': []
            }
            
            # Group by database type
            for conn in active_connections:
                db_type = conn.db_type
                if db_type not in pool_status['connections_by_type']:
                    pool_status['connections_by_type'][db_type] = 0
                pool_status['connections_by_type'][db_type] += 1
                
                # Add recent activity
                if conn.last_used:
                    pool_status['recent_activity'].append({
                        'connection_id': conn.connection_id,
                        'name': conn.name,
                        'last_used': conn.last_used.isoformat(),
                        'connection_count': conn.connection_count
                    })
            
            # Sort recent activity by last used
            pool_status['recent_activity'].sort(
                key=lambda x: x['last_used'], reverse=True
            )
            pool_status['recent_activity'] = pool_status['recent_activity'][:10]
            
            return {
                'success': True,
                'pool_status': pool_status
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_connection_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate connection configuration"""
        try:
            errors = []
            warnings = []
            
            # Required fields
            required_fields = ['name', 'db_type']
            for field in required_fields:
                if field not in config or not config[field]:
                    errors.append(f"Field '{field}' is required")
            
            # Database type validation
            supported_types = ['sqlite', 'postgresql', 'mysql', 'mongodb']
            if config.get('db_type') not in supported_types:
                errors.append(f"Database type must be one of: {', '.join(supported_types)}")
            
            # Type-specific validation
            db_type = config.get('db_type')
            
            if db_type == 'sqlite':
                if not config.get('database_name'):
                    errors.append("Database name/path is required for SQLite")
            
            elif db_type in ['postgresql', 'mysql']:
                required_network_fields = ['host', 'database_name', 'username']
                for field in required_network_fields:
                    if not config.get(field):
                        errors.append(f"Field '{field}' is required for {db_type}")
                
                # Port validation
                if config.get('port'):
                    try:
                        port = int(config['port'])
                        if port < 1 or port > 65535:
                            errors.append("Port must be between 1 and 65535")
                    except ValueError:
                        errors.append("Port must be a valid integer")
            
            elif db_type == 'mongodb':
                if not config.get('host'):
                    errors.append("Host is required for MongoDB")
            
            # Security warnings
            if db_type != 'sqlite' and not config.get('password'):
                warnings.append("No password provided. Connection may fail if authentication is required.")
            
            if config.get('host') == 'localhost' and db_type != 'sqlite':
                warnings.append("Using localhost. Ensure the database server is running locally.")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': []
            }
    
    def get_connection_templates(self) -> List[Dict[str, Any]]:
        """Get connection templates for common database setups"""
        templates = [
            {
                'name': 'Local SQLite Database',
                'description': 'Simple local SQLite database file',
                'db_type': 'sqlite',
                'template': {
                    'db_type': 'sqlite',
                    'database_name': 'data/app.db',
                    'config': {
                        'timeout': 30,
                        'check_same_thread': False
                    }
                }
            },
            {
                'name': 'Local PostgreSQL',
                'description': 'Local PostgreSQL database connection',
                'db_type': 'postgresql',
                'template': {
                    'db_type': 'postgresql',
                    'host': 'localhost',
                    'port': 5432,
                    'database_name': 'myapp',
                    'username': 'postgres',
                    'config': {
                        'sslmode': 'prefer',
                        'connect_timeout': 10
                    }
                }
            },
            {
                'name': 'Local MySQL',
                'description': 'Local MySQL database connection',
                'db_type': 'mysql',
                'template': {
                    'db_type': 'mysql',
                    'host': 'localhost',
                    'port': 3306,
                    'database_name': 'myapp',
                    'username': 'root',
                    'config': {
                        'charset': 'utf8mb4',
                        'connect_timeout': 10
                    }
                }
            },
            {
                'name': 'Local MongoDB',
                'description': 'Local MongoDB database connection',
                'db_type': 'mongodb',
                'template': {
                    'db_type': 'mongodb',
                    'host': 'localhost',
                    'port': 27017,
                    'database_name': 'myapp',
                    'config': {
                        'serverSelectionTimeoutMS': 5000,
                        'connectTimeoutMS': 10000
                    }
                }
            }
        ]
        
        return templates
    
    def clone_connection(self, source_connection_id: str, new_name: str) -> Dict[str, Any]:
        """Clone an existing connection with a new name"""
        try:
            source_connection = DatabaseConnection.query.filter_by(connection_id=source_connection_id).first()
            if not source_connection:
                return {'success': False, 'error': 'Source connection not found'}
            
            # Create new connection
            import uuid
            new_connection = DatabaseConnection(
                connection_id=str(uuid.uuid4()),
                name=new_name,
                description=f"Cloned from {source_connection.name}",
                db_type=source_connection.db_type,
                host=source_connection.host,
                port=source_connection.port,
                database_name=source_connection.database_name,
                username=source_connection.username,
                config=source_connection.config.copy() if source_connection.config else {}
            )
            
            # Note: Password is not cloned for security reasons
            
            db.session.add(new_connection)
            db.session.commit()
            
            return {
                'success': True,
                'connection_id': new_connection.connection_id,
                'message': 'Connection cloned successfully. Please set the password.',
                'connection': new_connection.to_dict()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

