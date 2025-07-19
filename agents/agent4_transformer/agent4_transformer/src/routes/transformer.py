"""
Transformer routes for Agent 4: Intelligent Data Transformer
"""

import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from src.models.transformer import db, TransformationJob, TemplateMapping
from src.services.transformation_service import TransformationService

transformer_bp = Blueprint('transformer', __name__)

# Initialize transformation service
transformation_service = TransformationService()

@transformer_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'agent': 'agent4_transformer',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@transformer_bp.route('/jobs', methods=['GET'])
def list_transformation_jobs():
    """List all transformation jobs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status')
        
        query = TransformationJob.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        jobs = query.order_by(TransformationJob.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'jobs': [job.to_dict() for job in jobs.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': jobs.total,
                'pages': jobs.pages
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transformer_bp.route('/jobs', methods=['POST'])
def create_transformation_job():
    """Create a new transformation job"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['name', 'mapping_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Check if mapping exists
        mapping = TemplateMapping.query.filter_by(mapping_id=data['mapping_id']).first()
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        
        # Create transformation job
        job = TransformationJob(
            job_id=str(uuid.uuid4()),
            name=data['name'],
            description=data.get('description', ''),
            mapping_id=data['mapping_id'],
            source_data_path=data.get('source_data_path'),
            target_data_path=data.get('target_data_path')
        )
        
        db.session.add(job)
        db.session.commit()
        
        return jsonify({
            'message': 'Transformation job created successfully',
            'job': job.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transformer_bp.route('/jobs/<job_id>', methods=['GET'])
def get_transformation_job(job_id):
    """Get a specific transformation job"""
    try:
        job = TransformationJob.query.filter_by(job_id=job_id).first()
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify({'job': job.to_dict()})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transformer_bp.route('/jobs/<job_id>/execute', methods=['POST'])
def execute_transformation_job(job_id):
    """Execute a transformation job"""
    try:
        job = TransformationJob.query.filter_by(job_id=job_id).first()
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        if job.status == 'running':
            return jsonify({'error': 'Job is already running'}), 400
        
        # Start the transformation
        result = transformation_service.execute_transformation(job_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transformer_bp.route('/jobs/<job_id>/cancel', methods=['POST'])
def cancel_transformation_job(job_id):
    """Cancel a running transformation job"""
    try:
        job = TransformationJob.query.filter_by(job_id=job_id).first()
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        if job.status != 'running':
            return jsonify({'error': 'Job is not running'}), 400
        
        # Cancel the transformation
        result = transformation_service.cancel_transformation(job_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transformer_bp.route('/jobs/<job_id>/status', methods=['GET'])
def get_job_status(job_id):
    """Get the status of a transformation job"""
    try:
        job = TransformationJob.query.filter_by(job_id=job_id).first()
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify({
            'job_id': job.job_id,
            'status': job.status,
            'progress_percentage': job.progress_percentage,
            'records_processed': job.records_processed,
            'records_successful': job.records_successful,
            'records_failed': job.records_failed,
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'error_message': job.error_message
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transformer_bp.route('/transform', methods=['POST'])
def transform_data():
    """Transform data directly without creating a job"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['mapping_id', 'source_data']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Check if mapping exists
        mapping = TemplateMapping.query.filter_by(mapping_id=data['mapping_id']).first()
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        
        # Transform the data
        result = transformation_service.transform_data_direct(
            data['mapping_id'],
            data['source_data'],
            data.get('options', {})
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transformer_bp.route('/validate', methods=['POST'])
def validate_transformation():
    """Validate a transformation without executing it"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['mapping_id', 'source_data']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Check if mapping exists
        mapping = TemplateMapping.query.filter_by(mapping_id=data['mapping_id']).first()
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        
        # Validate the transformation
        result = transformation_service.validate_transformation(
            data['mapping_id'],
            data['source_data']
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transformer_bp.route('/preview', methods=['POST'])
def preview_transformation():
    """Preview transformation results"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['mapping_id', 'source_data']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Check if mapping exists
        mapping = TemplateMapping.query.filter_by(mapping_id=data['mapping_id']).first()
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        
        # Preview the transformation
        result = transformation_service.preview_transformation(
            data['mapping_id'],
            data['source_data'],
            data.get('limit', 10)
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transformer_bp.route('/upload', methods=['POST'])
def upload_source_data():
    """Upload source data file for transformation"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Process the uploaded file
        result = transformation_service.process_uploaded_file(file)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transformer_bp.route('/download/<job_id>', methods=['GET'])
def download_transformed_data(job_id):
    """Download transformed data from a completed job"""
    try:
        job = TransformationJob.query.filter_by(job_id=job_id).first()
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        if job.status != 'completed':
            return jsonify({'error': 'Job is not completed'}), 400
        
        # Generate download for the transformed data
        result = transformation_service.generate_download(job_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transformer_bp.route('/statistics', methods=['GET'])
def get_transformation_statistics():
    """Get transformation statistics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Get statistics
        stats = transformation_service.get_transformation_statistics(days)
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transformer_bp.route('/quality/report', methods=['GET'])
def get_quality_report():
    """Get data quality report"""
    try:
        job_id = request.args.get('job_id')
        
        if job_id:
            # Get quality report for specific job
            job = TransformationJob.query.filter_by(job_id=job_id).first()
            if not job:
                return jsonify({'error': 'Job not found'}), 404
            
            report = transformation_service.get_job_quality_report(job_id)
        else:
            # Get overall quality report
            report = transformation_service.get_overall_quality_report()
        
        return jsonify(report)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transformer_bp.route('/batch', methods=['POST'])
def create_batch_transformation():
    """Create a batch transformation job for multiple files"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['name', 'mapping_id', 'source_files']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Create batch transformation
        result = transformation_service.create_batch_transformation(data)
        
        return jsonify(result), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transformer_bp.route('/templates/suggest', methods=['POST'])
def suggest_template_mapping():
    """Suggest template mapping based on source data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        if 'source_data' not in data:
            return jsonify({'error': 'Source data is required'}), 400
        
        # Get mapping suggestions
        suggestions = transformation_service.suggest_template_mapping(
            data['source_data'],
            data.get('target_template_id'),
            data.get('options', {})
        )
        
        return jsonify(suggestions)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

