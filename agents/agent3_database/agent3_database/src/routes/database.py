"""
Database routes for Agent 3: Database Manager
"""

import uuid
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from src.models.database import db, DatabaseConnection, DataSchema
from src.services.database_service import DatabaseService
from src.services.connection_manager import ConnectionManager

database_bp = Blueprint('database', __name__)

# Initialize services
database_service = DatabaseService()
connection_manager = ConnectionManager()

@database_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'agent': 'agent3_database',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@database_bp.route('/connections', methods=['POST'])
def create_connection():
    """Create a new database connection"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'db_type' not in data:
            return jsonify({'error': 'Name and db_type are required'}), 400
        
        # Create database connection
        connection = DatabaseConnection(
            connection_id=str(uuid.uuid4()),
            name=data['name'],
            description=data.get('description', ''),
            db_type=data['db_type'],
            host=data.get('host'),
            port=data.get('port'),
            database_name=data.get('database_name'),
            username=data.get('username'),
            config=data.get('config', {})
        )
        
        # Encrypt password if provided
        if 'password' in data:
            connection.password_encrypted = connection_manager.encrypt_password(data['password'])
        
        # Build connection string
        connection.connection_string = connection_manager.build_connection_string(connection, data.get('password'))
        
        db.session.add(connection)
        db.session.commit()
        
        # Test connection
        test_result = connection_manager.test_connection(connection.connection_id)
        
        return jsonify({
            'connection_id': connection.connection_id,
            'message': 'Database connection created successfully',
            'test_result': test_result,
            'connection': connection.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@database_bp.route('/connections', methods=['GET'])
def list_connections():
    """List all database connections"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        db_type = request.args.get('db_type')
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        query = DatabaseConnection.query
        
        if db_type:
            query = query.filter_by(db_type=db_type)
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        connections = query.order_by(DatabaseConnection.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'connections': [conn.to_dict() for conn in connections.items],
            'total': connections.total,
            'pages': connections.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@database_bp.route('/connections/<connection_id>', methods=['GET'])
def get_connection(connection_id):
    """Get database connection details"""
    try:
        connection = DatabaseConnection.query.filter_by(connection_id=connection_id).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Get associated schemas
        schemas = DataSchema.query.filter_by(connection_id=connection_id).all()
        
        response = connection.to_dict()
        response['schemas'] = [schema.to_dict() for schema in schemas]
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@database_bp.route('/connections/<connection_id>', methods=['PUT'])
def update_connection(connection_id):
    """Update database connection"""
    try:
        connection = DatabaseConnection.query.filter_by(connection_id=connection_id).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        data = request.get_json() or {}
        
        # Update allowed fields
        if 'name' in data:
            connection.name = data['name']
        if 'description' in data:
            connection.description = data['description']
        if 'host' in data:
            connection.host = data['host']
        if 'port' in data:
            connection.port = data['port']
        if 'database_name' in data:
            connection.database_name = data['database_name']
        if 'username' in data:
            connection.username = data['username']
        if 'config' in data:
            connection.config = data['config']
        if 'is_active' in data:
            connection.is_active = data['is_active']
        
        # Update password if provided
        if 'password' in data:
            connection.password_encrypted = connection_manager.encrypt_password(data['password'])
            connection.connection_string = connection_manager.build_connection_string(connection, data['password'])
        
        connection.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Connection updated successfully',
            'connection': connection.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@database_bp.route('/connections/<connection_id>', methods=['DELETE'])
def delete_connection(connection_id):
    """Delete database connection"""
    try:
        connection = DatabaseConnection.query.filter_by(connection_id=connection_id).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Delete associated data (cascade should handle this)
        db.session.delete(connection)
        db.session.commit()
        
        return jsonify({'message': 'Connection deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@database_bp.route('/connections/<connection_id>/test', methods=['POST'])
def test_connection(connection_id):
    """Test database connection"""
    try:
        connection = DatabaseConnection.query.filter_by(connection_id=connection_id).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Test connection
        result = connection_manager.test_connection(connection_id)
        
        # Update connection test status
        connection.last_tested = datetime.utcnow()
        connection.test_status = 'success' if result['success'] else 'failed'
        connection.test_message = result.get('message', '')
        
        db.session.commit()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@database_bp.route('/connections/<connection_id>/schema', methods=['GET'])
def get_connection_schema(connection_id):
    """Get database schema information"""
    try:
        connection = DatabaseConnection.query.filter_by(connection_id=connection_id).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Get schema information
        schema_info = database_service.get_schema_info(connection_id)
        
        return jsonify(schema_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@database_bp.route('/connections/<connection_id>/schema/refresh', methods=['POST'])
def refresh_connection_schema(connection_id):
    """Refresh database schema information"""
    try:
        connection = DatabaseConnection.query.filter_by(connection_id=connection_id).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Refresh schema information
        result = database_service.refresh_schema_info(connection_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@database_bp.route('/connections/<connection_id>/query', methods=['POST'])
def execute_query(connection_id):
    """Execute a query on the database"""
    try:
        connection = DatabaseConnection.query.filter_by(connection_id=connection_id).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query']
        limit = data.get('limit', 100)
        
        # Execute query
        result = database_service.execute_query(connection_id, query, limit)
        
        # Update connection usage
        connection.connection_count += 1
        connection.last_used = datetime.utcnow()
        db.session.commit()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@database_bp.route('/connections/<connection_id>/tables', methods=['GET'])
def list_tables(connection_id):
    """List tables in the database"""
    try:
        connection = DatabaseConnection.query.filter_by(connection_id=connection_id).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Get table list
        result = database_service.list_tables(connection_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@database_bp.route('/connections/<connection_id>/tables/<table_name>', methods=['GET'])
def get_table_info(connection_id, table_name):
    """Get detailed information about a table"""
    try:
        connection = DatabaseConnection.query.filter_by(connection_id=connection_id).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Get table information
        result = database_service.get_table_info(connection_id, table_name)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@database_bp.route('/connections/<connection_id>/tables/<table_name>/data', methods=['GET'])
def get_table_data(connection_id, table_name):
    """Get data from a table"""
    try:
        connection = DatabaseConnection.query.filter_by(connection_id=connection_id).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        where_clause = request.args.get('where')
        order_by = request.args.get('order_by')
        
        # Get table data
        result = database_service.get_table_data(
            connection_id, table_name, page, per_page, where_clause, order_by
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@database_bp.route('/stats', methods=['GET'])
def get_database_stats():
    """Get database management statistics"""
    try:
        # Overall statistics
        total_connections = DatabaseConnection.query.count()
        active_connections = DatabaseConnection.query.filter_by(is_active=True).count()
        
        # Connection type distribution
        from sqlalchemy import func
        type_stats = db.session.query(
            DatabaseConnection.db_type,
            func.count(DatabaseConnection.id).label('count')
        ).group_by(DatabaseConnection.db_type).all()
        
        # Recent activity
        recent_connections = DatabaseConnection.query.order_by(
            DatabaseConnection.last_used.desc().nullslast()
        ).limit(10).all()
        
        return jsonify({
            'connections': {
                'total': total_connections,
                'active': active_connections
            },
            'database_types': [
                {'type': db_type, 'count': count} for db_type, count in type_stats
            ],
            'recent_activity': [conn.to_dict() for conn in recent_connections]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@database_bp.route('/export', methods=['GET'])
def export_connections():
    """Export all database connections (without passwords)"""
    try:
        connections = DatabaseConnection.query.all()
        
        export_data = {
            'connections': [],
            'exported_at': datetime.utcnow().isoformat(),
            'total_connections': len(connections)
        }
        
        for conn in connections:
            conn_data = conn.to_dict()
            # Remove sensitive information
            conn_data.pop('password_encrypted', None)
            conn_data.pop('connection_string', None)
            export_data['connections'].append(conn_data)
        
        return jsonify(export_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@database_bp.route('/import', methods=['POST'])
def import_connections():
    """Import database connections"""
    try:
        data = request.get_json()
        
        if not data or 'connections' not in data:
            return jsonify({'error': 'Connections data is required'}), 400
        
        imported_count = 0
        errors = []
        
        for conn_data in data['connections']:
            try:
                # Check if connection already exists
                existing_conn = DatabaseConnection.query.filter_by(
                    connection_id=conn_data.get('connection_id')
                ).first()
                
                if existing_conn:
                    continue  # Skip existing connections
                
                # Create new connection
                connection = DatabaseConnection(
                    connection_id=conn_data.get('connection_id', str(uuid.uuid4())),
                    name=conn_data['name'],
                    description=conn_data.get('description', ''),
                    db_type=conn_data['db_type'],
                    host=conn_data.get('host'),
                    port=conn_data.get('port'),
                    database_name=conn_data.get('database_name'),
                    username=conn_data.get('username'),
                    config=conn_data.get('config', {}),
                    is_active=conn_data.get('is_active', True)
                )
                
                db.session.add(connection)
                imported_count += 1
                
            except Exception as e:
                errors.append({
                    'connection_name': conn_data.get('name', 'Unknown'),
                    'error': str(e)
                })
        
        db.session.commit()
        
        return jsonify({
            'message': f'Imported {imported_count} connections',
            'imported_count': imported_count,
            'errors': errors
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

