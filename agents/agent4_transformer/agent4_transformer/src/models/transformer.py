"""
Database models for Agent 4: Intelligent Data Transformer
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Template(db.Model):
    """Model for data templates (e.g., BestBuy, Walmart product templates)"""
    __tablename__ = 'templates'
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    template_type = db.Column(db.String(50), nullable=False)  # product, order, customer, etc.
    platform = db.Column(db.String(100))  # bestbuy, walmart, amazon, etc.
    
    # Template structure and metadata
    schema_definition = db.Column(db.JSON)  # Column definitions, types, constraints
    sample_data = db.Column(db.JSON)  # Sample data for understanding
    validation_rules = db.Column(db.JSON)  # Validation rules for the template
    
    # Documentation and context
    documentation = db.Column(db.Text)  # Human-readable documentation
    column_descriptions = db.Column(db.JSON)  # Descriptions for each column
    business_rules = db.Column(db.JSON)  # Business logic and rules
    
    # Metadata
    version = db.Column(db.String(20), default='1.0')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    mappings_as_source = db.relationship('TemplateMapping', foreign_keys='TemplateMapping.source_template_id', backref='source_template')
    mappings_as_target = db.relationship('TemplateMapping', foreign_keys='TemplateMapping.target_template_id', backref='target_template')
    
    def to_dict(self):
        return {
            'id': self.id,
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'template_type': self.template_type,
            'platform': self.platform,
            'schema_definition': self.schema_definition,
            'sample_data': self.sample_data,
            'validation_rules': self.validation_rules,
            'documentation': self.documentation,
            'column_descriptions': self.column_descriptions,
            'business_rules': self.business_rules,
            'version': self.version,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class TemplateMapping(db.Model):
    """Model for mappings between different templates"""
    __tablename__ = 'template_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    mapping_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Source and target templates
    source_template_id = db.Column(db.String(100), db.ForeignKey('templates.template_id'), nullable=False)
    target_template_id = db.Column(db.String(100), db.ForeignKey('templates.template_id'), nullable=False)
    
    # Mapping configuration
    field_mappings = db.Column(db.JSON)  # Field-to-field mappings
    transformation_rules = db.Column(db.JSON)  # Transformation logic
    default_values = db.Column(db.JSON)  # Default values for target fields
    conditional_logic = db.Column(db.JSON)  # Conditional transformation rules
    
    # Intelligence and learning
    confidence_score = db.Column(db.Float, default=0.0)  # AI confidence in mapping
    learning_data = db.Column(db.JSON)  # Data for improving mappings
    validation_results = db.Column(db.JSON)  # Results from mapping validation
    
    # Metadata
    mapping_type = db.Column(db.String(50), default='manual')  # manual, ai_generated, hybrid
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'mapping_id': self.mapping_id,
            'name': self.name,
            'description': self.description,
            'source_template_id': self.source_template_id,
            'target_template_id': self.target_template_id,
            'field_mappings': self.field_mappings,
            'transformation_rules': self.transformation_rules,
            'default_values': self.default_values,
            'conditional_logic': self.conditional_logic,
            'confidence_score': self.confidence_score,
            'learning_data': self.learning_data,
            'validation_results': self.validation_results,
            'mapping_type': self.mapping_type,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class TransformationJob(db.Model):
    """Model for data transformation jobs"""
    __tablename__ = 'transformation_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Job configuration
    mapping_id = db.Column(db.String(100), db.ForeignKey('template_mappings.mapping_id'), nullable=False)
    source_data_path = db.Column(db.String(500))  # Path to source data file
    target_data_path = db.Column(db.String(500))  # Path to output file
    
    # Job execution details
    status = db.Column(db.String(50), default='pending')  # pending, running, completed, failed
    progress_percentage = db.Column(db.Float, default=0.0)
    records_processed = db.Column(db.Integer, default=0)
    records_successful = db.Column(db.Integer, default=0)
    records_failed = db.Column(db.Integer, default=0)
    
    # Results and metrics
    execution_time_seconds = db.Column(db.Float)
    error_message = db.Column(db.Text)
    validation_results = db.Column(db.JSON)
    quality_metrics = db.Column(db.JSON)
    
    # Metadata
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    mapping = db.relationship('TemplateMapping', backref='transformation_jobs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'name': self.name,
            'description': self.description,
            'mapping_id': self.mapping_id,
            'source_data_path': self.source_data_path,
            'target_data_path': self.target_data_path,
            'status': self.status,
            'progress_percentage': self.progress_percentage,
            'records_processed': self.records_processed,
            'records_successful': self.records_successful,
            'records_failed': self.records_failed,
            'execution_time_seconds': self.execution_time_seconds,
            'error_message': self.error_message,
            'validation_results': self.validation_results,
            'quality_metrics': self.quality_metrics,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class IntelligenceRule(db.Model):
    """Model for AI intelligence rules and learning patterns"""
    __tablename__ = 'intelligence_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Rule configuration
    rule_type = db.Column(db.String(50), nullable=False)  # field_mapping, validation, transformation
    pattern = db.Column(db.JSON)  # Pattern to match
    action = db.Column(db.JSON)  # Action to take when pattern matches
    conditions = db.Column(db.JSON)  # Conditions for rule activation
    
    # Learning and adaptation
    confidence_score = db.Column(db.Float, default=0.0)
    usage_count = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.0)
    learning_data = db.Column(db.JSON)
    
    # Scope and applicability
    template_types = db.Column(db.JSON)  # Which template types this rule applies to
    platforms = db.Column(db.JSON)  # Which platforms this rule applies to
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    is_system_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'rule_type': self.rule_type,
            'pattern': self.pattern,
            'action': self.action,
            'conditions': self.conditions,
            'confidence_score': self.confidence_score,
            'usage_count': self.usage_count,
            'success_rate': self.success_rate,
            'learning_data': self.learning_data,
            'template_types': self.template_types,
            'platforms': self.platforms,
            'is_active': self.is_active,
            'is_system_generated': self.is_system_generated,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class KnowledgeBase(db.Model):
    """Model for storing domain knowledge and documentation"""
    __tablename__ = 'knowledge_base'
    
    id = db.Column(db.Integer, primary_key=True)
    knowledge_id = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # Knowledge categorization
    category = db.Column(db.String(100))  # platform_docs, business_rules, field_definitions
    subcategory = db.Column(db.String(100))
    tags = db.Column(db.JSON)
    
    # Source and context
    source_type = db.Column(db.String(50))  # scraped, uploaded, manual
    source_url = db.Column(db.String(500))
    source_file_path = db.Column(db.String(500))
    platform = db.Column(db.String(100))
    
    # Content processing
    processed_content = db.Column(db.Text)  # Processed/cleaned content
    embeddings = db.Column(db.JSON)  # Vector embeddings for similarity search
    keywords = db.Column(db.JSON)  # Extracted keywords
    
    # Usage and relevance
    relevance_score = db.Column(db.Float, default=0.0)
    usage_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'knowledge_id': self.knowledge_id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'subcategory': self.subcategory,
            'tags': self.tags,
            'source_type': self.source_type,
            'source_url': self.source_url,
            'source_file_path': self.source_file_path,
            'platform': self.platform,
            'processed_content': self.processed_content,
            'embeddings': self.embeddings,
            'keywords': self.keywords,
            'relevance_score': self.relevance_score,
            'usage_count': self.usage_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

