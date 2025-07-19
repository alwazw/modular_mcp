"""
Webhooks routes for n8n Integration Service
"""

import uuid
import json
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify
from src.models.orchestrator import db, Webhook, WebhookCall, Workflow, WorkflowExecution, Agent

webhooks_bp = Blueprint('webhooks', __name__)

@webhooks_bp.route('/', methods=['GET'])
def list_webhooks():
    """List all webhooks"""
    try:
        webhooks = Webhook.query.filter_by(is_active=True).all()
        
        return jsonify({
            'webhooks': [webhook.to_dict() for webhook in webhooks],
            'total': len(webhooks)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/', methods=['POST'])
def create_webhook():
    """Create a new webhook"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['name', 'endpoint_path']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Check if endpoint path already exists
        existing_webhook = Webhook.query.filter_by(endpoint_path=data['endpoint_path']).first()
        if existing_webhook:
            return jsonify({'error': 'Endpoint path already exists'}), 409
        
        # Create webhook
        webhook = Webhook(
            webhook_id=str(uuid.uuid4()),
            name=data['name'],
            description=data.get('description', ''),
            endpoint_path=data['endpoint_path'],
            workflow_id=data.get('workflow_id'),
            method=data.get('method', 'POST'),
            authentication_type=data.get('authentication_type', 'none'),
            authentication_config=json.dumps(data.get('authentication_config', {}))
        )
        
        db.session.add(webhook)
        db.session.commit()
        
        return jsonify({
            'message': 'Webhook created successfully',
            'webhook': webhook.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/<webhook_id>', methods=['GET'])
def get_webhook(webhook_id):
    """Get a specific webhook"""
    try:
        webhook = Webhook.query.filter_by(webhook_id=webhook_id).first()
        
        if not webhook:
            return jsonify({'error': 'Webhook not found'}), 404
        
        return jsonify({'webhook': webhook.to_dict()})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/<webhook_id>', methods=['PUT'])
def update_webhook(webhook_id):
    """Update a webhook"""
    try:
        webhook = Webhook.query.filter_by(webhook_id=webhook_id).first()
        
        if not webhook:
            return jsonify({'error': 'Webhook not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Update webhook fields
        updatable_fields = [
            'name', 'description', 'endpoint_path', 'workflow_id',
            'method', 'authentication_type', 'is_active'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(webhook, field, data[field])
        
        if 'authentication_config' in data:
            webhook.authentication_config = json.dumps(data['authentication_config'])
        
        webhook.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Webhook updated successfully',
            'webhook': webhook.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/<webhook_id>', methods=['DELETE'])
def delete_webhook(webhook_id):
    """Delete a webhook"""
    try:
        webhook = Webhook.query.filter_by(webhook_id=webhook_id).first()
        
        if not webhook:
            return jsonify({'error': 'Webhook not found'}), 404
        
        webhook.is_active = False
        webhook.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Webhook deactivated successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Dynamic webhook endpoints
@webhooks_bp.route('/trigger/<path:endpoint_path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def trigger_webhook(endpoint_path):
    """Dynamic webhook trigger endpoint"""
    try:
        # Find webhook by endpoint path
        webhook = Webhook.query.filter_by(
            endpoint_path=f"/{endpoint_path}",
            is_active=True
        ).first()
        
        if not webhook:
            return jsonify({'error': 'Webhook not found'}), 404
        
        # Check method
        if webhook.method != request.method:
            return jsonify({'error': f'Method {request.method} not allowed'}), 405
        
        # Authenticate if required
        auth_result = _authenticate_webhook(webhook, request)
        if not auth_result['success']:
            return jsonify({'error': auth_result['error']}), 401
        
        # Create webhook call record
        call = WebhookCall(
            call_id=str(uuid.uuid4()),
            webhook_id=webhook.webhook_id,
            method=request.method,
            headers=json.dumps(dict(request.headers)),
            query_params=json.dumps(dict(request.args)),
            body_data=json.dumps(request.get_json()) if request.is_json else request.get_data(as_text=True),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        db.session.add(call)
        db.session.flush()  # Get the call ID
        
        try:
            # Execute associated workflow if configured
            if webhook.workflow_id:
                execution_result = _execute_webhook_workflow(webhook, call, request)
                call.execution_id = execution_result.get('execution_id')
                call.response_status = 200
                call.response_data = json.dumps(execution_result)
                
                db.session.commit()
                
                return jsonify(execution_result)
            else:
                # No workflow configured, just return success
                response_data = {
                    'success': True,
                    'message': 'Webhook received successfully',
                    'call_id': call.call_id,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                call.response_status = 200
                call.response_data = json.dumps(response_data)
                
                db.session.commit()
                
                return jsonify(response_data)
                
        except Exception as e:
            call.response_status = 500
            call.response_data = json.dumps({'error': str(e)})
            db.session.commit()
            
            return jsonify({'error': str(e)}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _authenticate_webhook(webhook, request):
    """Authenticate webhook request"""
    try:
        if webhook.authentication_type == 'none':
            return {'success': True}
        
        auth_config = json.loads(webhook.authentication_config) if webhook.authentication_config else {}
        
        if webhook.authentication_type == 'api_key':
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            expected_key = auth_config.get('api_key')
            
            if not api_key or api_key != expected_key:
                return {'success': False, 'error': 'Invalid API key'}
        
        elif webhook.authentication_type == 'basic':
            auth = request.authorization
            if not auth:
                return {'success': False, 'error': 'Basic authentication required'}
            
            expected_username = auth_config.get('username')
            expected_password = auth_config.get('password')
            
            if auth.username != expected_username or auth.password != expected_password:
                return {'success': False, 'error': 'Invalid credentials'}
        
        elif webhook.authentication_type == 'bearer':
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return {'success': False, 'error': 'Bearer token required'}
            
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            expected_token = auth_config.get('token')
            
            if token != expected_token:
                return {'success': False, 'error': 'Invalid bearer token'}
        
        return {'success': True}
        
    except Exception as e:
        return {'success': False, 'error': f'Authentication error: {str(e)}'}

def _execute_webhook_workflow(webhook, call, request):
    """Execute workflow associated with webhook"""
    try:
        workflow = Workflow.query.filter_by(workflow_id=webhook.workflow_id).first()
        if not workflow:
            raise Exception('Associated workflow not found')
        
        if workflow.status != 'active':
            raise Exception('Associated workflow is not active')
        
        # Prepare trigger data
        trigger_data = {
            'webhook_data': {
                'headers': dict(request.headers),
                'query_params': dict(request.args),
                'body': request.get_json() if request.is_json else request.get_data(as_text=True)
            },
            'call_id': call.call_id,
            'webhook_id': webhook.webhook_id
        }
        
        # Create workflow execution
        execution = WorkflowExecution(
            execution_id=str(uuid.uuid4()),
            workflow_id=workflow.workflow_id,
            trigger_type='webhook',
            trigger_data=json.dumps(trigger_data),
            status='running'
        )
        
        db.session.add(execution)
        db.session.flush()
        
        # Execute workflow steps
        workflow_definition = json.loads(workflow.workflow_definition) if workflow.workflow_definition else {}
        execution_result = _process_workflow_nodes(workflow_definition, trigger_data, execution.execution_id)
        
        # Update execution with results
        execution.status = 'success' if execution_result['success'] else 'error'
        execution.execution_data = json.dumps(execution_result)
        execution.completed_at = datetime.utcnow()
        execution.execution_time_seconds = (execution.completed_at - execution.started_at).total_seconds()
        
        if not execution_result['success']:
            execution.error_message = execution_result.get('error', 'Unknown error')
        
        return {
            'success': execution_result['success'],
            'execution_id': execution.execution_id,
            'workflow_id': workflow.workflow_id,
            'message': 'Workflow executed successfully' if execution_result['success'] else 'Workflow execution failed',
            'data': execution_result.get('data', {}),
            'error': execution_result.get('error') if not execution_result['success'] else None
        }
        
    except Exception as e:
        raise Exception(f'Workflow execution failed: {str(e)}')

def _process_workflow_nodes(workflow_definition, trigger_data, execution_id):
    """Process workflow nodes"""
    try:
        nodes = workflow_definition.get('nodes', [])
        connections = workflow_definition.get('connections', [])
        
        if not nodes:
            return {'success': True, 'data': trigger_data, 'message': 'No nodes to process'}
        
        # Simple sequential processing (in a real implementation, this would handle complex flows)
        current_data = trigger_data
        results = {}
        
        for node in nodes:
            if node.get('type') == 'webhook':
                # Skip webhook trigger node
                results[node['id']] = {'success': True, 'data': current_data}
                continue
            
            elif node.get('type') == 'agent_call':
                # Call agent endpoint
                agent_result = _call_agent_node(node, current_data, execution_id)
                results[node['id']] = agent_result
                
                if not agent_result['success']:
                    return {
                        'success': False,
                        'error': f"Node {node['id']} failed: {agent_result.get('error', 'Unknown error')}",
                        'results': results
                    }
                
                current_data = agent_result.get('data', current_data)
            
            else:
                # Unknown node type, skip
                results[node['id']] = {'success': True, 'data': current_data, 'message': f"Skipped unknown node type: {node.get('type')}"}
        
        return {
            'success': True,
            'data': current_data,
            'results': results,
            'message': 'Workflow completed successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'results': {}
        }

def _call_agent_node(node, data, execution_id):
    """Call an agent node"""
    try:
        parameters = node.get('parameters', {})
        agent_id = parameters.get('agent_id')
        endpoint = parameters.get('endpoint')
        method = parameters.get('method', 'POST')
        
        if not agent_id or not endpoint:
            return {'success': False, 'error': 'Agent ID and endpoint are required'}
        
        # Get agent information
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        if not agent:
            return {'success': False, 'error': f'Agent {agent_id} not found'}
        
        if agent.status != 'healthy':
            return {'success': False, 'error': f'Agent {agent_id} is not healthy'}
        
        # Prepare request
        url = f"{agent.base_url.rstrip('/')}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Make request to agent
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=30)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=headers, timeout=30)
        else:
            return {'success': False, 'error': f'Unsupported method: {method}'}
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                return {'success': True, 'data': response_data}
            except:
                return {'success': True, 'data': {'response': response.text}}
        else:
            return {
                'success': False,
                'error': f'Agent call failed with status {response.status_code}: {response.text}'
            }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

@webhooks_bp.route('/<webhook_id>/calls', methods=['GET'])
def get_webhook_calls(webhook_id):
    """Get webhook call history"""
    try:
        webhook = Webhook.query.filter_by(webhook_id=webhook_id).first()
        
        if not webhook:
            return jsonify({'error': 'Webhook not found'}), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        calls = WebhookCall.query.filter_by(webhook_id=webhook_id).order_by(
            WebhookCall.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'calls': [call.to_dict() for call in calls.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': calls.total,
                'pages': calls.pages
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/calls/<call_id>', methods=['GET'])
def get_webhook_call(call_id):
    """Get specific webhook call details"""
    try:
        call = WebhookCall.query.filter_by(call_id=call_id).first()
        
        if not call:
            return jsonify({'error': 'Webhook call not found'}), 404
        
        return jsonify({'call': call.to_dict()})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/test/<webhook_id>', methods=['POST'])
def test_webhook(webhook_id):
    """Test a webhook with sample data"""
    try:
        webhook = Webhook.query.filter_by(webhook_id=webhook_id).first()
        
        if not webhook:
            return jsonify({'error': 'Webhook not found'}), 404
        
        data = request.get_json()
        test_data = data.get('test_data', {}) if data else {}
        
        # Simulate webhook call
        test_result = {
            'webhook_id': webhook_id,
            'test_successful': True,
            'endpoint_path': webhook.endpoint_path,
            'method': webhook.method,
            'test_data': test_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if webhook.workflow_id:
            test_result['workflow_id'] = webhook.workflow_id
            test_result['message'] = 'Webhook test successful - would trigger workflow'
        else:
            test_result['message'] = 'Webhook test successful - no workflow configured'
        
        return jsonify(test_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

