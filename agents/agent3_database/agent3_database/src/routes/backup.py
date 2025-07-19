"""
Backup routes for Agent 3: Database Manager
"""

import uuid
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from src.models.database import db, DatabaseConnection, BackupJob, BackupRun
from src.services.backup_service import BackupService

backup_bp = Blueprint('backup', __name__)

# Initialize backup service
backup_service = BackupService()

@backup_bp.route('/jobs', methods=['POST'])
def create_backup_job():
    """Create a new backup job"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'connection_id' not in data:
            return jsonify({'error': 'Name and connection_id are required'}), 400
        
        # Check if connection exists
        connection = DatabaseConnection.query.filter_by(connection_id=data['connection_id']).first()
        if not connection:
            return jsonify({'error': 'Database connection not found'}), 404
        
        # Create backup job
        backup_job = BackupJob(
            job_id=str(uuid.uuid4()),
            name=data['name'],
            description=data.get('description', ''),
            connection_id=data['connection_id'],
            backup_type=data.get('backup_type', 'full'),
            backup_format=data.get('backup_format', 'sql'),
            compression=data.get('compression', True),
            encryption=data.get('encryption', False),
            schedule_type=data.get('schedule_type', 'manual'),
            schedule_config=data.get('schedule_config', {}),
            storage_type=data.get('storage_type', 'local'),
            storage_path=data.get('storage_path'),
            storage_config=data.get('storage_config', {}),
            retention_days=data.get('retention_days', 30),
            max_backups=data.get('max_backups', 10)
        )
        
        # Calculate next run if scheduled
        if backup_job.schedule_type != 'manual':
            backup_job.next_run = backup_service.calculate_next_run(backup_job)
        
        db.session.add(backup_job)
        db.session.commit()
        
        return jsonify({
            'job_id': backup_job.job_id,
            'message': 'Backup job created successfully',
            'backup_job': backup_job.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/jobs', methods=['GET'])
def list_backup_jobs():
    """List all backup jobs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        connection_id = request.args.get('connection_id')
        status = request.args.get('status')
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        query = BackupJob.query
        
        if connection_id:
            query = query.filter_by(connection_id=connection_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        jobs = query.order_by(BackupJob.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'backup_jobs': [job.to_dict() for job in jobs.items],
            'total': jobs.total,
            'pages': jobs.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/jobs/<job_id>', methods=['GET'])
def get_backup_job(job_id):
    """Get backup job details"""
    try:
        backup_job = BackupJob.query.filter_by(job_id=job_id).first()
        
        if not backup_job:
            return jsonify({'error': 'Backup job not found'}), 404
        
        # Get recent backup runs
        recent_runs = BackupRun.query.filter_by(job_id=job_id).order_by(
            BackupRun.created_at.desc()
        ).limit(10).all()
        
        response = backup_job.to_dict()
        response['recent_runs'] = [run.to_dict() for run in recent_runs]
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/jobs/<job_id>', methods=['PUT'])
def update_backup_job(job_id):
    """Update backup job"""
    try:
        backup_job = BackupJob.query.filter_by(job_id=job_id).first()
        
        if not backup_job:
            return jsonify({'error': 'Backup job not found'}), 404
        
        data = request.get_json() or {}
        
        # Update allowed fields
        if 'name' in data:
            backup_job.name = data['name']
        if 'description' in data:
            backup_job.description = data['description']
        if 'backup_type' in data:
            backup_job.backup_type = data['backup_type']
        if 'backup_format' in data:
            backup_job.backup_format = data['backup_format']
        if 'compression' in data:
            backup_job.compression = data['compression']
        if 'encryption' in data:
            backup_job.encryption = data['encryption']
        if 'schedule_type' in data:
            backup_job.schedule_type = data['schedule_type']
        if 'schedule_config' in data:
            backup_job.schedule_config = data['schedule_config']
        if 'storage_type' in data:
            backup_job.storage_type = data['storage_type']
        if 'storage_path' in data:
            backup_job.storage_path = data['storage_path']
        if 'storage_config' in data:
            backup_job.storage_config = data['storage_config']
        if 'retention_days' in data:
            backup_job.retention_days = data['retention_days']
        if 'max_backups' in data:
            backup_job.max_backups = data['max_backups']
        if 'is_active' in data:
            backup_job.is_active = data['is_active']
        
        # Recalculate next run if schedule changed
        if 'schedule_type' in data or 'schedule_config' in data:
            if backup_job.schedule_type != 'manual':
                backup_job.next_run = backup_service.calculate_next_run(backup_job)
            else:
                backup_job.next_run = None
        
        backup_job.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Backup job updated successfully',
            'backup_job': backup_job.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/jobs/<job_id>', methods=['DELETE'])
def delete_backup_job(job_id):
    """Delete backup job"""
    try:
        backup_job = BackupJob.query.filter_by(job_id=job_id).first()
        
        if not backup_job:
            return jsonify({'error': 'Backup job not found'}), 404
        
        # Delete associated backup runs (cascade should handle this)
        db.session.delete(backup_job)
        db.session.commit()
        
        return jsonify({'message': 'Backup job deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/jobs/<job_id>/run', methods=['POST'])
def run_backup_job(job_id):
    """Run a backup job manually"""
    try:
        backup_job = BackupJob.query.filter_by(job_id=job_id).first()
        
        if not backup_job:
            return jsonify({'error': 'Backup job not found'}), 404
        
        if not backup_job.is_active:
            return jsonify({'error': 'Backup job is not active'}), 400
        
        # Start backup run
        run_id = backup_service.start_backup_run(job_id, 'manual')
        
        return jsonify({
            'run_id': run_id,
            'message': 'Backup run started',
            'status': 'running'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/runs/<run_id>', methods=['GET'])
def get_backup_run(run_id):
    """Get backup run details"""
    try:
        backup_run = BackupRun.query.filter_by(run_id=run_id).first()
        
        if not backup_run:
            return jsonify({'error': 'Backup run not found'}), 404
        
        return jsonify(backup_run.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/runs', methods=['GET'])
def list_backup_runs():
    """List backup runs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        job_id = request.args.get('job_id')
        status = request.args.get('status')
        
        query = BackupRun.query
        
        if job_id:
            query = query.filter_by(job_id=job_id)
        
        if status:
            query = query.filter_by(status=status)
        
        runs = query.order_by(BackupRun.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'backup_runs': [run.to_dict() for run in runs.items],
            'total': runs.total,
            'pages': runs.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/runs/<run_id>/cancel', methods=['POST'])
def cancel_backup_run(run_id):
    """Cancel a running backup"""
    try:
        backup_run = BackupRun.query.filter_by(run_id=run_id).first()
        
        if not backup_run:
            return jsonify({'error': 'Backup run not found'}), 404
        
        if backup_run.status != 'running':
            return jsonify({'error': 'Backup run is not running'}), 400
        
        # Cancel backup run
        result = backup_service.cancel_backup_run(run_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/schedule/check', methods=['POST'])
def check_scheduled_backups():
    """Check and run scheduled backups"""
    try:
        # Find jobs that need to run
        current_time = datetime.utcnow()
        due_jobs = BackupJob.query.filter(
            BackupJob.is_active == True,
            BackupJob.schedule_type != 'manual',
            BackupJob.next_run <= current_time
        ).all()
        
        started_runs = []
        
        for job in due_jobs:
            try:
                run_id = backup_service.start_backup_run(job.job_id, 'scheduled')
                started_runs.append({
                    'job_id': job.job_id,
                    'run_id': run_id,
                    'job_name': job.name
                })
                
                # Update next run time
                job.next_run = backup_service.calculate_next_run(job)
                
            except Exception as e:
                print(f"Error starting scheduled backup for job {job.job_id}: {e}")
        
        db.session.commit()
        
        return jsonify({
            'message': f'Started {len(started_runs)} scheduled backups',
            'started_runs': started_runs
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/cleanup', methods=['POST'])
def cleanup_old_backups():
    """Clean up old backup files based on retention policies"""
    try:
        data = request.get_json() or {}
        job_id = data.get('job_id')  # Optional: clean specific job
        
        result = backup_service.cleanup_old_backups(job_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/restore', methods=['POST'])
def restore_backup():
    """Restore from a backup"""
    try:
        data = request.get_json()
        
        if not data or 'run_id' not in data:
            return jsonify({'error': 'Backup run ID is required'}), 400
        
        run_id = data['run_id']
        target_connection_id = data.get('target_connection_id')
        restore_options = data.get('restore_options', {})
        
        # Start restore operation
        result = backup_service.start_restore_operation(run_id, target_connection_id, restore_options)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/stats', methods=['GET'])
def get_backup_stats():
    """Get backup statistics"""
    try:
        # Overall statistics
        total_jobs = BackupJob.query.count()
        active_jobs = BackupJob.query.filter_by(is_active=True).count()
        
        # Recent runs statistics
        recent_runs = BackupRun.query.filter(
            BackupRun.created_at >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        successful_runs = len([r for r in recent_runs if r.status == 'completed'])
        failed_runs = len([r for r in recent_runs if r.status == 'failed'])
        
        # Storage statistics
        total_backup_size = sum([r.backup_size_bytes or 0 for r in recent_runs if r.backup_size_bytes])
        
        # Upcoming scheduled backups
        upcoming_backups = BackupJob.query.filter(
            BackupJob.is_active == True,
            BackupJob.next_run.isnot(None),
            BackupJob.next_run > datetime.utcnow()
        ).order_by(BackupJob.next_run).limit(10).all()
        
        return jsonify({
            'jobs': {
                'total': total_jobs,
                'active': active_jobs
            },
            'recent_runs': {
                'total': len(recent_runs),
                'successful': successful_runs,
                'failed': failed_runs,
                'success_rate': round((successful_runs / len(recent_runs) * 100) if recent_runs else 0, 2)
            },
            'storage': {
                'total_size_bytes': total_backup_size,
                'total_size_mb': round(total_backup_size / (1024 * 1024), 2)
            },
            'upcoming_backups': [
                {
                    'job_id': job.job_id,
                    'job_name': job.name,
                    'next_run': job.next_run.isoformat() if job.next_run else None,
                    'backup_type': job.backup_type
                }
                for job in upcoming_backups
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/templates', methods=['GET'])
def get_backup_templates():
    """Get backup job templates for common scenarios"""
    try:
        templates = [
            {
                'name': 'Daily Full Backup',
                'description': 'Complete database backup every day at 2 AM',
                'template': {
                    'backup_type': 'full',
                    'backup_format': 'sql',
                    'compression': True,
                    'encryption': False,
                    'schedule_type': 'daily',
                    'schedule_config': {'hour': 2, 'minute': 0},
                    'retention_days': 30,
                    'max_backups': 30
                }
            },
            {
                'name': 'Weekly Full + Daily Incremental',
                'description': 'Full backup weekly, incremental daily',
                'template': {
                    'backup_type': 'incremental',
                    'backup_format': 'sql',
                    'compression': True,
                    'encryption': True,
                    'schedule_type': 'daily',
                    'schedule_config': {'hour': 3, 'minute': 0},
                    'retention_days': 90,
                    'max_backups': 90
                }
            },
            {
                'name': 'Hourly Incremental',
                'description': 'Incremental backup every hour during business hours',
                'template': {
                    'backup_type': 'incremental',
                    'backup_format': 'binary',
                    'compression': True,
                    'encryption': False,
                    'schedule_type': 'cron',
                    'schedule_config': {'cron_expression': '0 0 9-17 * * 1-5'},
                    'retention_days': 7,
                    'max_backups': 168
                }
            }
        ]
        
        return jsonify({'templates': templates})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

