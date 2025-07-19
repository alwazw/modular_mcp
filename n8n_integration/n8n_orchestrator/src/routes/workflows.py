"""
Workflows routes for n8n Integration Service
"""

import uuid
import json
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify
from src.models.orchestrator import db, Workflow, WorkflowExecution

workflows_bp = Blueprint('workflows', __name__)

@workflows_bp.route('/', methods=['GET'])
def list_workflows():
    """List all workflows"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status')
        
        query = Workflow.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        workflows = query.order_by(Workflow.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'workflows': [workflow.to_dict() for workflow in workflows.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': workflows.total,
                'pages': workflows.pages
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflows_bp.route('/', methods=['POST'])
def create_workflow():
    """Create a new workflow"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # Create workflow
        workflow = Workflow(
            workflow_id=str(uuid.uuid4()),
            name=data['name'],
            description=data.get('description', ''),
            n8n_workflow_id=data.get('n8n_workflow_id'),
            workflow_definition=json.dumps(data.get('workflow_definition', {})),
            status=data.get('status', 'active')
        )
        
        db.session.add(workflow)
        db.session.commit()
        
        return jsonify({
            'message': 'Workflow created successfully',
            'workflow': workflow.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflows_bp.route('/<workflow_id>', methods=['GET'])
def get_workflow(workflow_id):
    """Get a specific workflow"""
    try:
        workflow = Workflow.query.filter_by(workflow_id=workflow_id).first()
        
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404
        
        return jsonify({'workflow': workflow.to_dict()})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflows_bp.route('/<workflow_id>', methods=['PUT'])
def update_workflow(workflow_id):
    """Update a workflow"""
    try:
        workflow = Workflow.query.filter_by(workflow_id=workflow_id).first()
        
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Update workflow fields
        updatable_fields = ['name', 'description', 'n8n_workflow_id', 'status']
        
        for field in updatable_fields:
            if field in data:
                setattr(workflow, field, data[field])
        
        if 'workflow_definition' in data:
            workflow.workflow_definition = json.dumps(data['workflow_definition'])
        
        workflow.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Workflow updated successfully',
            'workflow': workflow.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflows_bp.route('/<workflow_id>', methods=['DELETE'])
def delete_workflow(workflow_id):
    """Delete a workflow"""
    try:
        workflow = Workflow.query.filter_by(workflow_id=workflow_id).first()
        
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404
        
        db.session.delete(workflow)
        db.session.commit()
        
        return jsonify({'message': 'Workflow deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflows_bp.route('/<workflow_id>/execute', methods=['POST'])
def execute_workflow(workflow_id):
    """Execute a workflow"""
    try:
        workflow = Workflow.query.filter_by(workflow_id=workflow_id).first()
        
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404
        
        if workflow.status != 'active':
            return jsonify({'error': 'Workflow is not active'}), 400
        
        data = request.get_json()
        trigger_data = data.get('trigger_data', {}) if data else {}
        
        # Create execution record
        execution = WorkflowExecution(
            execution_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            trigger_type='manual',
            trigger_data=json.dumps(trigger_data),
            status='running'
        )
        
        db.session.add(execution)
        db.session.commit()
        
        # Execute workflow logic here
        # This is a placeholder - in a real implementation, this would trigger n8n
        try:
            # Simulate workflow execution
            execution_result = {
                'status': 'success',
                'message': 'Workflow executed successfully',
                'data': trigger_data
            }
            
            execution.status = 'success'
            execution.execution_data = json.dumps(execution_result)
            execution.completed_at = datetime.utcnow()
            execution.execution_time_seconds = (execution.completed_at - execution.started_at).total_seconds()
            
        except Exception as e:
            execution.status = 'error'
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            execution.execution_time_seconds = (execution.completed_at - execution.started_at).total_seconds()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Workflow execution started',
            'execution': execution.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflows_bp.route('/<workflow_id>/executions', methods=['GET'])
def get_workflow_executions(workflow_id):
    """Get workflow executions"""
    try:
        workflow = Workflow.query.filter_by(workflow_id=workflow_id).first()
        
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status')
        
        query = WorkflowExecution.query.filter_by(workflow_id=workflow_id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        executions = query.order_by(WorkflowExecution.started_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'executions': [execution.to_dict() for execution in executions.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': executions.total,
                'pages': executions.pages
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflows_bp.route('/executions/<execution_id>', methods=['GET'])
def get_execution(execution_id):
    """Get a specific execution"""
    try:
        execution = WorkflowExecution.query.filter_by(execution_id=execution_id).first()
        
        if not execution:
            return jsonify({'error': 'Execution not found'}), 404
        
        return jsonify({'execution': execution.to_dict()})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflows_bp.route('/executions/<execution_id>/cancel', methods=['POST'])
def cancel_execution(execution_id):
    """Cancel a running execution"""
    try:
        execution = WorkflowExecution.query.filter_by(execution_id=execution_id).first()
        
        if not execution:
            return jsonify({'error': 'Execution not found'}), 404
        
        if execution.status != 'running':
            return jsonify({'error': 'Execution is not running'}), 400
        
        execution.status = 'cancelled'
        execution.completed_at = datetime.utcnow()
        execution.error_message = 'Cancelled by user'
        execution.execution_time_seconds = (execution.completed_at - execution.started_at).total_seconds()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Execution cancelled successfully',
            'execution': execution.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflows_bp.route('/templates', methods=['GET'])
def get_workflow_templates():
    """Get predefined workflow templates"""
    try:
        templates = [
            {
                'id': 'web_scraping_pipeline',
                'name': 'Web Scraping Pipeline',
                'description': 'Complete pipeline for web scraping, processing, and storage',
                'category': 'data_collection',
                'agents_used': ['agent1_scraper', 'agent2_knowledge', 'agent3_database'],
                'workflow_definition': {
                    'nodes': [
                        {
                            'id': 'trigger',
                            'type': 'webhook',
                            'name': 'Webhook Trigger',
                            'parameters': {
                                'path': '/scrape',
                                'method': 'POST'
                            }
                        },
                        {
                            'id': 'scraper',
                            'type': 'agent_call',
                            'name': 'Web Scraper',
                            'parameters': {
                                'agent_id': 'agent1_scraper',
                                'endpoint': '/api/scraper/scrape',
                                'method': 'POST'
                            }
                        },
                        {
                            'id': 'knowledge',
                            'type': 'agent_call',
                            'name': 'Create Knowledge Base',
                            'parameters': {
                                'agent_id': 'agent2_knowledge',
                                'endpoint': '/api/knowledge/create',
                                'method': 'POST'
                            }
                        },
                        {
                            'id': 'storage',
                            'type': 'agent_call',
                            'name': 'Store Data',
                            'parameters': {
                                'agent_id': 'agent3_database',
                                'endpoint': '/api/database/store',
                                'method': 'POST'
                            }
                        }
                    ],
                    'connections': [
                        {'from': 'trigger', 'to': 'scraper'},
                        {'from': 'scraper', 'to': 'knowledge'},
                        {'from': 'knowledge', 'to': 'storage'}
                    ]
                }
            },
            {
                'id': 'data_transformation_pipeline',
                'name': 'Data Transformation Pipeline',
                'description': 'Transform data between different formats (e.g., BestBuy to Walmart)',
                'category': 'data_transformation',
                'agents_used': ['agent4_transformer', 'agent3_database'],
                'workflow_definition': {
                    'nodes': [
                        {
                            'id': 'trigger',
                            'type': 'webhook',
                            'name': 'Data Input',
                            'parameters': {
                                'path': '/transform',
                                'method': 'POST'
                            }
                        },
                        {
                            'id': 'transformer',
                            'type': 'agent_call',
                            'name': 'Transform Data',
                            'parameters': {
                                'agent_id': 'agent4_transformer',
                                'endpoint': '/api/transformer/transform',
                                'method': 'POST'
                            }
                        },
                        {
                            'id': 'storage',
                            'type': 'agent_call',
                            'name': 'Store Results',
                            'parameters': {
                                'agent_id': 'agent3_database',
                                'endpoint': '/api/database/store',
                                'method': 'POST'
                            }
                        }
                    ],
                    'connections': [
                        {'from': 'trigger', 'to': 'transformer'},
                        {'from': 'transformer', 'to': 'storage'}
                    ]
                }
            },
            {
                'id': 'full_data_pipeline',
                'name': 'Complete Data Processing Pipeline',
                'description': 'End-to-end pipeline: scrape, process, transform, and store',
                'category': 'complete_pipeline',
                'agents_used': ['agent1_scraper', 'agent2_knowledge', 'agent4_transformer', 'agent3_database'],
                'workflow_definition': {
                    'nodes': [
                        {
                            'id': 'trigger',
                            'type': 'webhook',
                            'name': 'Pipeline Trigger',
                            'parameters': {
                                'path': '/pipeline',
                                'method': 'POST'
                            }
                        },
                        {
                            'id': 'scraper',
                            'type': 'agent_call',
                            'name': 'Collect Data',
                            'parameters': {
                                'agent_id': 'agent1_scraper',
                                'endpoint': '/api/scraper/scrape',
                                'method': 'POST'
                            }
                        },
                        {
                            'id': 'knowledge',
                            'type': 'agent_call',
                            'name': 'Process Knowledge',
                            'parameters': {
                                'agent_id': 'agent2_knowledge',
                                'endpoint': '/api/knowledge/create',
                                'method': 'POST'
                            }
                        },
                        {
                            'id': 'transformer',
                            'type': 'agent_call',
                            'name': 'Transform Data',
                            'parameters': {
                                'agent_id': 'agent4_transformer',
                                'endpoint': '/api/transformer/transform',
                                'method': 'POST'
                            }
                        },
                        {
                            'id': 'storage',
                            'type': 'agent_call',
                            'name': 'Final Storage',
                            'parameters': {
                                'agent_id': 'agent3_database',
                                'endpoint': '/api/database/store',
                                'method': 'POST'
                            }
                        }
                    ],
                    'connections': [
                        {'from': 'trigger', 'to': 'scraper'},
                        {'from': 'scraper', 'to': 'knowledge'},
                        {'from': 'knowledge', 'to': 'transformer'},
                        {'from': 'transformer', 'to': 'storage'}
                    ]
                }
            }
        ]
        
        return jsonify({'templates': templates})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflows_bp.route('/templates/<template_id>/create', methods=['POST'])
def create_workflow_from_template(template_id):
    """Create a workflow from a template"""
    try:
        data = request.get_json()
        
        # Get template (this would normally be from a database)
        templates = {
            'web_scraping_pipeline': {
                'name': 'Web Scraping Pipeline',
                'description': 'Complete pipeline for web scraping, processing, and storage',
                'workflow_definition': {
                    'nodes': [
                        {'id': 'trigger', 'type': 'webhook', 'name': 'Webhook Trigger'},
                        {'id': 'scraper', 'type': 'agent_call', 'name': 'Web Scraper'},
                        {'id': 'knowledge', 'type': 'agent_call', 'name': 'Create Knowledge Base'},
                        {'id': 'storage', 'type': 'agent_call', 'name': 'Store Data'}
                    ]
                }
            },
            'data_transformation_pipeline': {
                'name': 'Data Transformation Pipeline',
                'description': 'Transform data between different formats',
                'workflow_definition': {
                    'nodes': [
                        {'id': 'trigger', 'type': 'webhook', 'name': 'Data Input'},
                        {'id': 'transformer', 'type': 'agent_call', 'name': 'Transform Data'},
                        {'id': 'storage', 'type': 'agent_call', 'name': 'Store Results'}
                    ]
                }
            }
        }
        
        template = templates.get(template_id)
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        # Create workflow from template
        workflow_name = data.get('name', template['name'])
        workflow_description = data.get('description', template['description'])
        
        workflow = Workflow(
            workflow_id=str(uuid.uuid4()),
            name=workflow_name,
            description=workflow_description,
            workflow_definition=json.dumps(template['workflow_definition']),
            status='active'
        )
        
        db.session.add(workflow)
        db.session.commit()
        
        return jsonify({
            'message': 'Workflow created from template successfully',
            'workflow': workflow.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@workflows_bp.route('/statistics', methods=['GET'])
def get_workflow_statistics():
    """Get workflow statistics"""
    try:
        total_workflows = Workflow.query.count()
        active_workflows = Workflow.query.filter_by(status='active').count()
        
        total_executions = WorkflowExecution.query.count()
        successful_executions = WorkflowExecution.query.filter_by(status='success').count()
        failed_executions = WorkflowExecution.query.filter_by(status='error').count()
        running_executions = WorkflowExecution.query.filter_by(status='running').count()
        
        # Calculate average execution time
        completed_executions = WorkflowExecution.query.filter(
            WorkflowExecution.execution_time_seconds.isnot(None)
        ).all()
        
        avg_execution_time = 0
        if completed_executions:
            avg_execution_time = sum([e.execution_time_seconds for e in completed_executions]) / len(completed_executions)
        
        statistics = {
            'workflows': {
                'total': total_workflows,
                'active': active_workflows,
                'inactive': total_workflows - active_workflows
            },
            'executions': {
                'total': total_executions,
                'successful': successful_executions,
                'failed': failed_executions,
                'running': running_executions,
                'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0
            },
            'performance': {
                'average_execution_time_seconds': round(avg_execution_time, 2)
            }
        }
        
        return jsonify({'statistics': statistics})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

