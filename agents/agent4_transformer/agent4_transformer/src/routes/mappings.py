"""
Mappings routes for Agent 4: Intelligent Data Transformer
"""

import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from src.models.transformer import db, TemplateMapping, Template
from src.services.mapping_service import MappingService

mappings_bp = Blueprint('mappings', __name__)

# Initialize mapping service
mapping_service = MappingService()

@mappings_bp.route('/', methods=['GET'])
def list_mappings():
    """List all template mappings"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        source_template = request.args.get('source_template')
        target_template = request.args.get('target_template')
        
        query = TemplateMapping.query.filter_by(is_active=True)
        
        if source_template:
            query = query.filter_by(source_template_id=source_template)
        
        if target_template:
            query = query.filter_by(target_template_id=target_template)
        
        mappings = query.order_by(TemplateMapping.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'mappings': [mapping.to_dict() for mapping in mappings.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': mappings.total,
                'pages': mappings.pages
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/', methods=['POST'])
def create_mapping():
    """Create a new template mapping"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['name', 'source_template_id', 'target_template_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Check if templates exist
        source_template = Template.query.filter_by(template_id=data['source_template_id']).first()
        target_template = Template.query.filter_by(template_id=data['target_template_id']).first()
        
        if not source_template:
            return jsonify({'error': 'Source template not found'}), 404
        
        if not target_template:
            return jsonify({'error': 'Target template not found'}), 404
        
        # Create mapping
        mapping = TemplateMapping(
            mapping_id=str(uuid.uuid4()),
            name=data['name'],
            description=data.get('description', ''),
            source_template_id=data['source_template_id'],
            target_template_id=data['target_template_id'],
            field_mappings=data.get('field_mappings', {}),
            transformation_rules=data.get('transformation_rules', {}),
            default_values=data.get('default_values', {}),
            conditional_logic=data.get('conditional_logic', {}),
            mapping_type=data.get('mapping_type', 'manual')
        )
        
        db.session.add(mapping)
        db.session.commit()
        
        return jsonify({
            'message': 'Template mapping created successfully',
            'mapping': mapping.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/<mapping_id>', methods=['GET'])
def get_mapping(mapping_id):
    """Get a specific template mapping"""
    try:
        mapping = TemplateMapping.query.filter_by(mapping_id=mapping_id).first()
        
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        
        return jsonify({'mapping': mapping.to_dict()})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/<mapping_id>', methods=['PUT'])
def update_mapping(mapping_id):
    """Update a template mapping"""
    try:
        mapping = TemplateMapping.query.filter_by(mapping_id=mapping_id).first()
        
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Update mapping fields
        updatable_fields = [
            'name', 'description', 'field_mappings', 'transformation_rules',
            'default_values', 'conditional_logic', 'confidence_score'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(mapping, field, data[field])
        
        mapping.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Template mapping updated successfully',
            'mapping': mapping.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/<mapping_id>', methods=['DELETE'])
def delete_mapping(mapping_id):
    """Delete a template mapping (soft delete)"""
    try:
        mapping = TemplateMapping.query.filter_by(mapping_id=mapping_id).first()
        
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        
        # Soft delete
        mapping.is_active = False
        mapping.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Template mapping deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/generate', methods=['POST'])
def generate_mapping():
    """Generate mapping automatically using AI"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['source_template_id', 'target_template_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Check if templates exist
        source_template = Template.query.filter_by(template_id=data['source_template_id']).first()
        target_template = Template.query.filter_by(template_id=data['target_template_id']).first()
        
        if not source_template:
            return jsonify({'error': 'Source template not found'}), 404
        
        if not target_template:
            return jsonify({'error': 'Target template not found'}), 404
        
        # Generate mapping using AI
        result = mapping_service.generate_ai_mapping(
            data['source_template_id'],
            data['target_template_id'],
            data.get('sample_data'),
            data.get('options', {})
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/<mapping_id>/validate', methods=['POST'])
def validate_mapping(mapping_id):
    """Validate a template mapping"""
    try:
        mapping = TemplateMapping.query.filter_by(mapping_id=mapping_id).first()
        
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        
        data = request.get_json()
        sample_data = data.get('sample_data') if data else None
        
        # Validate the mapping
        validation_result = mapping_service.validate_mapping(mapping_id, sample_data)
        
        return jsonify(validation_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/<mapping_id>/test', methods=['POST'])
def test_mapping(mapping_id):
    """Test a template mapping with sample data"""
    try:
        mapping = TemplateMapping.query.filter_by(mapping_id=mapping_id).first()
        
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        
        data = request.get_json()
        if not data or 'test_data' not in data:
            return jsonify({'error': 'Test data is required'}), 400
        
        # Test the mapping
        test_result = mapping_service.test_mapping(mapping_id, data['test_data'])
        
        return jsonify(test_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/<mapping_id>/optimize', methods=['POST'])
def optimize_mapping(mapping_id):
    """Optimize a template mapping using AI"""
    try:
        mapping = TemplateMapping.query.filter_by(mapping_id=mapping_id).first()
        
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        
        data = request.get_json()
        optimization_data = data.get('optimization_data') if data else None
        
        # Optimize the mapping
        optimization_result = mapping_service.optimize_mapping(mapping_id, optimization_data)
        
        return jsonify(optimization_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/<mapping_id>/clone', methods=['POST'])
def clone_mapping(mapping_id):
    """Clone an existing template mapping"""
    try:
        mapping = TemplateMapping.query.filter_by(mapping_id=mapping_id).first()
        
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        
        data = request.get_json()
        new_name = data.get('name', f"{mapping.name} (Copy)")
        
        # Clone the mapping
        cloned_mapping = TemplateMapping(
            mapping_id=str(uuid.uuid4()),
            name=new_name,
            description=data.get('description', mapping.description),
            source_template_id=data.get('source_template_id', mapping.source_template_id),
            target_template_id=data.get('target_template_id', mapping.target_template_id),
            field_mappings=mapping.field_mappings.copy() if mapping.field_mappings else {},
            transformation_rules=mapping.transformation_rules.copy() if mapping.transformation_rules else {},
            default_values=mapping.default_values.copy() if mapping.default_values else {},
            conditional_logic=mapping.conditional_logic.copy() if mapping.conditional_logic else {},
            mapping_type='manual'
        )
        
        db.session.add(cloned_mapping)
        db.session.commit()
        
        return jsonify({
            'message': 'Template mapping cloned successfully',
            'mapping': cloned_mapping.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/suggest', methods=['POST'])
def suggest_mappings():
    """Suggest field mappings between templates"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['source_template_id', 'target_template_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Get mapping suggestions
        suggestions = mapping_service.suggest_field_mappings(
            data['source_template_id'],
            data['target_template_id'],
            data.get('sample_data'),
            data.get('context', {})
        )
        
        return jsonify(suggestions)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/<mapping_id>/learn', methods=['POST'])
def learn_from_feedback(mapping_id):
    """Learn from user feedback to improve mapping"""
    try:
        mapping = TemplateMapping.query.filter_by(mapping_id=mapping_id).first()
        
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        
        data = request.get_json()
        if not data or 'feedback' not in data:
            return jsonify({'error': 'Feedback data is required'}), 400
        
        # Learn from feedback
        learning_result = mapping_service.learn_from_feedback(mapping_id, data['feedback'])
        
        return jsonify(learning_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/batch/create', methods=['POST'])
def create_batch_mappings():
    """Create multiple mappings in batch"""
    try:
        data = request.get_json()
        
        if not data or 'mappings' not in data:
            return jsonify({'error': 'Mappings data is required'}), 400
        
        # Create batch mappings
        result = mapping_service.create_batch_mappings(data['mappings'])
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/export/<mapping_id>', methods=['GET'])
def export_mapping(mapping_id):
    """Export mapping configuration"""
    try:
        mapping = TemplateMapping.query.filter_by(mapping_id=mapping_id).first()
        
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        
        export_format = request.args.get('format', 'json')  # json, yaml, xml
        
        # Export the mapping
        result = mapping_service.export_mapping(mapping_id, export_format)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/import', methods=['POST'])
def import_mapping():
    """Import mapping configuration"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Import data is required'}), 400
        
        import_type = data.get('import_type', 'json')  # json, yaml, xml, file
        
        # Import the mapping
        result = mapping_service.import_mapping(data, import_type)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/<mapping_id>/statistics', methods=['GET'])
def get_mapping_statistics(mapping_id):
    """Get mapping usage and performance statistics"""
    try:
        mapping = TemplateMapping.query.filter_by(mapping_id=mapping_id).first()
        
        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404
        
        # Get mapping statistics
        stats = mapping_service.get_mapping_statistics(mapping_id)
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/search', methods=['POST'])
def search_mappings():
    """Search mappings by various criteria"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Search criteria is required'}), 400
        
        # Search mappings
        search_results = mapping_service.search_mappings(data)
        
        return jsonify(search_results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mappings_bp.route('/recommendations', methods=['GET'])
def get_mapping_recommendations():
    """Get mapping recommendations based on usage patterns"""
    try:
        # Get mapping recommendations
        recommendations = mapping_service.get_mapping_recommendations()
        
        return jsonify(recommendations)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

