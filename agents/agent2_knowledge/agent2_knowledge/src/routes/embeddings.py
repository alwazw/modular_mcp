"""
Embeddings routes for Agent 2: Knowledge Base Creator
"""

import uuid
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from src.models.knowledge import db, DocumentChunk, ProcessingJob, SearchQuery
from src.services.embedding_service import EmbeddingService

embeddings_bp = Blueprint('embeddings', __name__)

# Initialize embedding service
embedding_service = EmbeddingService()

@embeddings_bp.route('/generate', methods=['POST'])
def generate_embeddings():
    """Generate embeddings for chunks"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Get parameters
        chunk_ids = data.get('chunk_ids', [])
        document_id = data.get('document_id')
        kb_id = data.get('kb_id')
        force_regenerate = data.get('force_regenerate', False)
        
        # Build query for chunks to process
        query = DocumentChunk.query
        
        if chunk_ids:
            query = query.filter(DocumentChunk.chunk_id.in_(chunk_ids))
        elif document_id:
            query = query.filter_by(document_id=document_id)
        elif kb_id:
            # Join with Document to filter by kb_id
            from src.models.knowledge import Document
            query = query.join(Document).filter(Document.kb_id == kb_id)
        else:
            return jsonify({'error': 'Must specify chunk_ids, document_id, or kb_id'}), 400
        
        # Filter by embedding status if not forcing regeneration
        if not force_regenerate:
            query = query.filter(DocumentChunk.embedding_status.in_(['pending', 'failed']))
        
        chunks = query.all()
        
        if not chunks:
            return jsonify({
                'message': 'No chunks found to process',
                'processed_count': 0
            })
        
        # Create processing job
        job = ProcessingJob(
            job_id=str(uuid.uuid4()),
            job_type='embedding_generation',
            input_data={
                'chunk_count': len(chunks),
                'chunk_ids': [chunk.chunk_id for chunk in chunks],
                'force_regenerate': force_regenerate
            },
            config=data.get('config', {})
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Start embedding generation
        embedding_service.start_embedding_generation(job.job_id, [chunk.chunk_id for chunk in chunks])
        
        return jsonify({
            'job_id': job.job_id,
            'chunk_count': len(chunks),
            'status': 'started',
            'message': 'Embedding generation started'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@embeddings_bp.route('/search', methods=['POST'])
def search_embeddings():
    """Search for similar chunks using embeddings"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Search query is required'}), 400
        
        query_text = data['query']
        kb_id = data.get('kb_id')
        document_id = data.get('document_id')
        similarity_threshold = data.get('similarity_threshold', 0.7)
        max_results = data.get('max_results', 10)
        include_embeddings = data.get('include_embeddings', False)
        
        # Perform similarity search
        start_time = datetime.utcnow()
        results = embedding_service.search_similar_chunks(
            query_text=query_text,
            kb_id=kb_id,
            document_id=document_id,
            similarity_threshold=similarity_threshold,
            max_results=max_results,
            include_embeddings=include_embeddings
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
            'query_text': query_text,
            'results': results,
            'result_count': len(results),
            'search_time_ms': search_time_ms,
            'parameters': {
                'kb_id': kb_id,
                'document_id': document_id,
                'similarity_threshold': similarity_threshold,
                'max_results': max_results
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@embeddings_bp.route('/chunks/<chunk_id>/embedding', methods=['GET'])
def get_chunk_embedding(chunk_id):
    """Get embedding for a specific chunk"""
    try:
        chunk = DocumentChunk.query.filter_by(chunk_id=chunk_id).first()
        
        if not chunk:
            return jsonify({'error': 'Chunk not found'}), 404
        
        if chunk.embedding_status != 'completed' or not chunk.embedding_vector:
            return jsonify({
                'error': 'Embedding not available',
                'status': chunk.embedding_status
            }), 404
        
        # Parse embedding vector
        embedding_vector = json.loads(chunk.embedding_vector) if chunk.embedding_vector else None
        
        return jsonify({
            'chunk_id': chunk_id,
            'embedding_vector': embedding_vector,
            'embedding_model': chunk.embedding_model,
            'embedding_status': chunk.embedding_status,
            'embedded_at': chunk.embedded_at.isoformat() if chunk.embedded_at else None,
            'vector_dimension': len(embedding_vector) if embedding_vector else 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@embeddings_bp.route('/chunks/<chunk_id>/embedding', methods=['POST'])
def generate_chunk_embedding(chunk_id):
    """Generate embedding for a specific chunk"""
    try:
        chunk = DocumentChunk.query.filter_by(chunk_id=chunk_id).first()
        
        if not chunk:
            return jsonify({'error': 'Chunk not found'}), 404
        
        data = request.get_json() or {}
        force_regenerate = data.get('force_regenerate', False)
        
        # Check if embedding already exists
        if chunk.embedding_status == 'completed' and chunk.embedding_vector and not force_regenerate:
            return jsonify({
                'message': 'Embedding already exists',
                'chunk_id': chunk_id,
                'status': 'completed'
            })
        
        # Generate embedding
        result = embedding_service.generate_single_embedding(chunk_id)
        
        if result['success']:
            return jsonify({
                'chunk_id': chunk_id,
                'status': 'completed',
                'message': 'Embedding generated successfully',
                'embedding_model': result.get('model'),
                'vector_dimension': result.get('dimension')
            })
        else:
            return jsonify({
                'error': result.get('error', 'Failed to generate embedding'),
                'chunk_id': chunk_id
            }), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@embeddings_bp.route('/chunks/<chunk_id>/similar', methods=['GET'])
def find_similar_chunks(chunk_id):
    """Find chunks similar to a specific chunk"""
    try:
        chunk = DocumentChunk.query.filter_by(chunk_id=chunk_id).first()
        
        if not chunk:
            return jsonify({'error': 'Chunk not found'}), 404
        
        if chunk.embedding_status != 'completed' or not chunk.embedding_vector:
            return jsonify({
                'error': 'Chunk embedding not available',
                'status': chunk.embedding_status
            }), 404
        
        # Get parameters
        similarity_threshold = request.args.get('similarity_threshold', 0.7, type=float)
        max_results = request.args.get('max_results', 10, type=int)
        exclude_same_document = request.args.get('exclude_same_document', 'true').lower() == 'true'
        
        # Find similar chunks
        results = embedding_service.find_similar_to_chunk(
            chunk_id=chunk_id,
            similarity_threshold=similarity_threshold,
            max_results=max_results,
            exclude_same_document=exclude_same_document
        )
        
        return jsonify({
            'source_chunk_id': chunk_id,
            'similar_chunks': results,
            'result_count': len(results),
            'parameters': {
                'similarity_threshold': similarity_threshold,
                'max_results': max_results,
                'exclude_same_document': exclude_same_document
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@embeddings_bp.route('/stats', methods=['GET'])
def get_embedding_stats():
    """Get embedding statistics"""
    try:
        # Overall embedding statistics
        total_chunks = DocumentChunk.query.count()
        embedded_chunks = DocumentChunk.query.filter_by(embedding_status='completed').count()
        pending_chunks = DocumentChunk.query.filter_by(embedding_status='pending').count()
        failed_chunks = DocumentChunk.query.filter_by(embedding_status='failed').count()
        
        # Model statistics
        from sqlalchemy import func
        model_stats = db.session.query(
            DocumentChunk.embedding_model,
            func.count(DocumentChunk.id).label('count')
        ).filter_by(embedding_status='completed').group_by(
            DocumentChunk.embedding_model
        ).all()
        
        # Recent embedding jobs
        recent_jobs = ProcessingJob.query.filter_by(
            job_type='embedding_generation'
        ).order_by(ProcessingJob.created_at.desc()).limit(10).all()
        
        # Recent searches
        recent_searches = SearchQuery.query.order_by(
            SearchQuery.created_at.desc()
        ).limit(10).all()
        
        return jsonify({
            'chunks': {
                'total': total_chunks,
                'embedded': embedded_chunks,
                'pending': pending_chunks,
                'failed': failed_chunks,
                'completion_rate': round((embedded_chunks / total_chunks * 100) if total_chunks > 0 else 0, 2)
            },
            'models': [
                {'model': model, 'count': count} for model, count in model_stats
            ],
            'recent_jobs': [job.to_dict() for job in recent_jobs],
            'recent_searches': [search.to_dict() for search in recent_searches]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@embeddings_bp.route('/models', methods=['GET'])
def list_embedding_models():
    """List available embedding models"""
    try:
        models = embedding_service.get_available_models()
        
        return jsonify({
            'models': models,
            'default_model': embedding_service.default_model
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@embeddings_bp.route('/batch-search', methods=['POST'])
def batch_search():
    """Perform batch similarity search"""
    try:
        data = request.get_json()
        
        if not data or 'queries' not in data:
            return jsonify({'error': 'Queries list is required'}), 400
        
        queries = data['queries']
        if not isinstance(queries, list) or len(queries) == 0:
            return jsonify({'error': 'Queries must be a non-empty list'}), 400
        
        # Common parameters
        kb_id = data.get('kb_id')
        similarity_threshold = data.get('similarity_threshold', 0.7)
        max_results = data.get('max_results', 10)
        
        # Process each query
        results = []
        start_time = datetime.utcnow()
        
        for i, query_text in enumerate(queries):
            if not query_text or not isinstance(query_text, str):
                results.append({
                    'query_index': i,
                    'query_text': query_text,
                    'error': 'Invalid query text'
                })
                continue
            
            try:
                search_results = embedding_service.search_similar_chunks(
                    query_text=query_text,
                    kb_id=kb_id,
                    similarity_threshold=similarity_threshold,
                    max_results=max_results
                )
                
                results.append({
                    'query_index': i,
                    'query_text': query_text,
                    'results': search_results,
                    'result_count': len(search_results)
                })
                
            except Exception as e:
                results.append({
                    'query_index': i,
                    'query_text': query_text,
                    'error': str(e)
                })
        
        end_time = datetime.utcnow()
        total_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return jsonify({
            'batch_results': results,
            'total_queries': len(queries),
            'successful_queries': len([r for r in results if 'error' not in r]),
            'total_time_ms': total_time_ms,
            'parameters': {
                'kb_id': kb_id,
                'similarity_threshold': similarity_threshold,
                'max_results': max_results
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

