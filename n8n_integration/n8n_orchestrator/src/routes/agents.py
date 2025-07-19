"""
Agents routes for n8n Integration Service
"""

import uuid
import json
import requests
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from src.models.orchestrator import db, Agent, AgentTask

agents_bp = Blueprint('agents', __name__)

@agents_bp.route('/', methods=['GET'])
def list_agents():
    """List all agents with their status"""
    try:
        agents = Agent.query.all()
        
        agent_list = []
        for agent in agents:
            agent_dict = agent.to_dict()
            
            # Add recent task statistics
            recent_tasks = AgentTask.query.filter(
                AgentTask.agent_id == agent.agent_id,
                AgentTask.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).all()
            
            agent_dict['recent_stats'] = {
                'total_tasks_24h': len(recent_tasks),
                'completed_tasks_24h': len([t for t in recent_tasks if t.status == 'completed']),
                'failed_tasks_24h': len([t for t in recent_tasks if t.status == 'failed']),
                'running_tasks': len([t for t in recent_tasks if t.status == 'running'])
            }
            
            agent_list.append(agent_dict)
        
        return jsonify({
            'agents': agent_list,
            'total': len(agents)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agents_bp.route('/<agent_id>/tasks', methods=['POST'])
def create_agent_task(agent_id):
    """Create a new task for an agent"""
    try:
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['task_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Create task
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            agent_id=agent_id,
            execution_id=data.get('execution_id'),
            task_type=data['task_type'],
            task_data=json.dumps(data.get('task_data', {})),
            status='pending'
        )
        
        db.session.add(task)
        db.session.commit()
        
        # Execute task immediately if requested
        if data.get('execute_immediately', False):
            execution_result = _execute_agent_task(task)
            return jsonify({
                'message': 'Task created and executed',
                'task': task.to_dict(),
                'execution_result': execution_result
            }), 201
        
        return jsonify({
            'message': 'Task created successfully',
            'task': task.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agents_bp.route('/<agent_id>/tasks', methods=['GET'])
def get_agent_tasks(agent_id):
    """Get tasks for a specific agent"""
    try:
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status')
        
        query = AgentTask.query.filter_by(agent_id=agent_id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        tasks = query.order_by(AgentTask.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'tasks': [task.to_dict() for task in tasks.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': tasks.total,
                'pages': tasks.pages
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agents_bp.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """Get a specific task"""
    try:
        task = AgentTask.query.filter_by(task_id=task_id).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        return jsonify({'task': task.to_dict()})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agents_bp.route('/tasks/<task_id>/execute', methods=['POST'])
def execute_task(task_id):
    """Execute a pending task"""
    try:
        task = AgentTask.query.filter_by(task_id=task_id).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        if task.status != 'pending':
            return jsonify({'error': 'Task is not in pending status'}), 400
        
        execution_result = _execute_agent_task(task)
        
        return jsonify({
            'message': 'Task executed',
            'task': task.to_dict(),
            'execution_result': execution_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _execute_agent_task(task):
    """Execute an agent task"""
    try:
        agent = Agent.query.filter_by(agent_id=task.agent_id).first()
        if not agent:
            raise Exception('Agent not found')
        
        # Update task status
        task.status = 'running'
        task.started_at = datetime.utcnow()
        db.session.commit()
        
        # Prepare task data
        task_data = json.loads(task.task_data) if task.task_data else {}
        
        # Route task based on task type and agent type
        result = _route_agent_task(agent, task.task_type, task_data)
        
        # Update task with results
        if result['success']:
            task.status = 'completed'
            task.result_data = json.dumps(result.get('data', {}))
        else:
            task.status = 'failed'
            task.error_message = result.get('error', 'Unknown error')
        
        task.completed_at = datetime.utcnow()
        task.execution_time_seconds = (task.completed_at - task.started_at).total_seconds()
        
        db.session.commit()
        
        return result
        
    except Exception as e:
        task.status = 'failed'
        task.error_message = str(e)
        task.completed_at = datetime.utcnow()
        if task.started_at:
            task.execution_time_seconds = (task.completed_at - task.started_at).total_seconds()
        db.session.commit()
        
        return {'success': False, 'error': str(e)}

def _route_agent_task(agent, task_type, task_data):
    """Route task to appropriate agent endpoint"""
    try:
        # Define task routing based on agent type and task type
        routing_map = {
            'scraper': {
                'scrape_url': '/api/scraper/scrape',
                'upload_file': '/api/files/upload',
                'create_session': '/api/sessions/',
                'get_scraped_data': '/api/scraper/jobs'
            },
            'knowledge': {
                'create_knowledge_base': '/api/knowledge/bases',
                'process_document': '/api/documents/',
                'search_knowledge': '/api/knowledge/search',
                'generate_embeddings': '/api/embeddings/'
            },
            'database': {
                'store_data': '/api/database/',
                'create_backup': '/api/backup/',
                'sync_data': '/api/sync/',
                'get_analytics': '/api/analytics/'
            },
            'transformer': {
                'transform_data': '/api/transformer/transform',
                'create_mapping': '/api/mappings/',
                'analyze_template': '/api/templates/',
                'validate_data': '/api/transformer/validate'
            }
        }
        
        agent_routes = routing_map.get(agent.agent_type, {})
        endpoint = agent_routes.get(task_type)
        
        if not endpoint:
            return {
                'success': False,
                'error': f'Task type {task_type} not supported for agent type {agent.agent_type}'
            }
        
        # Make request to agent
        url = f"{agent.base_url.rstrip('/')}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(url, json=task_data, headers=headers, timeout=60)
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    return {'success': True, 'data': response_data}
                except:
                    return {'success': True, 'data': {'response': response.text}}
            else:
                return {
                    'success': False,
                    'error': f'Agent request failed with status {response.status_code}: {response.text}'
                }
                
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Agent request timed out'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Could not connect to agent'}
        except Exception as e:
            return {'success': False, 'error': f'Request error: {str(e)}'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

@agents_bp.route('/<agent_id>/call', methods=['POST'])
def call_agent_directly(agent_id):
    """Make a direct call to an agent"""
    try:
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['endpoint', 'method']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} is required'}), 400
        
        endpoint = data['endpoint']
        method = data['method'].upper()
        payload = data.get('payload', {})
        
        # Make request to agent
        url = f"{agent.base_url.rstrip('/')}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=payload, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=payload, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return jsonify({'error': f'Unsupported method: {method}'}), 400
            
            # Return response
            result = {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'agent_id': agent_id,
                'endpoint': endpoint,
                'method': method
            }
            
            try:
                result['data'] = response.json()
            except:
                result['data'] = response.text
            
            return jsonify(result)
            
        except requests.exceptions.Timeout:
            return jsonify({'error': 'Agent request timed out'}), 408
        except requests.exceptions.ConnectionError:
            return jsonify({'error': 'Could not connect to agent'}), 503
        except Exception as e:
            return jsonify({'error': f'Request error: {str(e)}'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agents_bp.route('/<agent_id>/capabilities', methods=['GET'])
def get_agent_capabilities(agent_id):
    """Get agent capabilities and available endpoints"""
    try:
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        # Get capabilities from agent configuration
        capabilities = json.loads(agent.capabilities) if agent.capabilities else []
        
        # Define available endpoints based on agent type
        endpoint_map = {
            'scraper': [
                {'endpoint': '/api/scraper/health', 'method': 'GET', 'description': 'Health check'},
                {'endpoint': '/api/scraper/scrape', 'method': 'POST', 'description': 'Scrape URL'},
                {'endpoint': '/api/scraper/jobs', 'method': 'GET', 'description': 'List scraping jobs'},
                {'endpoint': '/api/files/upload', 'method': 'POST', 'description': 'Upload file'},
                {'endpoint': '/api/sessions/', 'method': 'GET', 'description': 'List sessions'}
            ],
            'knowledge': [
                {'endpoint': '/api/knowledge/health', 'method': 'GET', 'description': 'Health check'},
                {'endpoint': '/api/knowledge/bases', 'method': 'GET', 'description': 'List knowledge bases'},
                {'endpoint': '/api/knowledge/bases', 'method': 'POST', 'description': 'Create knowledge base'},
                {'endpoint': '/api/knowledge/search', 'method': 'POST', 'description': 'Search knowledge'},
                {'endpoint': '/api/documents/', 'method': 'POST', 'description': 'Process document'}
            ],
            'database': [
                {'endpoint': '/api/database/health', 'method': 'GET', 'description': 'Health check'},
                {'endpoint': '/api/database/', 'method': 'GET', 'description': 'List connections'},
                {'endpoint': '/api/database/', 'method': 'POST', 'description': 'Create connection'},
                {'endpoint': '/api/backup/', 'method': 'POST', 'description': 'Create backup'},
                {'endpoint': '/api/analytics/', 'method': 'GET', 'description': 'Get analytics'}
            ],
            'transformer': [
                {'endpoint': '/api/transformer/health', 'method': 'GET', 'description': 'Health check'},
                {'endpoint': '/api/transformer/transform', 'method': 'POST', 'description': 'Transform data'},
                {'endpoint': '/api/templates/', 'method': 'GET', 'description': 'List templates'},
                {'endpoint': '/api/mappings/', 'method': 'GET', 'description': 'List mappings'},
                {'endpoint': '/api/intelligence/', 'method': 'GET', 'description': 'AI features'}
            ]
        }
        
        available_endpoints = endpoint_map.get(agent.agent_type, [])
        
        return jsonify({
            'agent_id': agent_id,
            'agent_type': agent.agent_type,
            'capabilities': capabilities,
            'available_endpoints': available_endpoints,
            'base_url': agent.base_url,
            'status': agent.status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agents_bp.route('/<agent_id>/statistics', methods=['GET'])
def get_agent_statistics(agent_id):
    """Get agent performance statistics"""
    try:
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        # Get time range
        days = request.args.get('days', 7, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get tasks in time range
        tasks = AgentTask.query.filter(
            AgentTask.agent_id == agent_id,
            AgentTask.created_at >= start_date
        ).all()
        
        # Calculate statistics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == 'completed'])
        failed_tasks = len([t for t in tasks if t.status == 'failed'])
        running_tasks = len([t for t in tasks if t.status == 'running'])
        pending_tasks = len([t for t in tasks if t.status == 'pending'])
        
        # Calculate average execution time
        completed_with_time = [t for t in tasks if t.status == 'completed' and t.execution_time_seconds]
        avg_execution_time = 0
        if completed_with_time:
            avg_execution_time = sum([t.execution_time_seconds for t in completed_with_time]) / len(completed_with_time)
        
        # Task types breakdown
        task_types = {}
        for task in tasks:
            task_type = task.task_type
            if task_type not in task_types:
                task_types[task_type] = {'total': 0, 'completed': 0, 'failed': 0}
            
            task_types[task_type]['total'] += 1
            if task.status == 'completed':
                task_types[task_type]['completed'] += 1
            elif task.status == 'failed':
                task_types[task_type]['failed'] += 1
        
        statistics = {
            'agent_id': agent_id,
            'time_period_days': days,
            'task_summary': {
                'total': total_tasks,
                'completed': completed_tasks,
                'failed': failed_tasks,
                'running': running_tasks,
                'pending': pending_tasks,
                'success_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            },
            'performance': {
                'average_execution_time_seconds': round(avg_execution_time, 2),
                'total_execution_time_seconds': sum([t.execution_time_seconds or 0 for t in tasks])
            },
            'task_types': task_types,
            'agent_status': agent.status,
            'last_health_check': agent.last_health_check.isoformat() if agent.last_health_check else None
        }
        
        return jsonify({'statistics': statistics})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agents_bp.route('/batch/health-check', methods=['POST'])
def batch_health_check():
    """Perform health check on multiple agents"""
    try:
        data = request.get_json()
        agent_ids = data.get('agent_ids', []) if data else []
        
        if not agent_ids:
            # Check all agents if none specified
            agents = Agent.query.all()
        else:
            agents = Agent.query.filter(Agent.agent_id.in_(agent_ids)).all()
        
        results = {}
        
        for agent in agents:
            try:
                health_url = f"{agent.base_url.rstrip('/')}{agent.health_endpoint}"
                response = requests.get(health_url, timeout=10)
                
                if response.status_code == 200:
                    agent.status = 'healthy'
                    results[agent.agent_id] = {
                        'status': 'healthy',
                        'response_time_ms': response.elapsed.total_seconds() * 1000,
                        'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                    }
                else:
                    agent.status = 'unhealthy'
                    results[agent.agent_id] = {
                        'status': 'unhealthy',
                        'error': f'HTTP {response.status_code}',
                        'response_time_ms': response.elapsed.total_seconds() * 1000
                    }
                    
            except Exception as e:
                agent.status = 'unhealthy'
                results[agent.agent_id] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'response_time_ms': None
                }
            
            agent.last_health_check = datetime.utcnow()
        
        db.session.commit()
        
        # Summary
        healthy_count = len([r for r in results.values() if r['status'] == 'healthy'])
        total_count = len(results)
        
        return jsonify({
            'summary': {
                'total_agents': total_count,
                'healthy_agents': healthy_count,
                'unhealthy_agents': total_count - healthy_count,
                'health_rate': (healthy_count / total_count * 100) if total_count > 0 else 0
            },
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

