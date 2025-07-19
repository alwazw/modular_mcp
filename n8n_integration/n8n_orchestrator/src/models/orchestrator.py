"""
Database models for n8n Orchestrator Service
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Workflow(db.Model):
    """n8n Workflow model"""
    __tablename__ = 'workflows'
    
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    n8n_workflow_id = db.Column(db.String(100))  # ID in n8n system
    workflow_definition = db.Column(db.Text)  # JSON workflow definition
    status = db.Column(db.String(50), default='active')  # active, inactive, error
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    executions = db.relationship('WorkflowExecution', backref='workflow', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'name': self.name,
            'description': self.description,
            'n8n_workflow_id': self.n8n_workflow_id,
            'workflow_definition': json.loads(self.workflow_definition) if self.workflow_definition else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class WorkflowExecution(db.Model):
    """Workflow execution tracking"""
    __tablename__ = 'workflow_executions'
    
    id = db.Column(db.Integer, primary_key=True)
    execution_id = db.Column(db.String(100), unique=True, nullable=False)
    workflow_id = db.Column(db.String(100), db.ForeignKey('workflows.workflow_id'), nullable=False)
    n8n_execution_id = db.Column(db.String(100))  # ID in n8n system
    status = db.Column(db.String(50), default='running')  # running, success, error, cancelled
    trigger_type = db.Column(db.String(50))  # webhook, manual, schedule, api
    trigger_data = db.Column(db.Text)  # JSON trigger data
    execution_data = db.Column(db.Text)  # JSON execution results
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    execution_time_seconds = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'execution_id': self.execution_id,
            'workflow_id': self.workflow_id,
            'n8n_execution_id': self.n8n_execution_id,
            'status': self.status,
            'trigger_type': self.trigger_type,
            'trigger_data': json.loads(self.trigger_data) if self.trigger_data else None,
            'execution_data': json.loads(self.execution_data) if self.execution_data else None,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'execution_time_seconds': self.execution_time_seconds
        }

class Agent(db.Model):
    """Agent registration and status"""
    __tablename__ = 'agents'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    agent_type = db.Column(db.String(50), nullable=False)  # scraper, knowledge, database, transformer
    base_url = db.Column(db.String(500), nullable=False)
    health_endpoint = db.Column(db.String(200), default='/health')
    status = db.Column(db.String(50), default='unknown')  # healthy, unhealthy, unknown
    last_health_check = db.Column(db.DateTime)
    capabilities = db.Column(db.Text)  # JSON list of capabilities
    configuration = db.Column(db.Text)  # JSON configuration
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = db.relationship('AgentTask', backref='agent', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'name': self.name,
            'description': self.description,
            'agent_type': self.agent_type,
            'base_url': self.base_url,
            'health_endpoint': self.health_endpoint,
            'status': self.status,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'capabilities': json.loads(self.capabilities) if self.capabilities else [],
            'configuration': json.loads(self.configuration) if self.configuration else {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AgentTask(db.Model):
    """Agent task tracking"""
    __tablename__ = 'agent_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(100), unique=True, nullable=False)
    agent_id = db.Column(db.String(100), db.ForeignKey('agents.agent_id'), nullable=False)
    execution_id = db.Column(db.String(100), db.ForeignKey('workflow_executions.execution_id'))
    task_type = db.Column(db.String(100), nullable=False)
    task_data = db.Column(db.Text)  # JSON task parameters
    status = db.Column(db.String(50), default='pending')  # pending, running, completed, failed
    result_data = db.Column(db.Text)  # JSON task results
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    execution_time_seconds = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'agent_id': self.agent_id,
            'execution_id': self.execution_id,
            'task_type': self.task_type,
            'task_data': json.loads(self.task_data) if self.task_data else None,
            'status': self.status,
            'result_data': json.loads(self.result_data) if self.result_data else None,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'execution_time_seconds': self.execution_time_seconds
        }

class Webhook(db.Model):
    """Webhook configuration"""
    __tablename__ = 'webhooks'
    
    id = db.Column(db.Integer, primary_key=True)
    webhook_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    endpoint_path = db.Column(db.String(200), nullable=False)
    workflow_id = db.Column(db.String(100), db.ForeignKey('workflows.workflow_id'))
    method = db.Column(db.String(10), default='POST')  # GET, POST, PUT, DELETE
    authentication_type = db.Column(db.String(50), default='none')  # none, api_key, basic, bearer
    authentication_config = db.Column(db.Text)  # JSON auth configuration
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    calls = db.relationship('WebhookCall', backref='webhook', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'webhook_id': self.webhook_id,
            'name': self.name,
            'description': self.description,
            'endpoint_path': self.endpoint_path,
            'workflow_id': self.workflow_id,
            'method': self.method,
            'authentication_type': self.authentication_type,
            'authentication_config': json.loads(self.authentication_config) if self.authentication_config else {},
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class WebhookCall(db.Model):
    """Webhook call tracking"""
    __tablename__ = 'webhook_calls'
    
    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.String(100), unique=True, nullable=False)
    webhook_id = db.Column(db.String(100), db.ForeignKey('webhooks.webhook_id'), nullable=False)
    execution_id = db.Column(db.String(100), db.ForeignKey('workflow_executions.execution_id'))
    method = db.Column(db.String(10), nullable=False)
    headers = db.Column(db.Text)  # JSON headers
    query_params = db.Column(db.Text)  # JSON query parameters
    body_data = db.Column(db.Text)  # JSON body data
    response_status = db.Column(db.Integer)
    response_data = db.Column(db.Text)  # JSON response data
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_id': self.call_id,
            'webhook_id': self.webhook_id,
            'execution_id': self.execution_id,
            'method': self.method,
            'headers': json.loads(self.headers) if self.headers else {},
            'query_params': json.loads(self.query_params) if self.query_params else {},
            'body_data': json.loads(self.body_data) if self.body_data else None,
            'response_status': self.response_status,
            'response_data': json.loads(self.response_data) if self.response_data else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Configuration(db.Model):
    """System configuration"""
    __tablename__ = 'configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default='general')
    is_encrypted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value if not self.is_encrypted else '[ENCRYPTED]',
            'description': self.description,
            'category': self.category,
            'is_encrypted': self.is_encrypted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

