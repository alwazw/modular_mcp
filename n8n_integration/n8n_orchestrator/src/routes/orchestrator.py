"""
Orchestrator routes for n8n Integration Service
"""

import uuid
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify
from src.models.orchestrator import db, Agent, Configuration

orchestrator_bp = Blueprint('orchestrator', __name__)

@orchestrator_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'service': 'n8n_orchestrator',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@orchestrator_bp.route('/status', methods=['GET'])
def system_status():
    """Get overall system status"""
    try:
        # Get all registered agents
        agents = Agent.query.all()
        
        system_status = {
            'orchestrator': 'healthy',
            'agents': {},
            'total_agents': len(agents),
            'healthy_agents': 0,
            'unhealthy_agents': 0,
            'unknown_agents': 0
        }
        
        # Check each agent's health
        for agent in agents:
            try:
                health_url = f"{agent.base_url.rstrip('/')}{agent.health_endpoint}"
                response = requests.get(health_url, timeout=5)
                
                if response.status_code == 200:
                    agent.status = 'healthy'
                    system_status['healthy_agents'] += 1
                else:
                    agent.status = 'unhealthy'
                    system_status['unhealthy_agents'] += 1
                    
            except Exception as e:
                agent.status = 'unhealthy'
                system_status['unhealthy_agents'] += 1
            
            agent.last_health_check = datetime.utcnow()
            system_status['agents'][agent.agent_id] = {
                'name': agent.name,
                'type': agent.agent_type,
                'status': agent.status,
                'url': agent.base_url,
                'last_check': agent.last_health_check.isoformat()
            }
        
        # Update database
        db.session.commit()
        
        # Calculate overall health
        if system_status['unhealthy_agents'] == 0:
            system_status['overall_status'] = 'healthy'
        elif system_status['healthy_agents'] > 0:
            system_status['overall_status'] = 'degraded'
        else:
            system_status['overall_status'] = 'unhealthy'
        
        return jsonify(system_status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/agents/register', methods=['POST'])
def register_agent():
    """Register a new agent"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['agent_id', 'name', 'agent_type', 'base_url']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Check if agent already exists
        existing_agent = Agent.query.filter_by(agent_id=data['agent_id']).first()
        if existing_agent:
            return jsonify({'error': 'Agent already registered'}), 409
        
        # Create new agent
        agent = Agent(
            agent_id=data['agent_id'],
            name=data['name'],
            description=data.get('description', ''),
            agent_type=data['agent_type'],
            base_url=data['base_url'],
            health_endpoint=data.get('health_endpoint', '/health'),
            capabilities=data.get('capabilities', '[]'),
            configuration=data.get('configuration', '{}')
        )
        
        db.session.add(agent)
        db.session.commit()
        
        return jsonify({
            'message': 'Agent registered successfully',
            'agent': agent.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/agents', methods=['GET'])
def list_agents():
    """List all registered agents"""
    try:
        agents = Agent.query.all()
        
        return jsonify({
            'agents': [agent.to_dict() for agent in agents],
            'total': len(agents)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/agents/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    """Get specific agent details"""
    try:
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        return jsonify({'agent': agent.to_dict()})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/agents/<agent_id>', methods=['PUT'])
def update_agent(agent_id):
    """Update agent configuration"""
    try:
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Update agent fields
        updatable_fields = [
            'name', 'description', 'base_url', 'health_endpoint',
            'capabilities', 'configuration'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(agent, field, data[field])
        
        agent.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Agent updated successfully',
            'agent': agent.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/agents/<agent_id>', methods=['DELETE'])
def unregister_agent(agent_id):
    """Unregister an agent"""
    try:
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        db.session.delete(agent)
        db.session.commit()
        
        return jsonify({'message': 'Agent unregistered successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/agents/<agent_id>/health', methods=['GET'])
def check_agent_health(agent_id):
    """Check specific agent health"""
    try:
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        try:
            health_url = f"{agent.base_url.rstrip('/')}{agent.health_endpoint}"
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                agent.status = 'healthy'
                health_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            else:
                agent.status = 'unhealthy'
                health_data = {'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            agent.status = 'unhealthy'
            health_data = {'error': str(e)}
        
        agent.last_health_check = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'agent_id': agent_id,
            'status': agent.status,
            'last_check': agent.last_health_check.isoformat(),
            'health_data': health_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/configuration', methods=['GET'])
def get_configuration():
    """Get system configuration"""
    try:
        configs = Configuration.query.all()
        
        config_dict = {}
        for config in configs:
            if config.category not in config_dict:
                config_dict[config.category] = {}
            
            config_dict[config.category][config.key] = {
                'value': config.value if not config.is_encrypted else '[ENCRYPTED]',
                'description': config.description
            }
        
        return jsonify({'configuration': config_dict})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/configuration', methods=['POST'])
def set_configuration():
    """Set configuration value"""
    try:
        data = request.get_json()
        
        if not data or 'key' not in data or 'value' not in data:
            return jsonify({'error': 'Key and value are required'}), 400
        
        config = Configuration.query.filter_by(key=data['key']).first()
        
        if config:
            config.value = data['value']
            config.description = data.get('description', config.description)
            config.category = data.get('category', config.category)
            config.is_encrypted = data.get('is_encrypted', config.is_encrypted)
            config.updated_at = datetime.utcnow()
        else:
            config = Configuration(
                key=data['key'],
                value=data['value'],
                description=data.get('description', ''),
                category=data.get('category', 'general'),
                is_encrypted=data.get('is_encrypted', False)
            )
            db.session.add(config)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Configuration updated successfully',
            'configuration': config.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/configuration/<key>', methods=['DELETE'])
def delete_configuration(key):
    """Delete configuration value"""
    try:
        config = Configuration.query.filter_by(key=key).first()
        
        if not config:
            return jsonify({'error': 'Configuration not found'}), 404
        
        db.session.delete(config)
        db.session.commit()
        
        return jsonify({'message': 'Configuration deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/initialize', methods=['POST'])
def initialize_system():
    """Initialize the orchestrator system with default agents"""
    try:
        # Default agent configurations
        default_agents = [
            {
                'agent_id': 'agent1_scraper',
                'name': 'Web Scraper & Data Collector',
                'description': 'Handles web scraping, file processing, and data collection',
                'agent_type': 'scraper',
                'base_url': 'https://5000-ij16cqdg6torl5w1ld6jw-72e62cc2.manusvm.computer',
                'health_endpoint': '/api/scraper/health',
                'capabilities': '["web_scraping", "file_processing", "session_management", "data_extraction"]'
            },
            {
                'agent_id': 'agent2_knowledge',
                'name': 'Knowledge Base Creator',
                'description': 'Creates and manages knowledge bases from processed data',
                'agent_type': 'knowledge',
                'base_url': 'https://5001-ij16cqdg6torl5w1ld6jw-72e62cc2.manusvm.computer',
                'health_endpoint': '/api/knowledge/health',
                'capabilities': '["knowledge_creation", "document_processing", "embedding_generation", "search"]'
            },
            {
                'agent_id': 'agent3_database',
                'name': 'Database Manager',
                'description': 'Manages databases, backups, and data synchronization',
                'agent_type': 'database',
                'base_url': 'https://5002-ij16cqdg6torl5w1ld6jw-72e62cc2.manusvm.computer',
                'health_endpoint': '/api/database/health',
                'capabilities': '["database_management", "backup_scheduling", "data_sync", "analytics"]'
            },
            {
                'agent_id': 'agent4_transformer',
                'name': 'Intelligent Data Transformer',
                'description': 'Transforms data between different formats using AI',
                'agent_type': 'transformer',
                'base_url': 'https://5003-ij16cqdg6torl5w1ld6jw-72e62cc2.manusvm.computer',
                'health_endpoint': '/api/transformer/health',
                'capabilities': '["data_transformation", "template_mapping", "ai_intelligence", "quality_analysis"]'
            }
        ]
        
        registered_agents = []
        errors = []
        
        for agent_config in default_agents:
            try:
                # Check if agent already exists
                existing_agent = Agent.query.filter_by(agent_id=agent_config['agent_id']).first()
                if existing_agent:
                    # Update existing agent
                    for key, value in agent_config.items():
                        if key != 'agent_id':
                            setattr(existing_agent, key, value)
                    existing_agent.updated_at = datetime.utcnow()
                    registered_agents.append(existing_agent.to_dict())
                else:
                    # Create new agent
                    agent = Agent(**agent_config)
                    db.session.add(agent)
                    registered_agents.append(agent.to_dict())
                    
            except Exception as e:
                errors.append(f"Failed to register {agent_config['agent_id']}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'message': 'System initialized successfully',
            'registered_agents': registered_agents,
            'errors': errors
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orchestrator_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get system metrics"""
    try:
        from src.models.orchestrator import WorkflowExecution, AgentTask, WebhookCall
        
        # Calculate metrics
        total_workflows = db.session.query(WorkflowExecution).count()
        successful_workflows = db.session.query(WorkflowExecution).filter_by(status='success').count()
        failed_workflows = db.session.query(WorkflowExecution).filter_by(status='error').count()
        
        total_tasks = db.session.query(AgentTask).count()
        successful_tasks = db.session.query(AgentTask).filter_by(status='completed').count()
        failed_tasks = db.session.query(AgentTask).filter_by(status='failed').count()
        
        total_webhook_calls = db.session.query(WebhookCall).count()
        
        agents = Agent.query.all()
        healthy_agents = len([a for a in agents if a.status == 'healthy'])
        
        metrics = {
            'workflows': {
                'total': total_workflows,
                'successful': successful_workflows,
                'failed': failed_workflows,
                'success_rate': (successful_workflows / total_workflows * 100) if total_workflows > 0 else 0
            },
            'tasks': {
                'total': total_tasks,
                'successful': successful_tasks,
                'failed': failed_tasks,
                'success_rate': (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
            },
            'agents': {
                'total': len(agents),
                'healthy': healthy_agents,
                'health_rate': (healthy_agents / len(agents) * 100) if len(agents) > 0 else 0
            },
            'webhooks': {
                'total_calls': total_webhook_calls
            }
        }
        
        return jsonify({'metrics': metrics})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

