"""
Database Service for Agent 3: Database Manager
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from src.models.database import db, DatabaseConnection, DataSchema

class DatabaseService:
    """Service for database operations and management"""
    
    def __init__(self):
        self.connection_pool = {}
    
    def get_schema_info(self, connection_id: str) -> Dict[str, Any]:
        """Get schema information for a database connection"""
        try:
            connection = DatabaseConnection.query.filter_by(connection_id=connection_id).first()
            if not connection:
                return {'error': 'Connection not found'}
            
            # Get cached schema info
            schemas = DataSchema.query.filter_by(connection_id=connection_id).all()
            
            if not schemas:
                # Refresh schema if not cached
                refresh_result = self.refresh_schema_info(connection_id)
                if not refresh_result.get('success'):
                    return refresh_result
                
                schemas = DataSchema.query.filter_by(connection_id=connection_id).all()
            
            return {
                'success': True,
                'schemas': [schema.to_dict() for schema in schemas],
                'total_tables': len(schemas),
                'last_updated': max([schema.updated_at for schema in schemas]).isoformat() if schemas else None
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def refresh_schema_info(self, connection_id: str) -> Dict[str, Any]:
        """Refresh schema information for a database connection"""
        try:
            connection = DatabaseConnection.query.filter_by(connection_id=connection_id).first()
            if not connection:
                return {'success': False, 'error': 'Connection not found'}
            
            # For now, we'll implement SQLite schema detection
            # In a full implementation, this would support multiple database types
            if connection.db_type == 'sqlite':
                return self._refresh_sqlite_schema(connection)
            else:
                return {'success': False, 'error': f'Schema refresh not implemented for {connection.db_type}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _refresh_sqlite_schema(self, connection: DatabaseConnection) -> Dict[str, Any]:
        """Refresh schema for SQLite database"""
        try:
            # Connect to SQLite database
            db_path = connection.source_path or connection.connection_string.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get table list
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            schemas_updated = 0
            
            for (table_name,) in tables:
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                # Get record count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                record_count = cursor.fetchone()[0]
                
                # Build schema definition
                schema_definition = {
                    'columns': [
                        {
                            'name': col[1],
                            'type': col[2],
                            'not_null': bool(col[3]),
                            'default_value': col[4],
                            'primary_key': bool(col[5])
                        }
                        for col in columns
                    ],
                    'table_type': 'table',
                    'engine': 'sqlite'
                }
                
                # Update or create schema record
                existing_schema = DataSchema.query.filter_by(
                    connection_id=connection.connection_id,
                    table_name=table_name
                ).first()
                
                if existing_schema:
                    existing_schema.schema_definition = schema_definition
                    existing_schema.record_count = record_count
                    existing_schema.last_analyzed = datetime.utcnow()
                    existing_schema.updated_at = datetime.utcnow()
                else:
                    new_schema = DataSchema(
                        schema_id=f"{connection.connection_id}_{table_name}",
                        connection_id=connection.connection_id,
                        table_name=table_name,
                        schema_definition=schema_definition,
                        record_count=record_count,
                        last_analyzed=datetime.utcnow()
                    )
                    db.session.add(new_schema)
                
                schemas_updated += 1
            
            conn.close()
            db.session.commit()
            
            return {
                'success': True,
                'schemas_updated': schemas_updated,
                'total_tables': len(tables)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def execute_query(self, connection_id: str, query: str, limit: int = 100) -> Dict[str, Any]:
        """Execute a query on the database"""
        try:
            connection = DatabaseConnection.query.filter_by(connection_id=connection_id).first()
            if not connection:
                return {'success': False, 'error': 'Connection not found'}
            
            # For now, we'll implement SQLite query execution
            if connection.db_type == 'sqlite':
                return self._execute_sqlite_query(connection, query, limit)
            else:
                return {'success': False, 'error': f'Query execution not implemented for {connection.db_type}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _execute_sqlite_query(self, connection: DatabaseConnection, query: str, limit: int) -> Dict[str, Any]:
        """Execute query on SQLite database"""
        try:
            # Basic query validation
            query = query.strip()
            if not query:
                return {'success': False, 'error': 'Empty query'}
            
            # Prevent dangerous operations
            dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
            query_upper = query.upper()
            
            for keyword in dangerous_keywords:
                if keyword in query_upper and not query_upper.startswith('SELECT'):
                    return {'success': False, 'error': f'Dangerous operation {keyword} not allowed'}
            
            # Connect to database
            db_path = connection.source_path or connection.connection_string.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            # Add LIMIT if not present and it's a SELECT query
            if query_upper.startswith('SELECT') and 'LIMIT' not in query_upper:
                query += f' LIMIT {limit}'
            
            # Execute query
            start_time = datetime.utcnow()
            cursor.execute(query)
            results = cursor.fetchall()
            end_time = datetime.utcnow()
            
            # Convert results to list of dictionaries
            data = [dict(row) for row in results]
            
            # Get column information
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            conn.close()
            
            execution_time = (end_time - start_time).total_seconds()
            
            return {
                'success': True,
                'data': data,
                'columns': columns,
                'row_count': len(data),
                'execution_time_seconds': execution_time,
                'query': query
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_tables(self, connection_id: str) -> Dict[str, Any]:
        """List tables in the database"""
        try:
            connection = DatabaseConnection.query.filter_by(connection_id=connection_id).first()
            if not connection:
                return {'success': False, 'error': 'Connection not found'}
            
            # Get tables from cached schema
            schemas = DataSchema.query.filter_by(connection_id=connection_id).all()
            
            if not schemas:
                # Refresh schema if not cached
                refresh_result = self.refresh_schema_info(connection_id)
                if not refresh_result.get('success'):
                    return refresh_result
                
                schemas = DataSchema.query.filter_by(connection_id=connection_id).all()
            
            tables = [
                {
                    'table_name': schema.table_name,
                    'record_count': schema.record_count,
                    'last_analyzed': schema.last_analyzed.isoformat() if schema.last_analyzed else None,
                    'column_count': len(schema.schema_definition.get('columns', [])) if schema.schema_definition else 0
                }
                for schema in schemas
            ]
            
            return {
                'success': True,
                'tables': tables,
                'total_tables': len(tables)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_table_info(self, connection_id: str, table_name: str) -> Dict[str, Any]:
        """Get detailed information about a table"""
        try:
            schema = DataSchema.query.filter_by(
                connection_id=connection_id,
                table_name=table_name
            ).first()
            
            if not schema:
                return {'success': False, 'error': 'Table not found'}
            
            return {
                'success': True,
                'table_info': schema.to_dict()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_table_data(self, connection_id: str, table_name: str, page: int = 1, 
                      per_page: int = 50, where_clause: str = None, 
                      order_by: str = None) -> Dict[str, Any]:
        """Get data from a table with pagination"""
        try:
            # Build query
            query = f"SELECT * FROM {table_name}"
            
            if where_clause:
                query += f" WHERE {where_clause}"
            
            if order_by:
                query += f" ORDER BY {order_by}"
            
            # Add pagination
            offset = (page - 1) * per_page
            query += f" LIMIT {per_page} OFFSET {offset}"
            
            # Execute query
            result = self.execute_query(connection_id, query, per_page)
            
            if not result.get('success'):
                return result
            
            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM {table_name}"
            if where_clause:
                count_query += f" WHERE {where_clause}"
            
            count_result = self.execute_query(connection_id, count_query, 1)
            total_records = count_result['data'][0]['total'] if count_result.get('success') else 0
            
            return {
                'success': True,
                'data': result['data'],
                'columns': result['columns'],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_records': total_records,
                    'total_pages': (total_records + per_page - 1) // per_page
                },
                'query_info': {
                    'execution_time_seconds': result.get('execution_time_seconds'),
                    'query': result.get('query')
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def analyze_table_performance(self, connection_id: str, table_name: str) -> Dict[str, Any]:
        """Analyze table performance and provide recommendations"""
        try:
            connection = DatabaseConnection.query.filter_by(connection_id=connection_id).first()
            if not connection:
                return {'success': False, 'error': 'Connection not found'}
            
            schema = DataSchema.query.filter_by(
                connection_id=connection_id,
                table_name=table_name
            ).first()
            
            if not schema:
                return {'success': False, 'error': 'Table not found'}
            
            # Basic performance analysis
            analysis = {
                'table_name': table_name,
                'record_count': schema.record_count,
                'column_count': len(schema.schema_definition.get('columns', [])),
                'estimated_size_mb': (schema.record_count * len(schema.schema_definition.get('columns', [])) * 50) / (1024 * 1024),  # Rough estimate
                'recommendations': []
            }
            
            # Add recommendations based on analysis
            if schema.record_count > 100000:
                analysis['recommendations'].append({
                    'type': 'performance',
                    'message': 'Large table detected. Consider indexing frequently queried columns.',
                    'priority': 'medium'
                })
            
            if len(schema.schema_definition.get('columns', [])) > 20:
                analysis['recommendations'].append({
                    'type': 'design',
                    'message': 'Table has many columns. Consider normalization.',
                    'priority': 'low'
                })
            
            return {
                'success': True,
                'analysis': analysis
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_database_statistics(self, connection_id: str) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            connection = DatabaseConnection.query.filter_by(connection_id=connection_id).first()
            if not connection:
                return {'success': False, 'error': 'Connection not found'}
            
            schemas = DataSchema.query.filter_by(connection_id=connection_id).all()
            
            if not schemas:
                return {'success': False, 'error': 'No schema information available. Please refresh schema first.'}
            
            # Calculate statistics
            total_tables = len(schemas)
            total_records = sum([schema.record_count or 0 for schema in schemas])
            total_columns = sum([len(schema.schema_definition.get('columns', [])) for schema in schemas])
            
            # Table size distribution
            table_sizes = [
                {
                    'table_name': schema.table_name,
                    'record_count': schema.record_count or 0
                }
                for schema in schemas
            ]
            table_sizes.sort(key=lambda x: x['record_count'], reverse=True)
            
            return {
                'success': True,
                'statistics': {
                    'total_tables': total_tables,
                    'total_records': total_records,
                    'total_columns': total_columns,
                    'average_records_per_table': total_records / total_tables if total_tables > 0 else 0,
                    'average_columns_per_table': total_columns / total_tables if total_tables > 0 else 0,
                    'largest_tables': table_sizes[:10],
                    'last_analyzed': max([schema.last_analyzed for schema in schemas if schema.last_analyzed]).isoformat() if schemas else None
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

