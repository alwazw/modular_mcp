"""
Database models for Agent 2: Knowledge Base Creator
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float, ForeignKey

db = SQLAlchemy()

class Document(db.Model):
    """Model for documents in the knowledge base"""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    title = db.Column(db.String(500), nullable=False)
    source_type = db.Column(db.String(50), nullable=False)  # file, url, text
    source_path = db.Column(db.Text)  # File path or URL
    content_type = db.Column(db.String(100))  # MIME type
    
    # Content
    raw_content = db.Column(db.Text)
    processed_content = db.Column(db.Text)
    
    # Processing status
    processing_status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    chunk_count = db.Column(db.Integer, default=0)
    embedding_count = db.Column(db.Integer, default=0)
    
    # Metadata
    meta_data = db.Column(db.JSON)
    content_hash = db.Column(db.String(64))  # SHA-256
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Error handling
    error_message = db.Column(db.Text)
    
    # Relationships
    chunks = db.relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'title': self.title,
            'source_type': self.source_type,
            'source_path': self.source_path,
            'content_type': self.content_type,
            'processing_status': self.processing_status,
            'chunk_count': self.chunk_count,
            'embedding_count': self.embedding_count,
            'meta_data': self.meta_data,
            'content_hash': self.content_hash,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'error_message': self.error_message
        }

class DocumentChunk(db.Model):
    """Model for document chunks with embeddings"""
    __tablename__ = 'document_chunks'
    
    id = db.Column(db.Integer, primary_key=True)
    chunk_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    document_id = db.Column(db.String(36), db.ForeignKey('documents.document_id'), nullable=False)
    
    # Chunk info
    chunk_index = db.Column(db.Integer, nullable=False)
    chunk_type = db.Column(db.String(50), default='text')  # text, table, list, code, etc.
    
    # Content
    content = db.Column(db.Text, nullable=False)
    content_length = db.Column(db.Integer)
    
    # Position in document
    start_position = db.Column(db.Integer)
    end_position = db.Column(db.Integer)
    
    # Embedding
    embedding_vector = db.Column(db.Text)  # JSON string of embedding vector
    embedding_model = db.Column(db.String(100))
    embedding_status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    
    # Metadata
    meta_data = db.Column(db.JSON)
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    embedded_at = db.Column(db.DateTime)
    
    # Relationships
    document = db.relationship("Document", back_populates="chunks")
    
    def to_dict(self):
        return {
            'id': self.id,
            'chunk_id': self.chunk_id,
            'document_id': self.document_id,
            'chunk_index': self.chunk_index,
            'chunk_type': self.chunk_type,
            'content': self.content,
            'content_length': self.content_length,
            'start_position': self.start_position,
            'end_position': self.end_position,
            'embedding_model': self.embedding_model,
            'embedding_status': self.embedding_status,
            'meta_data': self.meta_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'embedded_at': self.embedded_at.isoformat() if self.embedded_at else None
        }

class KnowledgeBase(db.Model):
    """Model for knowledge base collections"""
    __tablename__ = 'knowledge_bases'
    
    id = db.Column(db.Integer, primary_key=True)
    kb_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Configuration
    embedding_model = db.Column(db.String(100), default='text-embedding-ada-002')
    chunk_size = db.Column(db.Integer, default=1000)
    chunk_overlap = db.Column(db.Integer, default=200)
    
    # Statistics
    document_count = db.Column(db.Integer, default=0)
    chunk_count = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'kb_id': self.kb_id,
            'name': self.name,
            'description': self.description,
            'embedding_model': self.embedding_model,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'document_count': self.document_count,
            'chunk_count': self.chunk_count,
            'total_tokens': self.total_tokens,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ProcessingJob(db.Model):
    """Model for knowledge processing jobs"""
    __tablename__ = 'processing_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    job_type = db.Column(db.String(50), nullable=False)  # document_processing, embedding_generation, similarity_search
    
    # Input
    input_data = db.Column(db.JSON)
    
    # Configuration
    config = db.Column(db.JSON)
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    progress = db.Column(db.Integer, default=0)  # 0-100
    
    # Results
    output_data = db.Column(db.JSON)
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Error handling
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'job_type': self.job_type,
            'input_data': self.input_data,
            'config': self.config,
            'status': self.status,
            'progress': self.progress,
            'output_data': self.output_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }

class SearchQuery(db.Model):
    """Model for search queries and results"""
    __tablename__ = 'search_queries'
    
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    
    # Query
    query_text = db.Column(db.Text, nullable=False)
    query_embedding = db.Column(db.Text)  # JSON string of query embedding
    
    # Search parameters
    kb_id = db.Column(db.String(36))  # Knowledge base ID (optional)
    similarity_threshold = db.Column(db.Float, default=0.7)
    max_results = db.Column(db.Integer, default=10)
    
    # Results
    results = db.Column(db.JSON)  # Search results
    result_count = db.Column(db.Integer, default=0)
    
    # Performance
    search_time_ms = db.Column(db.Integer)
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'query_id': self.query_id,
            'query_text': self.query_text,
            'kb_id': self.kb_id,
            'similarity_threshold': self.similarity_threshold,
            'max_results': self.max_results,
            'results': self.results,
            'result_count': self.result_count,
            'search_time_ms': self.search_time_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

