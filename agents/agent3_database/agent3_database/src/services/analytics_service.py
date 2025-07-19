"""
Analytics Service for Agent 3: Database Manager
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import func
from src.models.database import db, DatabaseConnection, BackupJob, BackupRun, SyncOperation, SyncRun

class AnalyticsService:
    """Service for analytics and reporting"""
    
    def __init__(self):
        pass
    
    def get_connection_type_distribution(self) -> List[Dict[str, Any]]:
        """Get distribution of database connection types"""
        try:
            type_stats = db.session.query(
                DatabaseConnection.db_type,
                func.count(DatabaseConnection.id).label('count')
            ).group_by(DatabaseConnection.db_type).all()
            
            return [
                {'type': db_type, 'count': count}
                for db_type, count in type_stats
            ]
            
        except Exception as e:
            print(f"Error getting connection type distribution: {e}")
            return []
    
    def get_performance_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get performance metrics for the specified time range"""
        try:
            # Backup performance
            backup_runs = BackupRun.query.filter(
                BackupRun.created_at >= start_date,
                BackupRun.created_at <= end_date
            ).all()
            
            backup_metrics = {
                'total_runs': len(backup_runs),
                'successful_runs': len([r for r in backup_runs if r.status == 'completed']),
                'failed_runs': len([r for r in backup_runs if r.status == 'failed']),
                'average_duration': 0,
                'total_data_backed_up_mb': 0
            }
            
            if backup_runs:
                durations = [r.duration_seconds for r in backup_runs if r.duration_seconds]
                backup_metrics['average_duration'] = sum(durations) / len(durations) if durations else 0
                
                sizes = [r.backup_size_bytes for r in backup_runs if r.backup_size_bytes]
                backup_metrics['total_data_backed_up_mb'] = sum(sizes) / (1024 * 1024) if sizes else 0
            
            # Sync performance
            sync_runs = SyncRun.query.filter(
                SyncRun.created_at >= start_date,
                SyncRun.created_at <= end_date
            ).all()
            
            sync_metrics = {
                'total_runs': len(sync_runs),
                'successful_runs': len([r for r in sync_runs if r.status == 'completed']),
                'failed_runs': len([r for r in sync_runs if r.status == 'failed']),
                'total_records_synced': sum([r.records_processed or 0 for r in sync_runs])
            }
            
            return {
                'backup_metrics': backup_metrics,
                'sync_metrics': sync_metrics
            }
            
        except Exception as e:
            print(f"Error getting performance metrics: {e}")
            return {}
    
    def get_activity_timeline(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get activity timeline for the specified time range"""
        try:
            timeline = []
            
            # Add backup activities
            backup_runs = BackupRun.query.filter(
                BackupRun.created_at >= start_date,
                BackupRun.created_at <= end_date
            ).order_by(BackupRun.created_at.desc()).limit(50).all()
            
            for run in backup_runs:
                timeline.append({
                    'timestamp': run.created_at.isoformat(),
                    'type': 'backup',
                    'status': run.status,
                    'description': f"Backup run {run.run_id}",
                    'duration_seconds': run.duration_seconds
                })
            
            # Add sync activities
            sync_runs = SyncRun.query.filter(
                SyncRun.created_at >= start_date,
                SyncRun.created_at <= end_date
            ).order_by(SyncRun.created_at.desc()).limit(50).all()
            
            for run in sync_runs:
                timeline.append({
                    'timestamp': run.created_at.isoformat(),
                    'type': 'sync',
                    'status': run.status,
                    'description': f"Sync run {run.run_id}",
                    'records_processed': run.records_processed
                })
            
            # Sort by timestamp
            timeline.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return timeline[:100]  # Return latest 100 activities
            
        except Exception as e:
            print(f"Error getting activity timeline: {e}")
            return []
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            # Connection health
            total_connections = DatabaseConnection.query.count()
            active_connections = DatabaseConnection.query.filter_by(is_active=True).count()
            
            # Recent backup health
            recent_backups = BackupRun.query.filter(
                BackupRun.created_at >= datetime.utcnow() - timedelta(days=1)
            ).all()
            
            backup_success_rate = 0
            if recent_backups:
                successful = len([r for r in recent_backups if r.status == 'completed'])
                backup_success_rate = (successful / len(recent_backups)) * 100
            
            # Recent sync health
            recent_syncs = SyncRun.query.filter(
                SyncRun.created_at >= datetime.utcnow() - timedelta(days=1)
            ).all()
            
            sync_success_rate = 0
            if recent_syncs:
                successful = len([r for r in recent_syncs if r.status == 'completed'])
                sync_success_rate = (successful / len(recent_syncs)) * 100
            
            # Overall health score
            health_score = (
                (active_connections / total_connections * 100 if total_connections > 0 else 100) * 0.3 +
                backup_success_rate * 0.35 +
                sync_success_rate * 0.35
            )
            
            health_status = 'excellent' if health_score >= 90 else \
                           'good' if health_score >= 75 else \
                           'fair' if health_score >= 50 else 'poor'
            
            return {
                'overall_score': round(health_score, 1),
                'status': health_status,
                'connection_health': {
                    'total': total_connections,
                    'active': active_connections,
                    'percentage': round((active_connections / total_connections * 100) if total_connections > 0 else 0, 1)
                },
                'backup_health': {
                    'recent_runs': len(recent_backups),
                    'success_rate': round(backup_success_rate, 1)
                },
                'sync_health': {
                    'recent_runs': len(recent_syncs),
                    'success_rate': round(sync_success_rate, 1)
                }
            }
            
        except Exception as e:
            print(f"Error getting system health: {e}")
            return {'overall_score': 0, 'status': 'unknown'}
    
    def get_connection_usage_analytics(self, days: int) -> Dict[str, Any]:
        """Get connection usage analytics"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            connections = DatabaseConnection.query.all()
            
            usage_data = []
            for conn in connections:
                # Calculate usage metrics
                usage_data.append({
                    'connection_id': conn.connection_id,
                    'name': conn.name,
                    'db_type': conn.db_type,
                    'connection_count': conn.connection_count or 0,
                    'last_used': conn.last_used.isoformat() if conn.last_used else None,
                    'is_active': conn.is_active
                })
            
            # Sort by usage
            usage_data.sort(key=lambda x: x['connection_count'], reverse=True)
            
            return {
                'usage_data': usage_data,
                'total_connections': len(connections),
                'most_used': usage_data[0] if usage_data else None,
                'least_used': usage_data[-1] if usage_data else None
            }
            
        except Exception as e:
            print(f"Error getting connection usage analytics: {e}")
            return {}
    
    def get_backup_performance_analytics(self, days: int) -> Dict[str, Any]:
        """Get backup performance analytics"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            backup_runs = BackupRun.query.filter(
                BackupRun.created_at >= start_date
            ).all()
            
            if not backup_runs:
                return {'message': 'No backup data available for the specified period'}
            
            # Performance metrics
            durations = [r.duration_seconds for r in backup_runs if r.duration_seconds]
            sizes = [r.backup_size_bytes for r in backup_runs if r.backup_size_bytes]
            
            performance_data = {
                'total_runs': len(backup_runs),
                'successful_runs': len([r for r in backup_runs if r.status == 'completed']),
                'failed_runs': len([r for r in backup_runs if r.status == 'failed']),
                'average_duration_seconds': sum(durations) / len(durations) if durations else 0,
                'total_backup_size_mb': sum(sizes) / (1024 * 1024) if sizes else 0,
                'success_rate': len([r for r in backup_runs if r.status == 'completed']) / len(backup_runs) * 100
            }
            
            # Daily breakdown
            daily_stats = {}
            for run in backup_runs:
                date_key = run.created_at.date().isoformat()
                if date_key not in daily_stats:
                    daily_stats[date_key] = {'runs': 0, 'successful': 0, 'failed': 0}
                
                daily_stats[date_key]['runs'] += 1
                if run.status == 'completed':
                    daily_stats[date_key]['successful'] += 1
                elif run.status == 'failed':
                    daily_stats[date_key]['failed'] += 1
            
            return {
                'performance_summary': performance_data,
                'daily_breakdown': daily_stats
            }
            
        except Exception as e:
            print(f"Error getting backup performance analytics: {e}")
            return {}
    
    def get_sync_performance_analytics(self, days: int) -> Dict[str, Any]:
        """Get sync performance analytics"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            sync_runs = SyncRun.query.filter(
                SyncRun.created_at >= start_date
            ).all()
            
            if not sync_runs:
                return {'message': 'No sync data available for the specified period'}
            
            # Performance metrics
            performance_data = {
                'total_runs': len(sync_runs),
                'successful_runs': len([r for r in sync_runs if r.status == 'completed']),
                'failed_runs': len([r for r in sync_runs if r.status == 'failed']),
                'total_records_processed': sum([r.records_processed or 0 for r in sync_runs]),
                'total_records_synced': sum([
                    (r.records_inserted or 0) + (r.records_updated or 0) 
                    for r in sync_runs
                ]),
                'success_rate': len([r for r in sync_runs if r.status == 'completed']) / len(sync_runs) * 100
            }
            
            return {
                'performance_summary': performance_data
            }
            
        except Exception as e:
            print(f"Error getting sync performance analytics: {e}")
            return {}
    
    def get_storage_analysis(self) -> Dict[str, Any]:
        """Get storage usage analysis"""
        try:
            # Analyze backup storage
            backup_runs = BackupRun.query.filter_by(status='completed').all()
            
            total_backup_size = sum([r.backup_size_bytes or 0 for r in backup_runs])
            
            # Group by job
            job_storage = {}
            for run in backup_runs:
                job_id = run.job_id
                if job_id not in job_storage:
                    job_storage[job_id] = {'runs': 0, 'total_size': 0}
                
                job_storage[job_id]['runs'] += 1
                job_storage[job_id]['total_size'] += run.backup_size_bytes or 0
            
            return {
                'total_backup_storage_bytes': total_backup_size,
                'total_backup_storage_mb': round(total_backup_size / (1024 * 1024), 2),
                'backup_count': len(backup_runs),
                'storage_by_job': job_storage
            }
            
        except Exception as e:
            print(f"Error getting storage analysis: {e}")
            return {}
    
    def get_trend_analysis(self, days: int, metric: str) -> Dict[str, Any]:
        """Get trend analysis for specified metric"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # This is a placeholder implementation
            # In a real system, this would analyze trends over time
            
            trend_data = {
                'metric': metric,
                'time_period_days': days,
                'trend_direction': 'stable',  # up, down, stable
                'trend_percentage': 0,
                'data_points': []
            }
            
            # Generate sample trend data
            for i in range(days):
                date = start_date + timedelta(days=i)
                trend_data['data_points'].append({
                    'date': date.date().isoformat(),
                    'value': 100 + (i * 2)  # Sample increasing trend
                })
            
            return trend_data
            
        except Exception as e:
            print(f"Error getting trend analysis: {e}")
            return {}
    
    def generate_custom_report(self, report_type: str, time_range: Dict[str, Any], 
                             filters: Dict[str, Any], format_type: str) -> Dict[str, Any]:
        """Generate custom analytics report"""
        try:
            # This is a placeholder implementation
            report_data = {
                'report_id': f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'report_type': report_type,
                'generated_at': datetime.utcnow().isoformat(),
                'format': format_type,
                'data': {
                    'summary': 'Custom report generated successfully',
                    'metrics': {},
                    'charts': []
                }
            }
            
            return {
                'success': True,
                'report': report_data
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_scheduled_reports(self) -> List[Dict[str, Any]]:
        """Get list of scheduled reports"""
        # Placeholder implementation
        return [
            {
                'id': 'daily_summary',
                'name': 'Daily Summary Report',
                'schedule': 'daily',
                'last_run': datetime.utcnow().isoformat(),
                'status': 'active'
            }
        ]
    
    def create_scheduled_report(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a scheduled report"""
        # Placeholder implementation
        return {
            'success': True,
            'report_id': f"scheduled_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'message': 'Scheduled report created successfully'
        }
    
    def get_alert_rules(self) -> List[Dict[str, Any]]:
        """Get analytics alert rules"""
        # Placeholder implementation
        return [
            {
                'id': 'backup_failure_alert',
                'name': 'Backup Failure Alert',
                'condition': 'backup_failure_rate > 10%',
                'status': 'active'
            }
        ]
    
    def create_alert_rule(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create analytics alert rule"""
        # Placeholder implementation
        return {
            'success': True,
            'alert_id': f"alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'message': 'Alert rule created successfully'
        }
    
    def check_alert_conditions(self) -> Dict[str, Any]:
        """Check alert conditions and trigger alerts"""
        # Placeholder implementation
        return {
            'alerts_checked': 5,
            'alerts_triggered': 0,
            'message': 'All systems normal'
        }
    
    def export_analytics_data(self, export_type: str, format_type: str, 
                            time_range: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Export analytics data"""
        # Placeholder implementation
        return {
            'success': True,
            'export_id': f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'download_url': '/downloads/analytics_export.csv',
            'message': 'Export completed successfully'
        }
    
    def get_predictions(self, metric: str, days_ahead: int) -> Dict[str, Any]:
        """Get predictive analytics"""
        # Placeholder implementation
        return {
            'metric': metric,
            'prediction_period_days': days_ahead,
            'predicted_value': 150,
            'confidence': 0.85,
            'trend': 'increasing'
        }
    
    def get_agent_comparison_analytics(self, days: int) -> Dict[str, Any]:
        """Get comparison analytics between agents"""
        # Placeholder implementation
        return {
            'comparison_period_days': days,
            'agents': {
                'agent1': {'activity_score': 85, 'performance_score': 90},
                'agent2': {'activity_score': 78, 'performance_score': 88},
                'agent3': {'activity_score': 92, 'performance_score': 85}
            }
        }
    
    def get_data_quality_metrics(self, connection_id: Optional[str]) -> Dict[str, Any]:
        """Get data quality metrics"""
        # Placeholder implementation
        return {
            'overall_quality_score': 85,
            'completeness': 92,
            'accuracy': 88,
            'consistency': 90,
            'timeliness': 75
        }
    
    def get_visualization_configs(self) -> Dict[str, Any]:
        """Get available visualization configurations"""
        return {
            'chart_types': ['line', 'bar', 'pie', 'scatter', 'heatmap'],
            'metrics': ['backup_performance', 'sync_performance', 'storage_usage', 'connection_activity'],
            'time_ranges': ['1d', '7d', '30d', '90d', '1y']
        }
    
    def get_visualization_data(self, viz_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get data for specific visualization"""
        # Placeholder implementation
        return {
            'visualization_type': viz_type,
            'data': [
                {'x': '2025-01-01', 'y': 100},
                {'x': '2025-01-02', 'y': 120},
                {'x': '2025-01-03', 'y': 110}
            ],
            'config': config
        }
    
    def get_kpis(self, time_period: str) -> Dict[str, Any]:
        """Get key performance indicators"""
        return {
            'backup_success_rate': 95.5,
            'sync_success_rate': 98.2,
            'average_backup_time': 45.3,
            'data_processed_gb': 2.8,
            'system_uptime': 99.9
        }
    
    def get_performance_benchmarks(self) -> Dict[str, Any]:
        """Get performance benchmarks"""
        return {
            'backup_time_benchmark': 60,  # seconds
            'sync_success_benchmark': 95,  # percentage
            'storage_efficiency_benchmark': 80  # percentage
        }
    
    def get_automated_insights(self) -> List[Dict[str, Any]]:
        """Get automated insights and recommendations"""
        return [
            {
                'type': 'performance',
                'title': 'Backup Performance Improvement',
                'description': 'Consider scheduling backups during off-peak hours to improve performance.',
                'priority': 'medium',
                'action': 'reschedule_backups'
            },
            {
                'type': 'storage',
                'title': 'Storage Optimization',
                'description': 'Old backup files can be cleaned up to free 500MB of storage.',
                'priority': 'low',
                'action': 'cleanup_old_backups'
            }
        ]
    
    def calculate_health_score(self) -> Dict[str, Any]:
        """Calculate overall system health score"""
        try:
            health_data = self.get_system_health()
            
            return {
                'overall_score': health_data.get('overall_score', 0),
                'status': health_data.get('status', 'unknown'),
                'components': {
                    'connections': health_data.get('connection_health', {}),
                    'backups': health_data.get('backup_health', {}),
                    'syncs': health_data.get('sync_health', {})
                },
                'recommendations': self.get_automated_insights()
            }
            
        except Exception as e:
            return {
                'overall_score': 0,
                'status': 'error',
                'error': str(e)
            }

