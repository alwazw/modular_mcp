"""
Knowledge routes for Agent 2: Knowledge Base Creator
"""

import uuid
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from src.models.knowledge import db, KnowledgeBase, Document, DocumentChunk, ProcessingJob, SearchQuery
from src.services.knowledge_processor import KnowledgeProcessorService
from src.services.embedding_service import EmbeddingService

knowledge_bp = Blueprint('knowledge', __name__)

# Initialize services
knowledge_processor = KnowledgeProcessorService()
embedding_service = EmbeddingService()

@knowledge_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'agent': 'agent2_knowledge',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@knowledge_bp.route('/bases', methods=['POST'])
def create_knowledge_base():
    """Create a new knowledge base"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Knowledge base name is required'}), 400
        
        # Create knowledge base
        kb = KnowledgeBase(
            kb_id=str(uuid.uuid4()),
            name=data['name'],
            description=data.get('description', ''),
            embedding_model=data.get('embedding_model', 'text-embedding-ada-002'),
            chunk_size=data.get('chunk_size', 1000),
            chunk_overlap=data.get('chunk_overlap', 200)
        )
        
        db.session.add(kb)
        db.session.commit()
        
        return jsonify({
            'kb_id': kb.kb_id,
            'message': 'Knowledge base created successfully',
            'knowledge_base': kb.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/bases', methods=['GET'])
def list_knowledge_bases():
    """List all knowledge bases"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        query = KnowledgeBase.query
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        kbs = query.order_by(KnowledgeBase.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'knowledge_bases': [kb.to_dict() for kb in kbs.items],
            'total': kbs.total,
            'pages': kbs.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/bases/<kb_id>', methods=['GET'])
def get_knowledge_base(kb_id):
    """Get knowledge base details"""
    try:
        kb = KnowledgeBase.query.filter_by(kb_id=kb_id).first()
        
        if not kb:
            return jsonify({'error': 'Knowledge base not found'}), 404
        
        # Get associated documents
        documents = Document.query.filter_by(kb_id=kb_id).all()
        
        response = kb.to_dict()
        response['documents'] = [doc.to_dict() for doc in documents]
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/bases/<kb_id>', methods=['PUT'])
def update_knowledge_base(kb_id):
    """Update knowledge base"""
    try:
        kb = KnowledgeBase.query.filter_by(kb_id=kb_id).first()
        
        if not kb:
            return jsonify({'error': 'Knowledge base not found'}), 404
        
        data = request.get_json() or {}
        
        # Update allowed fields
        if 'name' in data:
            kb.name = data['name']
        if 'description' in data:
            kb.description = data['description']
        if 'is_active' in data:
            kb.is_active = data['is_active']
        
        kb.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Knowledge base updated successfully',
            'knowledge_base': kb.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/bases/<kb_id>', methods=['DELETE'])
def delete_knowledge_base(kb_id):
    """Delete knowledge base and all associated data"""
    try:
        kb = KnowledgeBase.query.filter_by(kb_id=kb_id).first()
        
        if not kb:
            return jsonify({'error': 'Knowledge base not found'}), 404
        
        # Delete associated documents and chunks (cascade should handle this)
        documents = Document.query.filter_by(kb_id=kb_id).all()
        for doc in documents:
            db.session.delete(doc)
        
        # Delete knowledge base
        db.session.delete(kb)
        db.session.commit()
        
        return jsonify({'message': 'Knowledge base deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/search', methods=['POST'])
def search_knowledge():
    """Search across knowledge bases"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Search query is required'}), 400
        
        query_text = data['query']
        kb_id = data.get('kb_id')  # Optional: search specific KB
        similarity_threshold = data.get('similarity_threshold', 0.7)
        max_results = data.get('max_results', 10)
        
        # Perform search
        start_time = datetime.utcnow()
        results = embedding_service.search_similar_chunks(
            query_text, kb_id, similarity_threshold, max_results
        )
        end_time = datetime.utcnow()
        
        search_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Save search query
        search_query = SearchQuery(
            query_id=str(uuid.uuid4()),
            query_text=query_text,
            kb_id=kb_id,
            similarity_threshold=similarity_threshold,
            max_results=max_results,
            results=results,
            result_count=len(results),
            search_time_ms=search_time_ms
        )
        
        db.session.add(search_query)
        db.session.commit()
        
        return jsonify({
            'query_id': search_query.query_id,
            'results': results,
            'result_count': len(results),
            'search_time_ms': search_time_ms
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/process', methods=['POST'])
def process_content():
    """Process content into knowledge base"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Create processing job
        job = ProcessingJob(
            job_id=str(uuid.uuid4()),
            job_type=data.get('job_type', 'document_processing'),
            input_data=data,
            config=data.get('config', {})
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Start processing asynchronously
        knowledge_processor.start_processing_job(job.job_id)
        
        return jsonify({
            'job_id': job.job_id,
            'status': 'started',
            'message': 'Processing job started'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/jobs/<job_id>', methods=['GET'])
def get_processing_job(job_id):
    """Get processing job status"""
    try:
        job = ProcessingJob.query.filter_by(job_id=job_id).first()
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify(job.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/jobs', methods=['GET'])
def list_processing_jobs():
    """List processing jobs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        job_type = request.args.get('job_type')
        
        query = ProcessingJob.query
        
        if status:
            query = query.filter_by(status=status)
        
        if job_type:
            query = query.filter_by(job_type=job_type)
        
        jobs = query.order_by(ProcessingJob.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'jobs': [job.to_dict() for job in jobs.items],
            'total': jobs.total,
            'pages': jobs.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/stats', methods=['GET'])
def get_knowledge_stats():
    """Get knowledge base statistics"""
    try:
        # Overall statistics
        total_kbs = KnowledgeBase.query.count()
        active_kbs = KnowledgeBase.query.filter_by(is_active=True).count()
        total_documents = Document.query.count()
        total_chunks = DocumentChunk.query.count()
        
        # Processing statistics
        pending_jobs = ProcessingJob.query.filter_by(status='pending').count()
        running_jobs = ProcessingJob.query.filter_by(status='running').count()
        completed_jobs = ProcessingJob.query.filter_by(status='completed').count()
        failed_jobs = ProcessingJob.query.filter_by(status='failed').count()
        
        # Embedding statistics
        embedded_chunks = DocumentChunk.query.filter_by(embedding_status='completed').count()
        pending_embeddings = DocumentChunk.query.filter_by(embedding_status='pending').count()
        
        # Recent activity
        recent_searches = SearchQuery.query.order_by(
            SearchQuery.created_at.desc()
        ).limit(10).all()
        
        return jsonify({
            'knowledge_bases': {
                'total': total_kbs,
                'active': active_kbs
            },
            'content': {
                'total_documents': total_documents,
                'total_chunks': total_chunks,
                'embedded_chunks': embedded_chunks,
                'pending_embeddings': pending_embeddings
            },
            'processing': {
                'pending_jobs': pending_jobs,
                'running_jobs': running_jobs,
                'completed_jobs': completed_jobs,
                'failed_jobs': failed_jobs
            },
            'recent_searches': [search.to_dict() for search in recent_searches]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/export/<kb_id>', methods=['GET'])
def export_knowledge_base(kb_id):
    """Export knowledge base data"""
    try:
        kb = KnowledgeBase.query.filter_by(kb_id=kb_id).first()
        
        if not kb:
            return jsonify({'error': 'Knowledge base not found'}), 404
        
        # Get all documents and chunks
        documents = Document.query.filter_by(kb_id=kb_id).all()
        
        export_data = {
            'knowledge_base': kb.to_dict(),
            'documents': []
        }
        
        for doc in documents:
            doc_data = doc.to_dict()
            chunks = DocumentChunk.query.filter_by(document_id=doc.document_id).all()
            doc_data['chunks'] = [chunk.to_dict() for chunk in chunks]
            export_data['documents'].append(doc_data)
        
        return jsonify(export_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@knowledge_bp.route('/import', methods=['POST'])
def import_knowledge_base():
    """Import knowledge base data"""
    try:
        data = request.get_json()
        
        if not data or 'knowledge_base' not in data:
            return jsonify({'error': 'Knowledge base data is required'}), 400
        
        # Start import job
        job = ProcessingJob(
            job_id=str(uuid.uuid4()),
            job_type='knowledge_import',
            input_data=data,
            config={}
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Start import processing
        knowledge_processor.start_import_job(job.job_id)
        
        return jsonify({
            'job_id': job.job_id,
            'status': 'started',
            'message': 'Import job started'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

