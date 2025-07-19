"""
Sync Service for Agent 3: Database Manager
"""

import uuid
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from src.models.database import db, SyncOperation, SyncRun

class SyncService:
    """Service for data synchronization operations"""
    
    def __init__(self):
        self.sync_threads = {}
    
    def start_sync_run(self, sync_id: str, trigger_type: str) -> str:
        """Start a sync run"""
        try:
            # Create sync run record
            run_id = str(uuid.uuid4())
            sync_run = SyncRun(
                run_id=run_id,
                sync_id=sync_id,
                trigger_type=trigger_type,
                status='running',
                started_at=datetime.utcnow()
            )
            
            db.session.add(sync_run)
            db.session.commit()
            
            # Start sync in background thread
            def run_sync():
                try:
                    # Simulate sync process
                    import time
                    time.sleep(3)  # Simulate sync time
                    
                    # Update run with success
                    run = SyncRun.query.filter_by(run_id=run_id).first()
                    if run:
                        run.status = 'completed'
                        run.completed_at = datetime.utcnow()
                        run.duration_seconds = (run.completed_at - run.started_at).total_seconds()
                        run.records_processed = 500  # Placeholder
                        run.records_inserted = 100   # Placeholder
                        run.records_updated = 50     # Placeholder
                        
                        # Update operation statistics
                        operation = SyncOperation.query.filter_by(sync_id=sync_id).first()
                        if operation:
                            operation.last_sync = datetime.utcnow()
                            operation.total_syncs += 1
                            operation.successful_syncs += 1
                            operation.status = 'completed'
                        
                        db.session.commit()
                        
                except Exception as e:
                    # Update run with failure
                    run = SyncRun.query.filter_by(run_id=run_id).first()
                    if run:
                        run.status = 'failed'
                        run.completed_at = datetime.utcnow()
                        run.error_message = str(e)
                        
                        # Update operation statistics
                        operation = SyncOperation.query.filter_by(sync_id=sync_id).first()
                        if operation:
                            operation.last_sync = datetime.utcnow()
                            operation.total_syncs += 1
                            operation.failed_syncs += 1
                            operation.status = 'failed'
                        
                        db.session.commit()
                
                finally:
                    # Clean up thread reference
                    if run_id in self.sync_threads:
                        del self.sync_threads[run_id]
            
            thread = threading.Thread(target=run_sync, daemon=True)
            thread.start()
            self.sync_threads[run_id] = thread
            
            return run_id
            
        except Exception as e:
            raise Exception(f"Failed to start sync run: {str(e)}")
    
    def cancel_sync_run(self, run_id: str) -> Dict[str, Any]:
        """Cancel a running sync"""
        try:
            sync_run = SyncRun.query.filter_by(run_id=run_id).first()
            if not sync_run:
                return {'success': False, 'error': 'Sync run not found'}
            
            if sync_run.status != 'running':
                return {'success': False, 'error': 'Sync run is not running'}
            
            # Update status to cancelled
            sync_run.status = 'cancelled'
            sync_run.completed_at = datetime.utcnow()
            sync_run.error_message = 'Cancelled by user'
            
            db.session.commit()
            
            return {'success': True, 'message': 'Sync run cancelled'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def calculate_next_sync(self, sync_operation: SyncOperation) -> Optional[datetime]:
        """Calculate next sync time for a sync operation"""
        try:
            if sync_operation.schedule_type == 'manual':
                return None
            
            current_time = datetime.utcnow()
            
            if sync_operation.schedule_type == 'realtime':
                # For realtime, next sync is immediate
                return current_time
            
            elif sync_operation.schedule_type == 'daily':
                config = sync_operation.schedule_config or {}
                hour = config.get('hour', 1)
                minute = config.get('minute', 0)
                
                next_sync = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_sync <= current_time:
                    next_sync += timedelta(days=1)
                
                return next_sync
            
            elif sync_operation.schedule_type == 'weekly':
                config = sync_operation.schedule_config or {}
                day_of_week = config.get('day_of_week', 0)
                hour = config.get('hour', 1)
                minute = config.get('minute', 0)
                
                days_ahead = day_of_week - current_time.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                
                next_sync = current_time + timedelta(days=days_ahead)
                next_sync = next_sync.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                return next_sync
            
            else:
                return None
                
        except Exception as e:
            print(f"Error calculating next sync: {e}")
            return None
    
    def sync_with_agent1(self, agent1_url: str) -> Dict[str, Any]:
        """Sync data with Agent 1 (Web Scraper)"""
        try:
            # Get scraped content from Agent 1
            response = requests.get(f"{agent1_url}/api/scraper/content", timeout=30)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Failed to connect to Agent 1: {response.status_code}'
                }
            
            content_data = response.json()
            
            # Process and store the data
            # This is a placeholder - in real implementation, would store in database
            
            return {
                'success': True,
                'synced_items': len(content_data.get('content', [])),
                'message': 'Successfully synced with Agent 1'
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error connecting to Agent 1: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error syncing with Agent 1: {str(e)}'
            }
    
    def sync_with_agent2(self, agent2_url: str) -> Dict[str, Any]:
        """Sync data with Agent 2 (Knowledge Base)"""
        try:
            # Get knowledge base data from Agent 2
            response = requests.get(f"{agent2_url}/api/knowledge/bases", timeout=30)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Failed to connect to Agent 2: {response.status_code}'
                }
            
            kb_data = response.json()
            
            # Process and store the data
            # This is a placeholder - in real implementation, would store in database
            
            return {
                'success': True,
                'synced_items': len(kb_data.get('knowledge_bases', [])),
                'message': 'Successfully synced with Agent 2'
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error connecting to Agent 2: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error syncing with Agent 2: {str(e)}'
            }
    
    def preview_sync_operation(self, sync_id: str, limit: int = 100) -> Dict[str, Any]:
        """Preview what a sync operation would do"""
        try:
            sync_operation = SyncOperation.query.filter_by(sync_id=sync_id).first()
            if not sync_operation:
                return {'success': False, 'error': 'Sync operation not found'}
            
            # This is a placeholder implementation
            # In real implementation, would execute the source query and show preview
            
            preview_data = {
                'operation_name': sync_operation.name,
                'sync_type': sync_operation.sync_type,
                'source_query': sync_operation.source_query,
                'target_table': sync_operation.target_table,
                'estimated_records': 150,  # Placeholder
                'preview_records': [
                    {'id': 1, 'name': 'Sample Record 1', 'status': 'active'},
                    {'id': 2, 'name': 'Sample Record 2', 'status': 'pending'}
                ]
            }
            
            return {
                'success': True,
                'preview': preview_data
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_sync_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate sync operation configuration"""
        try:
            errors = []
            warnings = []
            
            # Required fields
            required_fields = ['name', 'source_connection_id', 'sync_type']
            for field in required_fields:
                if field not in config or not config[field]:
                    errors.append(f"Field '{field}' is required")
            
            # Sync type validation
            valid_sync_types = ['full', 'incremental', 'bidirectional']
            if config.get('sync_type') not in valid_sync_types:
                errors.append(f"Sync type must be one of: {', '.join(valid_sync_types)}")
            
            # Mode validation
            valid_sync_modes = ['push', 'pull', 'bidirectional']
            if config.get('sync_mode') and config.get('sync_mode') not in valid_sync_modes:
                errors.append(f"Sync mode must be one of: {', '.join(valid_sync_modes)}")
            
            # Schedule validation
            if config.get('schedule_type') and config.get('schedule_type') not in ['manual', 'realtime', 'daily', 'weekly', 'cron']:
                errors.append("Invalid schedule type")
            
            # Query validation
            if config.get('source_query'):
                query = config['source_query'].strip().upper()
                if not query.startswith('SELECT'):
                    warnings.append("Source query should typically be a SELECT statement")
            
            # Bidirectional sync warnings
            if config.get('sync_mode') == 'bidirectional':
                warnings.append("Bidirectional sync can cause conflicts. Ensure proper conflict resolution is configured.")
            
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

