"""
Templates routes for Agent 4: Intelligent Data Transformer
"""

import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from src.models.transformer import db, Template
from src.services.template_service import TemplateService

templates_bp = Blueprint('templates', __name__)

# Initialize template service
template_service = TemplateService()

@templates_bp.route('/', methods=['GET'])
def list_templates():
    """List all templates"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        template_type = request.args.get('type')
        platform = request.args.get('platform')
        
        query = Template.query.filter_by(is_active=True)
        
        if template_type:
            query = query.filter_by(template_type=template_type)
        
        if platform:
            query = query.filter_by(platform=platform)
        
        templates = query.order_by(Template.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'templates': [template.to_dict() for template in templates.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': templates.total,
                'pages': templates.pages
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/', methods=['POST'])
def create_template():
    """Create a new template"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['name', 'template_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Create template
        template = Template(
            template_id=str(uuid.uuid4()),
            name=data['name'],
            description=data.get('description', ''),
            template_type=data['template_type'],
            platform=data.get('platform'),
            schema_definition=data.get('schema_definition', {}),
            sample_data=data.get('sample_data', {}),
            validation_rules=data.get('validation_rules', {}),
            documentation=data.get('documentation', ''),
            column_descriptions=data.get('column_descriptions', {}),
            business_rules=data.get('business_rules', {}),
            version=data.get('version', '1.0')
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            'message': 'Template created successfully',
            'template': template.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/<template_id>', methods=['GET'])
def get_template(template_id):
    """Get a specific template"""
    try:
        template = Template.query.filter_by(template_id=template_id).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        return jsonify({'template': template.to_dict()})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/<template_id>', methods=['PUT'])
def update_template(template_id):
    """Update a template"""
    try:
        template = Template.query.filter_by(template_id=template_id).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Update template fields
        updatable_fields = [
            'name', 'description', 'platform', 'schema_definition',
            'sample_data', 'validation_rules', 'documentation',
            'column_descriptions', 'business_rules', 'version'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(template, field, data[field])
        
        template.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Template updated successfully',
            'template': template.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Delete a template (soft delete)"""
    try:
        template = Template.query.filter_by(template_id=template_id).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        # Soft delete
        template.is_active = False
        template.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Template deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/types', methods=['GET'])
def get_template_types():
    """Get available template types"""
    try:
        types = template_service.get_available_template_types()
        return jsonify({'template_types': types})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/platforms', methods=['GET'])
def get_platforms():
    """Get available platforms"""
    try:
        platforms = template_service.get_available_platforms()
        return jsonify({'platforms': platforms})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/<template_id>/validate', methods=['POST'])
def validate_template_data(template_id):
    """Validate data against a template"""
    try:
        template = Template.query.filter_by(template_id=template_id).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        data = request.get_json()
        if not data or 'data' not in data:
            return jsonify({'error': 'Data to validate is required'}), 400
        
        # Validate the data
        validation_result = template_service.validate_data_against_template(
            template_id, data['data']
        )
        
        return jsonify(validation_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/<template_id>/analyze', methods=['POST'])
def analyze_template_data(template_id):
    """Analyze data structure against a template"""
    try:
        template = Template.query.filter_by(template_id=template_id).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        data = request.get_json()
        if not data or 'data' not in data:
            return jsonify({'error': 'Data to analyze is required'}), 400
        
        # Analyze the data
        analysis_result = template_service.analyze_data_structure(
            template_id, data['data']
        )
        
        return jsonify(analysis_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/import', methods=['POST'])
def import_template():
    """Import template from file or URL"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        import_type = data.get('import_type', 'file')  # file, url, sample_data
        
        if import_type == 'file':
            if 'file_path' not in data:
                return jsonify({'error': 'File path is required'}), 400
            
            result = template_service.import_template_from_file(data['file_path'])
            
        elif import_type == 'url':
            if 'url' not in data:
                return jsonify({'error': 'URL is required'}), 400
            
            result = template_service.import_template_from_url(data['url'])
            
        elif import_type == 'sample_data':
            if 'sample_data' not in data:
                return jsonify({'error': 'Sample data is required'}), 400
            
            result = template_service.create_template_from_sample_data(
                data['sample_data'],
                data.get('template_name', 'Imported Template'),
                data.get('template_type', 'unknown'),
                data.get('platform')
            )
            
        else:
            return jsonify({'error': 'Invalid import type'}), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/export/<template_id>', methods=['GET'])
def export_template(template_id):
    """Export template to various formats"""
    try:
        template = Template.query.filter_by(template_id=template_id).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        export_format = request.args.get('format', 'json')  # json, csv, excel
        
        # Export the template
        result = template_service.export_template(template_id, export_format)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/<template_id>/clone', methods=['POST'])
def clone_template(template_id):
    """Clone an existing template"""
    try:
        template = Template.query.filter_by(template_id=template_id).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        data = request.get_json()
        new_name = data.get('name', f"{template.name} (Copy)")
        
        # Clone the template
        cloned_template = Template(
            template_id=str(uuid.uuid4()),
            name=new_name,
            description=data.get('description', template.description),
            template_type=template.template_type,
            platform=data.get('platform', template.platform),
            schema_definition=template.schema_definition.copy() if template.schema_definition else {},
            sample_data=template.sample_data.copy() if template.sample_data else {},
            validation_rules=template.validation_rules.copy() if template.validation_rules else {},
            documentation=template.documentation,
            column_descriptions=template.column_descriptions.copy() if template.column_descriptions else {},
            business_rules=template.business_rules.copy() if template.business_rules else {},
            version=data.get('version', '1.0')
        )
        
        db.session.add(cloned_template)
        db.session.commit()
        
        return jsonify({
            'message': 'Template cloned successfully',
            'template': cloned_template.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/<template_id>/compare/<other_template_id>', methods=['GET'])
def compare_templates(template_id, other_template_id):
    """Compare two templates"""
    try:
        template1 = Template.query.filter_by(template_id=template_id).first()
        template2 = Template.query.filter_by(template_id=other_template_id).first()
        
        if not template1:
            return jsonify({'error': 'First template not found'}), 404
        
        if not template2:
            return jsonify({'error': 'Second template not found'}), 404
        
        # Compare the templates
        comparison_result = template_service.compare_templates(template_id, other_template_id)
        
        return jsonify(comparison_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/search', methods=['POST'])
def search_templates():
    """Search templates by various criteria"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Search criteria is required'}), 400
        
        # Search templates
        search_results = template_service.search_templates(data)
        
        return jsonify(search_results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/<template_id>/usage', methods=['GET'])
def get_template_usage(template_id):
    """Get template usage statistics"""
    try:
        template = Template.query.filter_by(template_id=template_id).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        # Get usage statistics
        usage_stats = template_service.get_template_usage_statistics(template_id)
        
        return jsonify(usage_stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/bulk/upload', methods=['POST'])
def bulk_upload_templates():
    """Bulk upload templates from file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Process bulk upload
        result = template_service.bulk_upload_templates(file)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@templates_bp.route('/suggestions', methods=['POST'])
def get_template_suggestions():
    """Get template suggestions based on data sample"""
    try:
        data = request.get_json()
        
        if not data or 'sample_data' not in data:
            return jsonify({'error': 'Sample data is required'}), 400
        
        # Get template suggestions
        suggestions = template_service.suggest_templates_for_data(
            data['sample_data'],
            data.get('context', {})
        )
        
        return jsonify(suggestions)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

