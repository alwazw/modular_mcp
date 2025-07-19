"""
Database models for Agent 1: Web Scraper & Data Collector
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float

db = SQLAlchemy()

class ScrapingJob(db.Model):
    """Model for scraping jobs"""
    __tablename__ = 'scraping_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    url = db.Column(db.Text, nullable=False)
    job_type = db.Column(db.String(50), nullable=False)  # single_page, multi_page, file_download
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    priority = db.Column(db.Integer, default=5)  # 1-10, higher is more urgent
    
    # Configuration
    scraping_config = db.Column(db.JSON)  # Scraping parameters
    output_format = db.Column(db.String(20), default='json')  # json, csv, html
    
    # Results
    output_path = db.Column(db.Text)
    extracted_data = db.Column(db.JSON)
    meta_data = db.Column(db.JSON)
    
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
            'url': self.url,
            'job_type': self.job_type,
            'status': self.status,
            'priority': self.priority,
            'scraping_config': self.scraping_config,
            'output_format': self.output_format,
            'output_path': self.output_path,
            'extracted_data': self.extracted_data,
            'meta_data': self.meta_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }

class BrowserSession(db.Model):
    """Model for persistent browser sessions"""
    __tablename__ = 'browser_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    session_name = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(255))
    
    # Session data
    cookies = db.Column(db.JSON)
    local_storage = db.Column(db.JSON)
    session_storage = db.Column(db.JSON)
    user_agent = db.Column(db.Text)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_authenticated = db.Column(db.Boolean, default=False)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'session_name': self.session_name,
            'domain': self.domain,
            'is_active': self.is_active,
            'is_authenticated': self.is_authenticated,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'notes': self.notes
        }

class FileUpload(db.Model):
    """Model for uploaded files"""
    __tablename__ = 'file_uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    
    # File info
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    file_hash = db.Column(db.String(64))  # SHA-256
    
    # Processing status
    processing_status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    extracted_content = db.Column(db.JSON)
    meta_data = db.Column(db.JSON)
    
    # Timing
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Error handling
    error_message = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'file_id': self.file_id,
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'file_hash': self.file_hash,
            'processing_status': self.processing_status,
            'extracted_content': self.extracted_content,
            'meta_data': self.meta_data,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'error_message': self.error_message
        }

class ScrapedContent(db.Model):
    """Model for scraped content"""
    __tablename__ = 'scraped_content'
    
    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    job_id = db.Column(db.String(36), db.ForeignKey('scraping_jobs.job_id'), nullable=False)
    
    # Content info
    url = db.Column(db.Text, nullable=False)
    title = db.Column(db.Text)
    content_type = db.Column(db.String(50))  # text, image, video, document
    
    # Content data
    raw_content = db.Column(db.Text)
    cleaned_content = db.Column(db.Text)
    structured_data = db.Column(db.JSON)
    
    # Metadata
    meta_data = db.Column(db.JSON)
    content_hash = db.Column(db.String(64))  # SHA-256
    
    # Timing
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'content_id': self.content_id,
            'job_id': self.job_id,
            'url': self.url,
            'title': self.title,
            'content_type': self.content_type,
            'raw_content': self.raw_content,
            'cleaned_content': self.cleaned_content,
            'structured_data': self.structured_data,
            'meta_data': self.meta_data,
            'content_hash': self.content_hash,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None
        }

