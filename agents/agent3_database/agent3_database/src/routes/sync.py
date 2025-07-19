"""
Sync routes for Agent 3: Database Manager
"""

import uuid
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from src.models.database import db, DatabaseConnection, SyncOperation, SyncRun
from src.services.sync_service import SyncService

sync_bp = Blueprint('sync', __name__)

# Initialize sync service
sync_service = SyncService()

@sync_bp.route('/operations', methods=['POST'])
def create_sync_operation():
    """Create a new sync operation"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'source_connection_id' not in data:
            return jsonify({'error': 'Name and source_connection_id are required'}), 400
        
        # Check if source connection exists
        source_connection = DatabaseConnection.query.filter_by(connection_id=data['source_connection_id']).first()
        if not source_connection:
            return jsonify({'error': 'Source database connection not found'}), 404
        
        # Check target connection if provided
        if 'target_connection_id' in data and data['target_connection_id']:
            target_connection = DatabaseConnection.query.filter_by(connection_id=data['target_connection_id']).first()
            if not target_connection:
                return jsonify({'error': 'Target database connection not found'}), 404
        
        # Create sync operation
        sync_operation = SyncOperation(
            sync_id=str(uuid.uuid4()),
            name=data['name'],
            description=data.get('description', ''),
            source_connection_id=data['source_connection_id'],
            target_connection_id=data.get('target_connection_id'),
            sync_type=data.get('sync_type', 'full'),
            sync_mode=data.get('sync_mode', 'push'),
            source_query=data.get('source_query'),
            target_table=data.get('target_table'),
            field_mapping=data.get('field_mapping', {}),
            schedule_type=data.get('schedule_type', 'manual'),
            schedule_config=data.get('schedule_config', {}),
            conflict_resolution=data.get('conflict_resolution', 'source_wins')
        )
        
        # Calculate next sync if scheduled
        if sync_operation.schedule_type != 'manual':
            sync_operation.next_sync = sync_service.calculate_next_sync(sync_operation)
        
        db.session.add(sync_operation)
        db.session.commit()
        
        return jsonify({
            'sync_id': sync_operation.sync_id,
            'message': 'Sync operation created successfully',
            'sync_operation': sync_operation.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/operations', methods=['GET'])
def list_sync_operations():
    """List all sync operations"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        source_connection_id = request.args.get('source_connection_id')
        target_connection_id = request.args.get('target_connection_id')
        status = request.args.get('status')
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        query = SyncOperation.query
        
        if source_connection_id:
            query = query.filter_by(source_connection_id=source_connection_id)
        
        if target_connection_id:
            query = query.filter_by(target_connection_id=target_connection_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        operations = query.order_by(SyncOperation.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'sync_operations': [op.to_dict() for op in operations.items],
            'total': operations.total,
            'pages': operations.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/operations/<sync_id>', methods=['GET'])
def get_sync_operation(sync_id):
    """Get sync operation details"""
    try:
        sync_operation = SyncOperation.query.filter_by(sync_id=sync_id).first()
        
        if not sync_operation:
            return jsonify({'error': 'Sync operation not found'}), 404
        
        # Get recent sync runs
        recent_runs = SyncRun.query.filter_by(sync_id=sync_id).order_by(
            SyncRun.created_at.desc()
        ).limit(10).all()
        
        response = sync_operation.to_dict()
        response['recent_runs'] = [run.to_dict() for run in recent_runs]
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/operations/<sync_id>', methods=['PUT'])
def update_sync_operation(sync_id):
    """Update sync operation"""
    try:
        sync_operation = SyncOperation.query.filter_by(sync_id=sync_id).first()
        
        if not sync_operation:
            return jsonify({'error': 'Sync operation not found'}), 404
        
        data = request.get_json() or {}
        
        # Update allowed fields
        if 'name' in data:
            sync_operation.name = data['name']
        if 'description' in data:
            sync_operation.description = data['description']
        if 'target_connection_id' in data:
            sync_operation.target_connection_id = data['target_connection_id']
        if 'sync_type' in data:
            sync_operation.sync_type = data['sync_type']
        if 'sync_mode' in data:
            sync_operation.sync_mode = data['sync_mode']
        if 'source_query' in data:
            sync_operation.source_query = data['source_query']
        if 'target_table' in data:
            sync_operation.target_table = data['target_table']
        if 'field_mapping' in data:
            sync_operation.field_mapping = data['field_mapping']
        if 'schedule_type' in data:
            sync_operation.schedule_type = data['schedule_type']
        if 'schedule_config' in data:
            sync_operation.schedule_config = data['schedule_config']
        if 'conflict_resolution' in data:
            sync_operation.conflict_resolution = data['conflict_resolution']
        if 'is_active' in data:
            sync_operation.is_active = data['is_active']
        
        # Recalculate next sync if schedule changed
        if 'schedule_type' in data or 'schedule_config' in data:
            if sync_operation.schedule_type != 'manual':
                sync_operation.next_sync = sync_service.calculate_next_sync(sync_operation)
            else:
                sync_operation.next_sync = None
        
        sync_operation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Sync operation updated successfully',
            'sync_operation': sync_operation.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/operations/<sync_id>', methods=['DELETE'])
def delete_sync_operation(sync_id):
    """Delete sync operation"""
    try:
        sync_operation = SyncOperation.query.filter_by(sync_id=sync_id).first()
        
        if not sync_operation:
            return jsonify({'error': 'Sync operation not found'}), 404
        
        # Delete associated sync runs (cascade should handle this)
        db.session.delete(sync_operation)
        db.session.commit()
        
        return jsonify({'message': 'Sync operation deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/operations/<sync_id>/run', methods=['POST'])
def run_sync_operation(sync_id):
    """Run a sync operation manually"""
    try:
        sync_operation = SyncOperation.query.filter_by(sync_id=sync_id).first()
        
        if not sync_operation:
            return jsonify({'error': 'Sync operation not found'}), 404
        
        if not sync_operation.is_active:
            return jsonify({'error': 'Sync operation is not active'}), 400
        
        # Start sync run
        run_id = sync_service.start_sync_run(sync_id, 'manual')
        
        return jsonify({
            'run_id': run_id,
            'message': 'Sync run started',
            'status': 'running'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/runs/<run_id>', methods=['GET'])
def get_sync_run(run_id):
    """Get sync run details"""
    try:
        sync_run = SyncRun.query.filter_by(run_id=run_id).first()
        
        if not sync_run:
            return jsonify({'error': 'Sync run not found'}), 404
        
        return jsonify(sync_run.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/runs', methods=['GET'])
def list_sync_runs():
    """List sync runs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        sync_id = request.args.get('sync_id')
        status = request.args.get('status')
        
        query = SyncRun.query
        
        if sync_id:
            query = query.filter_by(sync_id=sync_id)
        
        if status:
            query = query.filter_by(status=status)
        
        runs = query.order_by(SyncRun.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'sync_runs': [run.to_dict() for run in runs.items],
            'total': runs.total,
            'pages': runs.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/runs/<run_id>/cancel', methods=['POST'])
def cancel_sync_run(run_id):
    """Cancel a running sync"""
    try:
        sync_run = SyncRun.query.filter_by(run_id=run_id).first()
        
        if not sync_run:
            return jsonify({'error': 'Sync run not found'}), 404
        
        if sync_run.status != 'running':
            return jsonify({'error': 'Sync run is not running'}), 400
        
        # Cancel sync run
        result = sync_service.cancel_sync_run(run_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/schedule/check', methods=['POST'])
def check_scheduled_syncs():
    """Check and run scheduled syncs"""
    try:
        # Find operations that need to run
        current_time = datetime.utcnow()
        due_operations = SyncOperation.query.filter(
            SyncOperation.is_active == True,
            SyncOperation.schedule_type != 'manual',
            SyncOperation.next_sync <= current_time
        ).all()
        
        started_runs = []
        
        for operation in due_operations:
            try:
                run_id = sync_service.start_sync_run(operation.sync_id, 'scheduled')
                started_runs.append({
                    'sync_id': operation.sync_id,
                    'run_id': run_id,
                    'operation_name': operation.name
                })
                
                # Update next sync time
                operation.next_sync = sync_service.calculate_next_sync(operation)
                
            except Exception as e:
                print(f"Error starting scheduled sync for operation {operation.sync_id}: {e}")
        
        db.session.commit()
        
        return jsonify({
            'message': f'Started {len(started_runs)} scheduled syncs',
            'started_runs': started_runs
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/agents/sync', methods=['POST'])
def sync_with_agents():
    """Sync data with other agents in the MCP system"""
    try:
        data = request.get_json() or {}
        
        # Get agent configurations
        agent1_url = data.get('agent1_url', 'http://localhost:5000')
        agent2_url = data.get('agent2_url', 'http://localhost:5001')
        
        # Sync with Agent 1 (scraper data)
        agent1_result = sync_service.sync_with_agent1(agent1_url)
        
        # Sync with Agent 2 (knowledge base data)
        agent2_result = sync_service.sync_with_agent2(agent2_url)
        
        return jsonify({
            'message': 'Agent sync completed',
            'agent1_sync': agent1_result,
            'agent2_sync': agent2_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/agents/status', methods=['GET'])
def get_agent_sync_status():
    """Get sync status with other agents"""
    try:
        # Get recent sync operations with agents
        agent_syncs = SyncOperation.query.filter(
            SyncOperation.name.like('%agent%')
        ).order_by(SyncOperation.last_sync.desc()).limit(10).all()
        
        return jsonify({
            'agent_syncs': [sync.to_dict() for sync in agent_syncs]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/preview', methods=['POST'])
def preview_sync():
    """Preview what a sync operation would do without executing it"""
    try:
        data = request.get_json()
        
        if not data or 'sync_id' not in data:
            return jsonify({'error': 'Sync ID is required'}), 400
        
        sync_id = data['sync_id']
        limit = data.get('limit', 100)
        
        # Get preview of sync operation
        result = sync_service.preview_sync_operation(sync_id, limit)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/validate', methods=['POST'])
def validate_sync_config():
    """Validate sync operation configuration"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Configuration data is required'}), 400
        
        # Validate sync configuration
        result = sync_service.validate_sync_config(data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/stats', methods=['GET'])
def get_sync_stats():
    """Get sync statistics"""
    try:
        from datetime import timedelta
        
        # Overall statistics
        total_operations = SyncOperation.query.count()
        active_operations = SyncOperation.query.filter_by(is_active=True).count()
        
        # Recent runs statistics
        recent_runs = SyncRun.query.filter(
            SyncRun.created_at >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        successful_runs = len([r for r in recent_runs if r.status == 'completed'])
        failed_runs = len([r for r in recent_runs if r.status == 'failed'])
        
        # Data transfer statistics
        total_records_processed = sum([r.records_processed or 0 for r in recent_runs])
        total_records_synced = sum([
            (r.records_inserted or 0) + (r.records_updated or 0) 
            for r in recent_runs
        ])
        
        # Upcoming scheduled syncs
        upcoming_syncs = SyncOperation.query.filter(
            SyncOperation.is_active == True,
            SyncOperation.next_sync.isnot(None),
            SyncOperation.next_sync > datetime.utcnow()
        ).order_by(SyncOperation.next_sync).limit(10).all()
        
        return jsonify({
            'operations': {
                'total': total_operations,
                'active': active_operations
            },
            'recent_runs': {
                'total': len(recent_runs),
                'successful': successful_runs,
                'failed': failed_runs,
                'success_rate': round((successful_runs / len(recent_runs) * 100) if recent_runs else 0, 2)
            },
            'data_transfer': {
                'total_records_processed': total_records_processed,
                'total_records_synced': total_records_synced
            },
            'upcoming_syncs': [
                {
                    'sync_id': op.sync_id,
                    'operation_name': op.name,
                    'next_sync': op.next_sync.isoformat() if op.next_sync else None,
                    'sync_type': op.sync_type
                }
                for op in upcoming_syncs
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/templates', methods=['GET'])
def get_sync_templates():
    """Get sync operation templates for common scenarios"""
    try:
        templates = [
            {
                'name': 'Agent 1 to Agent 2 Sync',
                'description': 'Sync scraped content from Agent 1 to Agent 2 knowledge base',
                'template': {
                    'sync_type': 'incremental',
                    'sync_mode': 'push',
                    'source_query': 'SELECT * FROM scraped_content WHERE status = "completed"',
                    'field_mapping': {
                        'url': 'source_path',
                        'title': 'title',
                        'content': 'raw_content',
                        'cleaned_content': 'processed_content'
                    },
                    'schedule_type': 'daily',
                    'schedule_config': {'hour': 1, 'minute': 0},
                    'conflict_resolution': 'source_wins'
                }
            },
            {
                'name': 'Real-time Data Sync',
                'description': 'Real-time synchronization for live data updates',
                'template': {
                    'sync_type': 'incremental',
                    'sync_mode': 'bidirectional',
                    'schedule_type': 'realtime',
                    'schedule_config': {'trigger_on': 'insert,update,delete'},
                    'conflict_resolution': 'merge'
                }
            },
            {
                'name': 'Weekly Full Sync',
                'description': 'Complete data synchronization weekly',
                'template': {
                    'sync_type': 'full',
                    'sync_mode': 'push',
                    'schedule_type': 'weekly',
                    'schedule_config': {'day_of_week': 0, 'hour': 2, 'minute': 0},
                    'conflict_resolution': 'source_wins'
                }
            }
        ]
        
        return jsonify({'templates': templates})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

