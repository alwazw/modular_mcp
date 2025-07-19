"""
Database models for Agent 3: Database Manager
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float, ForeignKey

db = SQLAlchemy()

class DatabaseConnection(db.Model):
    """Model for database connections"""
    __tablename__ = 'database_connections'
    
    id = db.Column(db.Integer, primary_key=True)
    connection_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Connection details
    db_type = db.Column(db.String(50), nullable=False)  # postgresql, mysql, sqlite, mongodb
    host = db.Column(db.String(255))
    port = db.Column(db.Integer)
    database_name = db.Column(db.String(255))
    username = db.Column(db.String(255))
    password_encrypted = db.Column(db.Text)  # Encrypted password
    connection_string = db.Column(db.Text)  # Full connection string
    
    # Configuration
    config = db.Column(db.JSON)  # Additional configuration options
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_tested = db.Column(db.DateTime)
    test_status = db.Column(db.String(20))  # success, failed, pending
    test_message = db.Column(db.Text)
    
    # Usage tracking
    connection_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    backup_jobs = db.relationship("BackupJob", back_populates="database_connection", cascade="all, delete-orphan")
    sync_operations = db.relationship("SyncOperation", back_populates="source_connection", foreign_keys="SyncOperation.source_connection_id")
    
    def to_dict(self):
        return {
            'id': self.id,
            'connection_id': self.connection_id,
            'name': self.name,
            'description': self.description,
            'db_type': self.db_type,
            'host': self.host,
            'port': self.port,
            'database_name': self.database_name,
            'username': self.username,
            'config': self.config,
            'is_active': self.is_active,
            'last_tested': self.last_tested.isoformat() if self.last_tested else None,
            'test_status': self.test_status,
            'test_message': self.test_message,
            'connection_count': self.connection_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class BackupJob(db.Model):
    """Model for backup jobs"""
    __tablename__ = 'backup_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Source database
    connection_id = db.Column(db.String(36), db.ForeignKey('database_connections.connection_id'), nullable=False)
    
    # Backup configuration
    backup_type = db.Column(db.String(50), nullable=False)  # full, incremental, differential
    backup_format = db.Column(db.String(50), default='sql')  # sql, binary, json
    compression = db.Column(db.Boolean, default=True)
    encryption = db.Column(db.Boolean, default=False)
    
    # Schedule
    schedule_type = db.Column(db.String(20))  # manual, daily, weekly, monthly, cron
    schedule_config = db.Column(db.JSON)  # Schedule configuration
    
    # Storage
    storage_type = db.Column(db.String(50), default='local')  # local, s3, ftp, etc.
    storage_path = db.Column(db.Text)
    storage_config = db.Column(db.JSON)
    
    # Retention
    retention_days = db.Column(db.Integer, default=30)
    max_backups = db.Column(db.Integer, default=10)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime)
    next_run = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    
    # Statistics
    total_runs = db.Column(db.Integer, default=0)
    successful_runs = db.Column(db.Integer, default=0)
    failed_runs = db.Column(db.Integer, default=0)
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    database_connection = db.relationship("DatabaseConnection", back_populates="backup_jobs")
    backup_runs = db.relationship("BackupRun", back_populates="backup_job", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'name': self.name,
            'description': self.description,
            'connection_id': self.connection_id,
            'backup_type': self.backup_type,
            'backup_format': self.backup_format,
            'compression': self.compression,
            'encryption': self.encryption,
            'schedule_type': self.schedule_type,
            'schedule_config': self.schedule_config,
            'storage_type': self.storage_type,
            'storage_path': self.storage_path,
            'storage_config': self.storage_config,
            'retention_days': self.retention_days,
            'max_backups': self.max_backups,
            'is_active': self.is_active,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'status': self.status,
            'total_runs': self.total_runs,
            'successful_runs': self.successful_runs,
            'failed_runs': self.failed_runs,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class BackupRun(db.Model):
    """Model for individual backup runs"""
    __tablename__ = 'backup_runs'
    
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    job_id = db.Column(db.String(36), db.ForeignKey('backup_jobs.job_id'), nullable=False)
    
    # Execution details
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    trigger_type = db.Column(db.String(20))  # manual, scheduled, api
    
    # Results
    backup_file_path = db.Column(db.Text)
    backup_size_bytes = db.Column(db.Integer)
    compressed_size_bytes = db.Column(db.Integer)
    
    # Performance
    duration_seconds = db.Column(db.Float)
    records_backed_up = db.Column(db.Integer)
    
    # Error handling
    error_message = db.Column(db.Text)
    error_details = db.Column(db.JSON)
    
    # Timing
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    backup_job = db.relationship("BackupJob", back_populates="backup_runs")
    
    def to_dict(self):
        return {
            'id': self.id,
            'run_id': self.run_id,
            'job_id': self.job_id,
            'status': self.status,
            'trigger_type': self.trigger_type,
            'backup_file_path': self.backup_file_path,
            'backup_size_bytes': self.backup_size_bytes,
            'compressed_size_bytes': self.compressed_size_bytes,
            'duration_seconds': self.duration_seconds,
            'records_backed_up': self.records_backed_up,
            'error_message': self.error_message,
            'error_details': self.error_details,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SyncOperation(db.Model):
    """Model for data synchronization operations"""
    __tablename__ = 'sync_operations'
    
    id = db.Column(db.Integer, primary_key=True)
    sync_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Source and target
    source_connection_id = db.Column(db.String(36), db.ForeignKey('database_connections.connection_id'), nullable=False)
    target_connection_id = db.Column(db.String(36), db.ForeignKey('database_connections.connection_id'))
    
    # Sync configuration
    sync_type = db.Column(db.String(50), nullable=False)  # full, incremental, bidirectional
    sync_mode = db.Column(db.String(50), default='push')  # push, pull, bidirectional
    
    # Data selection
    source_query = db.Column(db.Text)  # SQL query or filter
    target_table = db.Column(db.String(255))
    field_mapping = db.Column(db.JSON)  # Field mapping configuration
    
    # Schedule
    schedule_type = db.Column(db.String(20))  # manual, realtime, daily, weekly, cron
    schedule_config = db.Column(db.JSON)
    
    # Conflict resolution
    conflict_resolution = db.Column(db.String(50), default='source_wins')  # source_wins, target_wins, merge, skip
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_sync = db.Column(db.DateTime)
    next_sync = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')
    
    # Statistics
    total_syncs = db.Column(db.Integer, default=0)
    successful_syncs = db.Column(db.Integer, default=0)
    failed_syncs = db.Column(db.Integer, default=0)
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source_connection = db.relationship("DatabaseConnection", foreign_keys=[source_connection_id])
    sync_runs = db.relationship("SyncRun", back_populates="sync_operation", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'sync_id': self.sync_id,
            'name': self.name,
            'description': self.description,
            'source_connection_id': self.source_connection_id,
            'target_connection_id': self.target_connection_id,
            'sync_type': self.sync_type,
            'sync_mode': self.sync_mode,
            'source_query': self.source_query,
            'target_table': self.target_table,
            'field_mapping': self.field_mapping,
            'schedule_type': self.schedule_type,
            'schedule_config': self.schedule_config,
            'conflict_resolution': self.conflict_resolution,
            'is_active': self.is_active,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'next_sync': self.next_sync.isoformat() if self.next_sync else None,
            'status': self.status,
            'total_syncs': self.total_syncs,
            'successful_syncs': self.successful_syncs,
            'failed_syncs': self.failed_syncs,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SyncRun(db.Model):
    """Model for individual sync runs"""
    __tablename__ = 'sync_runs'
    
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    sync_id = db.Column(db.String(36), db.ForeignKey('sync_operations.sync_id'), nullable=False)
    
    # Execution details
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    trigger_type = db.Column(db.String(20))  # manual, scheduled, realtime
    
    # Results
    records_processed = db.Column(db.Integer, default=0)
    records_inserted = db.Column(db.Integer, default=0)
    records_updated = db.Column(db.Integer, default=0)
    records_deleted = db.Column(db.Integer, default=0)
    records_skipped = db.Column(db.Integer, default=0)
    
    # Performance
    duration_seconds = db.Column(db.Float)
    
    # Error handling
    error_message = db.Column(db.Text)
    error_details = db.Column(db.JSON)
    
    # Timing
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sync_operation = db.relationship("SyncOperation", back_populates="sync_runs")
    
    def to_dict(self):
        return {
            'id': self.id,
            'run_id': self.run_id,
            'sync_id': self.sync_id,
            'status': self.status,
            'trigger_type': self.trigger_type,
            'records_processed': self.records_processed,
            'records_inserted': self.records_inserted,
            'records_updated': self.records_updated,
            'records_deleted': self.records_deleted,
            'records_skipped': self.records_skipped,
            'duration_seconds': self.duration_seconds,
            'error_message': self.error_message,
            'error_details': self.error_details,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class DataSchema(db.Model):
    """Model for tracking database schemas"""
    __tablename__ = 'data_schemas'
    
    id = db.Column(db.Integer, primary_key=True)
    schema_id = db.Column(db.String(36), unique=True, nullable=False)  # UUID
    connection_id = db.Column(db.String(36), db.ForeignKey('database_connections.connection_id'), nullable=False)
    
    # Schema details
    schema_name = db.Column(db.String(255))
    table_name = db.Column(db.String(255), nullable=False)
    schema_definition = db.Column(db.JSON)  # Full schema definition
    
    # Metadata
    record_count = db.Column(db.Integer)
    size_bytes = db.Column(db.Integer)
    last_analyzed = db.Column(db.DateTime)
    
    # Timing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'schema_id': self.schema_id,
            'connection_id': self.connection_id,
            'schema_name': self.schema_name,
            'table_name': self.table_name,
            'schema_definition': self.schema_definition,
            'record_count': self.record_count,
            'size_bytes': self.size_bytes,
            'last_analyzed': self.last_analyzed.isoformat() if self.last_analyzed else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

