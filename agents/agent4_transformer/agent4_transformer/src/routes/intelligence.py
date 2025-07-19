"""
Intelligence routes for Agent 4: Intelligent Data Transformer
"""

import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from src.models.transformer import db, IntelligenceRule, KnowledgeBase
from src.services.intelligence_service import IntelligenceService

intelligence_bp = Blueprint('intelligence', __name__)

# Initialize intelligence service
intelligence_service = IntelligenceService()

@intelligence_bp.route('/rules', methods=['GET'])
def list_intelligence_rules():
    """List all intelligence rules"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        rule_type = request.args.get('type')
        
        query = IntelligenceRule.query.filter_by(is_active=True)
        
        if rule_type:
            query = query.filter_by(rule_type=rule_type)
        
        rules = query.order_by(IntelligenceRule.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'rules': [rule.to_dict() for rule in rules.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': rules.total,
                'pages': rules.pages
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/rules', methods=['POST'])
def create_intelligence_rule():
    """Create a new intelligence rule"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['name', 'rule_type', 'pattern', 'action']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Create intelligence rule
        rule = IntelligenceRule(
            rule_id=str(uuid.uuid4()),
            name=data['name'],
            description=data.get('description', ''),
            rule_type=data['rule_type'],
            pattern=data['pattern'],
            action=data['action'],
            conditions=data.get('conditions', {}),
            template_types=data.get('template_types', []),
            platforms=data.get('platforms', []),
            is_system_generated=data.get('is_system_generated', False)
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify({
            'message': 'Intelligence rule created successfully',
            'rule': rule.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/rules/<rule_id>', methods=['GET'])
def get_intelligence_rule(rule_id):
    """Get a specific intelligence rule"""
    try:
        rule = IntelligenceRule.query.filter_by(rule_id=rule_id).first()
        
        if not rule:
            return jsonify({'error': 'Rule not found'}), 404
        
        return jsonify({'rule': rule.to_dict()})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/rules/<rule_id>', methods=['PUT'])
def update_intelligence_rule(rule_id):
    """Update an intelligence rule"""
    try:
        rule = IntelligenceRule.query.filter_by(rule_id=rule_id).first()
        
        if not rule:
            return jsonify({'error': 'Rule not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Update rule fields
        updatable_fields = [
            'name', 'description', 'pattern', 'action', 'conditions',
            'template_types', 'platforms', 'confidence_score'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(rule, field, data[field])
        
        rule.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Intelligence rule updated successfully',
            'rule': rule.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/rules/<rule_id>', methods=['DELETE'])
def delete_intelligence_rule(rule_id):
    """Delete an intelligence rule (soft delete)"""
    try:
        rule = IntelligenceRule.query.filter_by(rule_id=rule_id).first()
        
        if not rule:
            return jsonify({'error': 'Rule not found'}), 404
        
        # Soft delete
        rule.is_active = False
        rule.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Intelligence rule deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/analyze', methods=['POST'])
def analyze_data():
    """Analyze data using intelligence rules"""
    try:
        data = request.get_json()
        
        if not data or 'data' not in data:
            return jsonify({'error': 'Data to analyze is required'}), 400
        
        # Analyze the data
        analysis_result = intelligence_service.analyze_data(
            data['data'],
            data.get('context', {}),
            data.get('rule_types', [])
        )
        
        return jsonify(analysis_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/suggest/mappings', methods=['POST'])
def suggest_intelligent_mappings():
    """Suggest intelligent field mappings"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['source_schema', 'target_schema']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Get intelligent mapping suggestions
        suggestions = intelligence_service.suggest_intelligent_mappings(
            data['source_schema'],
            data['target_schema'],
            data.get('sample_data'),
            data.get('context', {})
        )
        
        return jsonify(suggestions)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/learn', methods=['POST'])
def learn_from_data():
    """Learn patterns from transformation data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Learning data is required'}), 400
        
        # Learn from the data
        learning_result = intelligence_service.learn_from_transformation_data(
            data.get('transformation_data', []),
            data.get('feedback_data', []),
            data.get('options', {})
        )
        
        return jsonify(learning_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/patterns/detect', methods=['POST'])
def detect_patterns():
    """Detect patterns in data"""
    try:
        data = request.get_json()
        
        if not data or 'data' not in data:
            return jsonify({'error': 'Data is required'}), 400
        
        # Detect patterns
        patterns = intelligence_service.detect_data_patterns(
            data['data'],
            data.get('pattern_types', []),
            data.get('options', {})
        )
        
        return jsonify(patterns)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/knowledge', methods=['GET'])
def list_knowledge_base():
    """List knowledge base entries"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category = request.args.get('category')
        platform = request.args.get('platform')
        
        query = KnowledgeBase.query.filter_by(is_active=True)
        
        if category:
            query = query.filter_by(category=category)
        
        if platform:
            query = query.filter_by(platform=platform)
        
        knowledge = query.order_by(KnowledgeBase.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'knowledge': [kb.to_dict() for kb in knowledge.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': knowledge.total,
                'pages': knowledge.pages
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/knowledge', methods=['POST'])
def create_knowledge_entry():
    """Create a new knowledge base entry"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['title', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Create knowledge entry
        knowledge = KnowledgeBase(
            knowledge_id=str(uuid.uuid4()),
            title=data['title'],
            content=data['content'],
            category=data.get('category'),
            subcategory=data.get('subcategory'),
            tags=data.get('tags', []),
            source_type=data.get('source_type', 'manual'),
            source_url=data.get('source_url'),
            source_file_path=data.get('source_file_path'),
            platform=data.get('platform')
        )
        
        # Process content for embeddings and keywords
        processed_data = intelligence_service.process_knowledge_content(data['content'])
        knowledge.processed_content = processed_data.get('processed_content')
        knowledge.embeddings = processed_data.get('embeddings')
        knowledge.keywords = processed_data.get('keywords')
        
        db.session.add(knowledge)
        db.session.commit()
        
        return jsonify({
            'message': 'Knowledge entry created successfully',
            'knowledge': knowledge.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/knowledge/<knowledge_id>', methods=['GET'])
def get_knowledge_entry(knowledge_id):
    """Get a specific knowledge base entry"""
    try:
        knowledge = KnowledgeBase.query.filter_by(knowledge_id=knowledge_id).first()
        
        if not knowledge:
            return jsonify({'error': 'Knowledge entry not found'}), 404
        
        # Update usage statistics
        knowledge.usage_count += 1
        knowledge.last_used = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'knowledge': knowledge.to_dict()})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/knowledge/search', methods=['POST'])
def search_knowledge():
    """Search knowledge base"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Search knowledge base
        search_results = intelligence_service.search_knowledge_base(
            data['query'],
            data.get('filters', {}),
            data.get('limit', 10)
        )
        
        return jsonify(search_results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/recommendations', methods=['POST'])
def get_recommendations():
    """Get intelligent recommendations"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Get recommendations
        recommendations = intelligence_service.get_intelligent_recommendations(
            data.get('context', {}),
            data.get('recommendation_types', []),
            data.get('limit', 5)
        )
        
        return jsonify(recommendations)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/validate/business-rules', methods=['POST'])
def validate_business_rules():
    """Validate data against business rules"""
    try:
        data = request.get_json()
        
        if not data or 'data' not in data:
            return jsonify({'error': 'Data to validate is required'}), 400
        
        # Validate business rules
        validation_result = intelligence_service.validate_business_rules(
            data['data'],
            data.get('template_id'),
            data.get('platform'),
            data.get('rule_types', [])
        )
        
        return jsonify(validation_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/optimize/transformation', methods=['POST'])
def optimize_transformation():
    """Optimize transformation using AI"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Optimize transformation
        optimization_result = intelligence_service.optimize_transformation_with_ai(
            data.get('mapping_id'),
            data.get('historical_data', []),
            data.get('performance_metrics', {}),
            data.get('optimization_goals', [])
        )
        
        return jsonify(optimization_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/feedback', methods=['POST'])
def process_feedback():
    """Process user feedback for learning"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Feedback data is required'}), 400
        
        # Process feedback
        feedback_result = intelligence_service.process_user_feedback(
            data.get('feedback_type'),
            data.get('feedback_data', {}),
            data.get('context', {})
        )
        
        return jsonify(feedback_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/insights', methods=['GET'])
def get_insights():
    """Get intelligent insights about transformations"""
    try:
        time_period = request.args.get('period', 'week')  # day, week, month
        insight_types = request.args.getlist('types')  # performance, quality, patterns
        
        # Get insights
        insights = intelligence_service.get_transformation_insights(
            time_period,
            insight_types
        )
        
        return jsonify(insights)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/auto-improve', methods=['POST'])
def auto_improve_mappings():
    """Automatically improve mappings based on performance data"""
    try:
        data = request.get_json()
        
        # Auto-improve mappings
        improvement_result = intelligence_service.auto_improve_mappings(
            data.get('mapping_ids', []),
            data.get('improvement_criteria', {}),
            data.get('options', {})
        )
        
        return jsonify(improvement_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/explain', methods=['POST'])
def explain_transformation():
    """Explain why certain transformation decisions were made"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Explain transformation
        explanation = intelligence_service.explain_transformation_decisions(
            data.get('transformation_id'),
            data.get('mapping_id'),
            data.get('specific_fields', [])
        )
        
        return jsonify(explanation)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/confidence/score', methods=['POST'])
def calculate_confidence_score():
    """Calculate confidence score for a transformation"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Calculate confidence score
        confidence_result = intelligence_service.calculate_transformation_confidence(
            data.get('mapping_id'),
            data.get('source_data'),
            data.get('context', {})
        )
        
        return jsonify(confidence_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/rules/generate', methods=['POST'])
def generate_rules():
    """Generate intelligence rules from data patterns"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Generate rules
        generation_result = intelligence_service.generate_rules_from_patterns(
            data.get('pattern_data', []),
            data.get('rule_types', []),
            data.get('options', {})
        )
        
        return jsonify(generation_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@intelligence_bp.route('/health/intelligence', methods=['GET'])
def get_intelligence_health():
    """Get intelligence system health and performance metrics"""
    try:
        # Get intelligence health
        health_data = intelligence_service.get_intelligence_system_health()
        
        return jsonify(health_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

