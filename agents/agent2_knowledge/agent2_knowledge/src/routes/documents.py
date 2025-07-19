"""
Documents routes for Agent 2: Knowledge Base Creator
"""

import uuid
import hashlib
from datetime import datetime
from flask import Blueprint, request, jsonify
from src.models.knowledge import db, Document, DocumentChunk, KnowledgeBase
from src.services.document_processor import DocumentProcessorService

documents_bp = Blueprint('documents', __name__)

# Initialize document processor service
document_processor = DocumentProcessorService()

@documents_bp.route('/', methods=['POST'])
def add_document():
    """Add a document to a knowledge base"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['kb_id', 'title', 'source_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if knowledge base exists
        kb = KnowledgeBase.query.filter_by(kb_id=data['kb_id']).first()
        if not kb:
            return jsonify({'error': 'Knowledge base not found'}), 404
        
        # Create document
        content = data.get('content', '')
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Check for duplicates
        existing_doc = Document.query.filter_by(content_hash=content_hash).first()
        if existing_doc:
            return jsonify({
                'message': 'Document already exists',
                'document_id': existing_doc.document_id,
                'duplicate': True
            }), 200
        
        document = Document(
            document_id=str(uuid.uuid4()),
            title=data['title'],
            source_type=data['source_type'],
            source_path=data.get('source_path'),
            content_type=data.get('content_type'),
            raw_content=content,
            meta_data=data.get('metadata', {}),
            content_hash=content_hash
        )
        
        db.session.add(document)
        db.session.commit()
        
        # Start processing asynchronously
        document_processor.start_document_processing(document.document_id, kb.to_dict())
        
        return jsonify({
            'document_id': document.document_id,
            'status': 'created',
            'message': 'Document added and processing started'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/<document_id>', methods=['GET'])
def get_document(document_id):
    """Get document details"""
    try:
        document = Document.query.filter_by(document_id=document_id).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Get associated chunks
        chunks = DocumentChunk.query.filter_by(document_id=document_id).all()
        
        response = document.to_dict()
        response['chunks'] = [chunk.to_dict() for chunk in chunks]
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/', methods=['GET'])
def list_documents():
    """List documents"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        kb_id = request.args.get('kb_id')
        status = request.args.get('status')
        source_type = request.args.get('source_type')
        
        query = Document.query
        
        if kb_id:
            query = query.filter_by(kb_id=kb_id)
        
        if status:
            query = query.filter_by(processing_status=status)
        
        if source_type:
            query = query.filter_by(source_type=source_type)
        
        documents = query.order_by(Document.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'documents': [doc.to_dict() for doc in documents.items],
            'total': documents.total,
            'pages': documents.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/<document_id>', methods=['PUT'])
def update_document(document_id):
    """Update document"""
    try:
        document = Document.query.filter_by(document_id=document_id).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        data = request.get_json() or {}
        
        # Update allowed fields
        if 'title' in data:
            document.title = data['title']
        
        if 'meta_data' in data:
            document.meta_data = data['meta_data']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Document updated successfully',
            'document': document.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Delete document and all associated chunks"""
    try:
        document = Document.query.filter_by(document_id=document_id).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Delete associated chunks (cascade should handle this)
        DocumentChunk.query.filter_by(document_id=document_id).delete()
        
        # Delete document
        db.session.delete(document)
        db.session.commit()
        
        return jsonify({'message': 'Document deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/<document_id>/reprocess', methods=['POST'])
def reprocess_document(document_id):
    """Reprocess a document"""
    try:
        document = Document.query.filter_by(document_id=document_id).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Get knowledge base configuration
        kb = KnowledgeBase.query.filter_by(kb_id=document.kb_id).first()
        if not kb:
            return jsonify({'error': 'Knowledge base not found'}), 404
        
        # Reset processing status
        document.processing_status = 'pending'
        document.chunk_count = 0
        document.embedding_count = 0
        document.error_message = None
        
        # Delete existing chunks
        DocumentChunk.query.filter_by(document_id=document_id).delete()
        
        db.session.commit()
        
        # Start reprocessing
        document_processor.start_document_processing(document_id, kb.to_dict())
        
        return jsonify({
            'message': 'Document reprocessing started',
            'document_id': document_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/<document_id>/chunks', methods=['GET'])
def get_document_chunks(document_id):
    """Get chunks for a document"""
    try:
        document = Document.query.filter_by(document_id=document_id).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        chunks = DocumentChunk.query.filter_by(document_id=document_id).order_by(
            DocumentChunk.chunk_index
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'document_id': document_id,
            'chunks': [chunk.to_dict() for chunk in chunks.items],
            'total': chunks.total,
            'pages': chunks.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/chunks/<chunk_id>', methods=['GET'])
def get_chunk(chunk_id):
    """Get specific chunk details"""
    try:
        chunk = DocumentChunk.query.filter_by(chunk_id=chunk_id).first()
        
        if not chunk:
            return jsonify({'error': 'Chunk not found'}), 404
        
        return jsonify(chunk.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/chunks/<chunk_id>', methods=['PUT'])
def update_chunk(chunk_id):
    """Update chunk content"""
    try:
        chunk = DocumentChunk.query.filter_by(chunk_id=chunk_id).first()
        
        if not chunk:
            return jsonify({'error': 'Chunk not found'}), 404
        
        data = request.get_json() or {}
        
        # Update allowed fields
        if 'content' in data:
            chunk.content = data['content']
            chunk.content_length = len(data['content'])
            # Reset embedding status if content changed
            chunk.embedding_status = 'pending'
            chunk.embedding_vector = None
            chunk.embedded_at = None
        
        if 'meta_data' in data:
            chunk.meta_data = data['meta_data']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Chunk updated successfully',
            'chunk': chunk.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/chunks/<chunk_id>', methods=['DELETE'])
def delete_chunk(chunk_id):
    """Delete a specific chunk"""
    try:
        chunk = DocumentChunk.query.filter_by(chunk_id=chunk_id).first()
        
        if not chunk:
            return jsonify({'error': 'Chunk not found'}), 404
        
        db.session.delete(chunk)
        db.session.commit()
        
        return jsonify({'message': 'Chunk deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/upload', methods=['POST'])
def upload_document():
    """Upload a document file for processing"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        kb_id = request.form.get('kb_id')
        title = request.form.get('title')
        
        if not kb_id:
            return jsonify({'error': 'Knowledge base ID is required'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if knowledge base exists
        kb = KnowledgeBase.query.filter_by(kb_id=kb_id).first()
        if not kb:
            return jsonify({'error': 'Knowledge base not found'}), 404
        
        # Save file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            file.save(tmp_file.name)
            file_path = tmp_file.name
        
        # Create document record
        document = Document(
            document_id=str(uuid.uuid4()),
            title=title or file.filename,
            source_type='file',
            source_path=file_path,
            content_type=file.content_type,
            meta_data={'original_filename': file.filename}
        )
        
        db.session.add(document)
        db.session.commit()
        
        # Start processing
        document_processor.start_file_processing(document.document_id, file_path, kb.to_dict())
        
        return jsonify({
            'document_id': document.document_id,
            'status': 'uploaded',
            'message': 'File uploaded and processing started'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/from-agent1', methods=['POST'])
def import_from_agent1():
    """Import processed content from Agent 1"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields
        required_fields = ['kb_id', 'agent1_content']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if knowledge base exists
        kb = KnowledgeBase.query.filter_by(kb_id=data['kb_id']).first()
        if not kb:
            return jsonify({'error': 'Knowledge base not found'}), 404
        
        agent1_content = data['agent1_content']
        
        # Create document from Agent 1 content
        document = Document(
            document_id=str(uuid.uuid4()),
            title=agent1_content.get('title', 'Imported from Agent 1'),
            source_type='agent1',
            source_path=agent1_content.get('url'),
            content_type='text/html',
            raw_content=agent1_content.get('raw_content'),
            processed_content=agent1_content.get('cleaned_content'),
            meta_data=agent1_content.get('metadata', {}),
            content_hash=agent1_content.get('content_hash')
        )
        
        db.session.add(document)
        db.session.commit()
        
        # Start processing
        document_processor.start_agent1_import(document.document_id, agent1_content, kb.to_dict())
        
        return jsonify({
            'document_id': document.document_id,
            'status': 'imported',
            'message': 'Content imported from Agent 1 and processing started'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

