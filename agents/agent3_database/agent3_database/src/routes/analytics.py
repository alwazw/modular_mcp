"""
Analytics routes for Agent 3: Database Manager
"""

import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from src.models.database import db, DatabaseConnection, BackupJob, BackupRun, SyncOperation, SyncRun
from src.services.analytics_service import AnalyticsService

analytics_bp = Blueprint('analytics', __name__)

# Initialize analytics service
analytics_service = AnalyticsService()

@analytics_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get dashboard analytics data"""
    try:
        # Time range for analytics
        days = request.args.get('days', 7, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # System overview
        system_stats = {
            'connections': {
                'total': DatabaseConnection.query.count(),
                'active': DatabaseConnection.query.filter_by(is_active=True).count(),
                'by_type': analytics_service.get_connection_type_distribution()
            },
            'backups': {
                'total_jobs': BackupJob.query.count(),
                'active_jobs': BackupJob.query.filter_by(is_active=True).count(),
                'recent_runs': BackupRun.query.filter(BackupRun.created_at >= start_date).count()
            },
            'syncs': {
                'total_operations': SyncOperation.query.count(),
                'active_operations': SyncOperation.query.filter_by(is_active=True).count(),
                'recent_runs': SyncRun.query.filter(SyncRun.created_at >= start_date).count()
            }
        }
        
        # Performance metrics
        performance_metrics = analytics_service.get_performance_metrics(start_date, end_date)
        
        # Activity timeline
        activity_timeline = analytics_service.get_activity_timeline(start_date, end_date)
        
        # Health status
        health_status = analytics_service.get_system_health()
        
        return jsonify({
            'system_stats': system_stats,
            'performance_metrics': performance_metrics,
            'activity_timeline': activity_timeline,
            'health_status': health_status,
            'time_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/connections/usage', methods=['GET'])
def get_connection_usage():
    """Get database connection usage analytics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Get usage analytics
        usage_data = analytics_service.get_connection_usage_analytics(days)
        
        return jsonify(usage_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/backups/performance', methods=['GET'])
def get_backup_performance():
    """Get backup performance analytics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Get backup performance data
        performance_data = analytics_service.get_backup_performance_analytics(days)
        
        return jsonify(performance_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/syncs/performance', methods=['GET'])
def get_sync_performance():
    """Get sync performance analytics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Get sync performance data
        performance_data = analytics_service.get_sync_performance_analytics(days)
        
        return jsonify(performance_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/storage/analysis', methods=['GET'])
def get_storage_analysis():
    """Get storage usage analysis"""
    try:
        # Get storage analysis
        storage_data = analytics_service.get_storage_analysis()
        
        return jsonify(storage_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/trends', methods=['GET'])
def get_trends():
    """Get trend analysis"""
    try:
        days = request.args.get('days', 90, type=int)
        metric = request.args.get('metric', 'all')  # all, backups, syncs, connections
        
        # Get trend data
        trend_data = analytics_service.get_trend_analysis(days, metric)
        
        return jsonify(trend_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/reports/generate', methods=['POST'])
def generate_report():
    """Generate custom analytics report"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Report configuration is required'}), 400
        
        report_type = data.get('report_type', 'summary')
        time_range = data.get('time_range', {'days': 30})
        filters = data.get('filters', {})
        format_type = data.get('format', 'json')  # json, csv, pdf
        
        # Generate report
        report_data = analytics_service.generate_custom_report(
            report_type, time_range, filters, format_type
        )
        
        return jsonify(report_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/reports/scheduled', methods=['GET'])
def list_scheduled_reports():
    """List scheduled reports"""
    try:
        # Get scheduled reports (this would be stored in database in full implementation)
        scheduled_reports = analytics_service.get_scheduled_reports()
        
        return jsonify({'scheduled_reports': scheduled_reports})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/reports/scheduled', methods=['POST'])
def create_scheduled_report():
    """Create a scheduled report"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Report name is required'}), 400
        
        # Create scheduled report
        result = analytics_service.create_scheduled_report(data)
        
        return jsonify(result), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/alerts/rules', methods=['GET'])
def get_alert_rules():
    """Get analytics alert rules"""
    try:
        # Get alert rules
        alert_rules = analytics_service.get_alert_rules()
        
        return jsonify({'alert_rules': alert_rules})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/alerts/rules', methods=['POST'])
def create_alert_rule():
    """Create analytics alert rule"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'condition' not in data:
            return jsonify({'error': 'Name and condition are required'}), 400
        
        # Create alert rule
        result = analytics_service.create_alert_rule(data)
        
        return jsonify(result), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/alerts/check', methods=['POST'])
def check_alerts():
    """Check and trigger alerts based on current metrics"""
    try:
        # Check all alert conditions
        alert_results = analytics_service.check_alert_conditions()
        
        return jsonify(alert_results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/data/export', methods=['POST'])
def export_analytics_data():
    """Export analytics data in various formats"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Export configuration is required'}), 400
        
        export_type = data.get('export_type', 'summary')
        format_type = data.get('format', 'csv')  # csv, json, excel
        time_range = data.get('time_range', {'days': 30})
        filters = data.get('filters', {})
        
        # Export data
        export_result = analytics_service.export_analytics_data(
            export_type, format_type, time_range, filters
        )
        
        return jsonify(export_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/predictions', methods=['GET'])
def get_predictions():
    """Get predictive analytics"""
    try:
        metric = request.args.get('metric', 'storage_growth')
        days_ahead = request.args.get('days_ahead', 30, type=int)
        
        # Get predictions
        predictions = analytics_service.get_predictions(metric, days_ahead)
        
        return jsonify(predictions)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/agents/comparison', methods=['GET'])
def get_agent_comparison():
    """Get comparison analytics between agents"""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Get agent comparison data
        comparison_data = analytics_service.get_agent_comparison_analytics(days)
        
        return jsonify(comparison_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/data/quality', methods=['GET'])
def get_data_quality_metrics():
    """Get data quality metrics"""
    try:
        connection_id = request.args.get('connection_id')
        
        # Get data quality metrics
        quality_metrics = analytics_service.get_data_quality_metrics(connection_id)
        
        return jsonify(quality_metrics)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/visualizations/config', methods=['GET'])
def get_visualization_configs():
    """Get available visualization configurations"""
    try:
        # Get visualization configurations for dashboard building
        viz_configs = analytics_service.get_visualization_configs()
        
        return jsonify(viz_configs)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/visualizations/data', methods=['POST'])
def get_visualization_data():
    """Get data for specific visualization"""
    try:
        data = request.get_json()
        
        if not data or 'visualization_type' not in data:
            return jsonify({'error': 'Visualization type is required'}), 400
        
        viz_type = data['visualization_type']
        config = data.get('config', {})
        
        # Get visualization data
        viz_data = analytics_service.get_visualization_data(viz_type, config)
        
        return jsonify(viz_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/kpis', methods=['GET'])
def get_kpis():
    """Get key performance indicators"""
    try:
        time_period = request.args.get('period', 'week')  # day, week, month, quarter
        
        # Get KPIs
        kpis = analytics_service.get_kpis(time_period)
        
        return jsonify(kpis)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/benchmarks', methods=['GET'])
def get_benchmarks():
    """Get performance benchmarks"""
    try:
        # Get performance benchmarks
        benchmarks = analytics_service.get_performance_benchmarks()
        
        return jsonify(benchmarks)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/insights', methods=['GET'])
def get_insights():
    """Get automated insights and recommendations"""
    try:
        # Get automated insights
        insights = analytics_service.get_automated_insights()
        
        return jsonify(insights)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/health/score', methods=['GET'])
def get_health_score():
    """Get overall system health score"""
    try:
        # Calculate health score
        health_score = analytics_service.calculate_health_score()
        
        return jsonify(health_score)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

