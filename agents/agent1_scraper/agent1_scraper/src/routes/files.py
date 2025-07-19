"""
File handling routes for Agent 1: Web Scraper & Data Collector
"""

import uuid
import os
import hashlib
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from src.models.scraper import db, FileUpload
from src.services.file_processor import FileProcessorService

files_bp = Blueprint('files', __name__)

# Initialize file processor service
file_processor = FileProcessorService()

# Configure upload settings
UPLOAD_FOLDER = '/home/ubuntu/multi_agent_mcp/shared/storage/raw'
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'json', 'xml', 'html',
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp',
    'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm',
    'mp3', 'wav', 'flac', 'aac', 'ogg',
    'zip', 'rar', '7z', 'tar', 'gz'
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of a file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

@files_bp.route('/upload', methods=['POST'])
def upload_file():
    """Upload a file for processing"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        stored_filename = f"{file_id}.{file_extension}" if file_extension else file_id
        
        # Ensure upload directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file_path = os.path.join(UPLOAD_FOLDER, stored_filename)
        
        # Save file
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_hash = calculate_file_hash(file_path)
        
        # Check for duplicates
        existing_file = FileUpload.query.filter_by(file_hash=file_hash).first()
        if existing_file:
            # Remove the newly uploaded file since it's a duplicate
            os.remove(file_path)
            return jsonify({
                'message': 'File already exists',
                'file_id': existing_file.file_id,
                'duplicate': True
            }), 200
        
        # Create database record
        file_upload = FileUpload(
            file_id=file_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type,
            file_hash=file_hash
        )
        
        db.session.add(file_upload)
        db.session.commit()
        
        # Start processing asynchronously
        file_processor.start_processing(file_id)
        
        return jsonify({
            'file_id': file_id,
            'original_filename': original_filename,
            'file_size': file_size,
            'status': 'uploaded',
            'message': 'File uploaded successfully and processing started'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/<file_id>', methods=['GET'])
def get_file_info(file_id):
    """Get file information and processing status"""
    try:
        file_upload = FileUpload.query.filter_by(file_id=file_id).first()
        
        if not file_upload:
            return jsonify({'error': 'File not found'}), 404
        
        return jsonify(file_upload.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/', methods=['GET'])
def list_files():
    """List all uploaded files"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        file_type = request.args.get('type')
        
        query = FileUpload.query
        
        if status:
            query = query.filter_by(processing_status=status)
        
        if file_type:
            query = query.filter(FileUpload.mime_type.like(f'{file_type}%'))
        
        files = query.order_by(FileUpload.uploaded_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'files': [file.to_dict() for file in files.items],
            'total': files.total,
            'pages': files.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/<file_id>/download', methods=['GET'])
def download_file(file_id):
    """Download a file"""
    try:
        file_upload = FileUpload.query.filter_by(file_id=file_id).first()
        
        if not file_upload:
            return jsonify({'error': 'File not found'}), 404
        
        if not os.path.exists(file_upload.file_path):
            return jsonify({'error': 'File not found on disk'}), 404
        
        return send_file(
            file_upload.file_path,
            as_attachment=True,
            download_name=file_upload.original_filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/<file_id>/content', methods=['GET'])
def get_file_content(file_id):
    """Get extracted content from a file"""
    try:
        file_upload = FileUpload.query.filter_by(file_id=file_id).first()
        
        if not file_upload:
            return jsonify({'error': 'File not found'}), 404
        
        if file_upload.processing_status != 'completed':
            return jsonify({
                'error': 'File not yet processed',
                'status': file_upload.processing_status
            }), 400
        
        return jsonify({
            'file_id': file_id,
            'original_filename': file_upload.original_filename,
            'extracted_content': file_upload.extracted_content,
            'meta_data': file_upload.meta_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete a file"""
    try:
        file_upload = FileUpload.query.filter_by(file_id=file_id).first()
        
        if not file_upload:
            return jsonify({'error': 'File not found'}), 404
        
        # Delete file from disk
        if os.path.exists(file_upload.file_path):
            os.remove(file_upload.file_path)
        
        # Delete database record
        db.session.delete(file_upload)
        db.session.commit()
        
        return jsonify({'message': 'File deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/<file_id>/reprocess', methods=['POST'])
def reprocess_file(file_id):
    """Reprocess a file"""
    try:
        file_upload = FileUpload.query.filter_by(file_id=file_id).first()
        
        if not file_upload:
            return jsonify({'error': 'File not found'}), 404
        
        if not os.path.exists(file_upload.file_path):
            return jsonify({'error': 'File not found on disk'}), 404
        
        # Reset processing status
        file_upload.processing_status = 'pending'
        file_upload.extracted_content = None
        file_upload.meta_data = None
        file_upload.error_message = None
        
        db.session.commit()
        
        # Start processing
        file_processor.start_processing(file_id)
        
        return jsonify({
            'message': 'File reprocessing started',
            'file_id': file_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/batch-upload', methods=['POST'])
def batch_upload():
    """Upload multiple files at once"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({'error': 'No files selected'}), 400
        
        results = []
        
        for file in files:
            if file.filename == '':
                continue
            
            if not allowed_file(file.filename):
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': 'File type not allowed'
                })
                continue
            
            try:
                # Generate unique filename
                file_id = str(uuid.uuid4())
                original_filename = secure_filename(file.filename)
                file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
                stored_filename = f"{file_id}.{file_extension}" if file_extension else file_id
                
                # Ensure upload directory exists
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file_path = os.path.join(UPLOAD_FOLDER, stored_filename)
                
                # Save file
                file.save(file_path)
                
                # Get file info
                file_size = os.path.getsize(file_path)
                file_hash = calculate_file_hash(file_path)
                
                # Check for duplicates
                existing_file = FileUpload.query.filter_by(file_hash=file_hash).first()
                if existing_file:
                    os.remove(file_path)
                    results.append({
                        'filename': original_filename,
                        'file_id': existing_file.file_id,
                        'status': 'duplicate',
                        'message': 'File already exists'
                    })
                    continue
                
                # Create database record
                file_upload = FileUpload(
                    file_id=file_id,
                    original_filename=original_filename,
                    stored_filename=stored_filename,
                    file_path=file_path,
                    file_size=file_size,
                    mime_type=file.content_type,
                    file_hash=file_hash
                )
                
                db.session.add(file_upload)
                
                # Start processing
                file_processor.start_processing(file_id)
                
                results.append({
                    'filename': original_filename,
                    'file_id': file_id,
                    'file_size': file_size,
                    'status': 'uploaded',
                    'message': 'File uploaded successfully'
                })
                
            except Exception as e:
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': str(e)
                })
        
        db.session.commit()
        
        return jsonify({
            'message': f'Batch upload completed',
            'results': results,
            'total_files': len(files),
            'successful_uploads': len([r for r in results if r['status'] == 'uploaded'])
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/stats', methods=['GET'])
def get_file_stats():
    """Get file upload and processing statistics"""
    try:
        total_files = FileUpload.query.count()
        pending_files = FileUpload.query.filter_by(processing_status='pending').count()
        processing_files = FileUpload.query.filter_by(processing_status='processing').count()
        completed_files = FileUpload.query.filter_by(processing_status='completed').count()
        failed_files = FileUpload.query.filter_by(processing_status='failed').count()
        
        # Get total storage used
        total_size = db.session.query(db.func.sum(FileUpload.file_size)).scalar() or 0
        
        # Get file type distribution
        file_types = db.session.query(
            FileUpload.mime_type,
            db.func.count(FileUpload.id).label('count')
        ).group_by(FileUpload.mime_type).all()
        
        return jsonify({
            'statistics': {
                'total_files': total_files,
                'pending_files': pending_files,
                'processing_files': processing_files,
                'completed_files': completed_files,
                'failed_files': failed_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            },
            'file_types': [{'type': ft[0], 'count': ft[1]} for ft in file_types]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

