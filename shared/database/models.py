"""
Database models for the Multi-Agent MCP System
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

Base = declarative_base()

class Document(Base):
    """
    Stores metadata about documents processed by the system
    """
    __tablename__ = 'documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    source_url = Column(Text)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer)
    content_hash = Column(String(64))  # SHA-256 hash for deduplication
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_by_agent = Column(String(50))
    processing_status = Column(String(20), default='pending')  # pending, processing, completed, failed
    
    # Relationships
    knowledge_entries = relationship("KnowledgeEntry", back_populates="document")
    transformations = relationship("Transformation", back_populates="source_document")

class KnowledgeEntry(Base):
    """
    Stores processed knowledge from documents with embeddings
    """
    __tablename__ = 'knowledge_entries'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(50))  # paragraph, table, list, code, etc.
    embedding_vector = Column(Text)  # JSON string of embedding vector
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="knowledge_entries")

class Template(Base):
    """
    Stores template definitions for data transformation
    """
    __tablename__ = 'templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    platform = Column(String(100), nullable=False)  # bestbuy, walmart, amazon, etc.
    template_type = Column(String(50), nullable=False)  # product_creation, inventory_update, etc.
    schema_definition = Column(JSONB, nullable=False)  # Field definitions and types
    field_mappings = Column(JSONB)  # Known mappings to other templates
    validation_rules = Column(JSONB)  # Validation constraints
    example_data = Column(JSONB)  # Sample data for training
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    transformations = relationship("Transformation", back_populates="target_template")

class Transformation(Base):
    """
    Stores transformation history and rules
    """
    __tablename__ = 'transformations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'))
    target_template_id = Column(UUID(as_uuid=True), ForeignKey('templates.id'), nullable=False)
    transformation_rules = Column(JSONB, nullable=False)  # AI-generated mapping rules
    input_data = Column(JSONB)
    output_data = Column(JSONB)
    confidence_score = Column(Float)  # AI confidence in transformation
    validation_status = Column(String(20), default='pending')  # pending, validated, rejected
    user_feedback = Column(JSONB)  # User corrections and feedback
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_agent = Column(String(50), nullable=False)
    
    # Relationships
    source_document = relationship("Document", back_populates="transformations")
    target_template = relationship("Template", back_populates="transformations")

class Task(Base):
    """
    Stores task information for workflow management
    """
    __tablename__ = 'tasks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_type = Column(String(50), nullable=False)  # scrape, process, transform, etc.
    status = Column(String(20), default='pending')  # pending, running, completed, failed
    priority = Column(Integer, default=5)  # 1-10, higher is more urgent
    assigned_agent = Column(String(50))
    input_data = Column(JSONB)
    output_data = Column(JSONB)
    error_message = Column(Text)
    progress_percentage = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    estimated_duration = Column(Integer)  # seconds
    actual_duration = Column(Integer)  # seconds
    
    # Relationships
    subtasks = relationship("Task", backref="parent_task", remote_side=[id])
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'))

class AgentSession(Base):
    """
    Stores agent session information for browser persistence
    """
    __tablename__ = 'agent_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(50), nullable=False)
    session_name = Column(String(100), nullable=False)
    session_data = Column(JSONB)  # Cookies, local storage, etc.
    browser_profile = Column(String(100))
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

class SystemConfig(Base):
    """
    Stores system configuration and settings
    """
    __tablename__ = 'system_config'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_key = Column(String(100), nullable=False, unique=True)
    config_value = Column(JSONB, nullable=False)
    description = Column(Text)
    is_sensitive = Column(Boolean, default=False)  # For passwords, API keys, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(Base):
    """
    Stores audit trail for all system operations
    """
    __tablename__ = 'audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    details = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
    error_message = Column(Text)

# Database connection and session management
class DatabaseManager:
    """
    Manages database connections and sessions
    """
    
    def __init__(self, database_url=None):
        if database_url is None:
            # Default to SQLite for development, PostgreSQL for production
            database_url = "sqlite:///multi_agent_mcp.db"
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()
    
    def close_session(self, session):
        """Close a database session"""
        session.close()

# Utility functions for common database operations
def get_or_create(session, model, **kwargs):
    """Get an existing record or create a new one"""
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance, True

def update_task_status(session, task_id, status, progress=None, error_message=None):
    """Update task status and progress"""
    task = session.query(Task).filter_by(id=task_id).first()
    if task:
        task.status = status
        if progress is not None:
            task.progress_percentage = progress
        if error_message:
            task.error_message = error_message
        if status == 'running' and not task.started_at:
            task.started_at = datetime.utcnow()
        elif status in ['completed', 'failed']:
            task.completed_at = datetime.utcnow()
            if task.started_at:
                task.actual_duration = int((task.completed_at - task.started_at).total_seconds())
        session.commit()
        return task
    return None

def log_audit_event(session, agent_id, action, resource_type=None, resource_id=None, 
                   details=None, success=True, error_message=None):
    """Log an audit event"""
    audit_log = AuditLog(
        agent_id=agent_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        details=details,
        success=success,
        error_message=error_message
    )
    session.add(audit_log)
    session.commit()
    return audit_log

