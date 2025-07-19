"""
Backup Service for Agent 3: Database Manager
"""

import uuid
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from src.models.database import db, BackupJob, BackupRun

class BackupService:
    """Service for database backup operations"""
    
    def __init__(self):
        self.backup_threads = {}
    
    def start_backup_run(self, job_id: str, trigger_type: str) -> str:
        """Start a backup run"""
        try:
            # Create backup run record
            run_id = str(uuid.uuid4())
            backup_run = BackupRun(
                run_id=run_id,
                job_id=job_id,
                trigger_type=trigger_type,
                status='running',
                started_at=datetime.utcnow()
            )
            
            db.session.add(backup_run)
            db.session.commit()
            
            # Start backup in background thread
            def run_backup():
                try:
                    # Simulate backup process
                    # In a real implementation, this would perform actual backup
                    import time
                    time.sleep(5)  # Simulate backup time
                    
                    # Update run with success
                    run = BackupRun.query.filter_by(run_id=run_id).first()
                    if run:
                        run.status = 'completed'
                        run.completed_at = datetime.utcnow()
                        run.duration_seconds = (run.completed_at - run.started_at).total_seconds()
                        run.backup_file_path = f"/backups/{job_id}_{run_id}.sql"
                        run.backup_size_bytes = 1024 * 1024  # 1MB placeholder
                        run.records_backed_up = 1000  # Placeholder
                        
                        # Update job statistics
                        job = BackupJob.query.filter_by(job_id=job_id).first()
                        if job:
                            job.last_run = datetime.utcnow()
                            job.total_runs += 1
                            job.successful_runs += 1
                            job.status = 'completed'
                        
                        db.session.commit()
                        
                except Exception as e:
                    # Update run with failure
                    run = BackupRun.query.filter_by(run_id=run_id).first()
                    if run:
                        run.status = 'failed'
                        run.completed_at = datetime.utcnow()
                        run.error_message = str(e)
                        
                        # Update job statistics
                        job = BackupJob.query.filter_by(job_id=job_id).first()
                        if job:
                            job.last_run = datetime.utcnow()
                            job.total_runs += 1
                            job.failed_runs += 1
                            job.status = 'failed'
                        
                        db.session.commit()
                
                finally:
                    # Clean up thread reference
                    if run_id in self.backup_threads:
                        del self.backup_threads[run_id]
            
            thread = threading.Thread(target=run_backup, daemon=True)
            thread.start()
            self.backup_threads[run_id] = thread
            
            return run_id
            
        except Exception as e:
            raise Exception(f"Failed to start backup run: {str(e)}")
    
    def cancel_backup_run(self, run_id: str) -> Dict[str, Any]:
        """Cancel a running backup"""
        try:
            backup_run = BackupRun.query.filter_by(run_id=run_id).first()
            if not backup_run:
                return {'success': False, 'error': 'Backup run not found'}
            
            if backup_run.status != 'running':
                return {'success': False, 'error': 'Backup run is not running'}
            
            # Update status to cancelled
            backup_run.status = 'cancelled'
            backup_run.completed_at = datetime.utcnow()
            backup_run.error_message = 'Cancelled by user'
            
            db.session.commit()
            
            return {'success': True, 'message': 'Backup run cancelled'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def calculate_next_run(self, backup_job: BackupJob) -> Optional[datetime]:
        """Calculate next run time for a backup job"""
        try:
            if backup_job.schedule_type == 'manual':
                return None
            
            current_time = datetime.utcnow()
            
            if backup_job.schedule_type == 'daily':
                config = backup_job.schedule_config or {}
                hour = config.get('hour', 2)
                minute = config.get('minute', 0)
                
                next_run = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= current_time:
                    next_run += timedelta(days=1)
                
                return next_run
            
            elif backup_job.schedule_type == 'weekly':
                config = backup_job.schedule_config or {}
                day_of_week = config.get('day_of_week', 0)  # 0 = Monday
                hour = config.get('hour', 2)
                minute = config.get('minute', 0)
                
                days_ahead = day_of_week - current_time.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                
                next_run = current_time + timedelta(days=days_ahead)
                next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                return next_run
            
            elif backup_job.schedule_type == 'monthly':
                config = backup_job.schedule_config or {}
                day_of_month = config.get('day_of_month', 1)
                hour = config.get('hour', 2)
                minute = config.get('minute', 0)
                
                # Simple monthly calculation (can be improved)
                next_month = current_time.replace(day=1) + timedelta(days=32)
                next_run = next_month.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
                
                return next_run
            
            else:
                return None
                
        except Exception as e:
            print(f"Error calculating next run: {e}")
            return None
    
    def cleanup_old_backups(self, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Clean up old backup files based on retention policies"""
        try:
            # This is a placeholder implementation
            # In a real system, this would delete old backup files
            
            cleaned_files = 0
            freed_space_bytes = 0
            
            # Get jobs to clean up
            if job_id:
                jobs = BackupJob.query.filter_by(job_id=job_id).all()
            else:
                jobs = BackupJob.query.all()
            
            for job in jobs:
                # Find old backup runs to clean up
                cutoff_date = datetime.utcnow() - timedelta(days=job.retention_days)
                old_runs = BackupRun.query.filter(
                    BackupRun.job_id == job.job_id,
                    BackupRun.created_at < cutoff_date,
                    BackupRun.status == 'completed'
                ).all()
                
                # Also limit by max_backups
                all_runs = BackupRun.query.filter_by(
                    job_id=job.job_id,
                    status='completed'
                ).order_by(BackupRun.created_at.desc()).all()
                
                if len(all_runs) > job.max_backups:
                    old_runs.extend(all_runs[job.max_backups:])
                
                # Clean up old runs
                for run in old_runs:
                    if run.backup_size_bytes:
                        freed_space_bytes += run.backup_size_bytes
                    cleaned_files += 1
                    
                    # In real implementation, delete the actual backup file here
                    # os.remove(run.backup_file_path)
                    
                    db.session.delete(run)
            
            db.session.commit()
            
            return {
                'success': True,
                'cleaned_files': cleaned_files,
                'freed_space_bytes': freed_space_bytes,
                'freed_space_mb': round(freed_space_bytes / (1024 * 1024), 2)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def start_restore_operation(self, run_id: str, target_connection_id: Optional[str], 
                              restore_options: Dict[str, Any]) -> Dict[str, Any]:
        """Start a restore operation from a backup"""
        try:
            backup_run = BackupRun.query.filter_by(run_id=run_id).first()
            if not backup_run:
                return {'success': False, 'error': 'Backup run not found'}
            
            if backup_run.status != 'completed':
                return {'success': False, 'error': 'Backup run is not completed'}
            
            # This is a placeholder implementation
            # In a real system, this would perform actual restore
            
            restore_id = str(uuid.uuid4())
            
            return {
                'success': True,
                'restore_id': restore_id,
                'message': 'Restore operation started',
                'status': 'running'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

