"""
Embedding Service for Agent 2: Knowledge Base Creator
"""

import os
import json
import threading
import time
try:
    import numpy as np
except ImportError:
    np = None
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
try:
    import openai
except ImportError:
    openai = None
from src.models.knowledge import db, DocumentChunk, Document, ProcessingJob

class EmbeddingService:
    """Service for generating and managing embeddings"""
    
    def __init__(self):
        # Initialize OpenAI client
        try:
            self.client = openai.OpenAI(
                api_key=os.getenv('OPENAI_API_KEY'),
                base_url=os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
            )
        except Exception as e:
            print(f"Warning: Could not initialize OpenAI client: {e}")
            self.client = None
        
        self.default_model = 'text-embedding-ada-002'
        self.embedding_threads = {}
        
        # Available models
        self.available_models = [
            'text-embedding-ada-002',
            'text-embedding-3-small',
            'text-embedding-3-large'
        ]
    
    def start_embedding_generation(self, job_id: str, chunk_ids: List[str]):
        """Start embedding generation for chunks asynchronously"""
        def generate_embeddings():
            try:
                # Get job from database
                job = ProcessingJob.query.filter_by(job_id=job_id).first()
                if not job:
                    return
                
                # Update status
                job.status = 'running'
                job.started_at = datetime.utcnow()
                job.progress = 0
                db.session.commit()
                
                total_chunks = len(chunk_ids)
                processed_chunks = 0
                successful_chunks = 0
                failed_chunks = 0
                
                # Process chunks in batches
                batch_size = 10  # Process 10 chunks at a time
                
                for i in range(0, len(chunk_ids), batch_size):
                    batch_chunk_ids = chunk_ids[i:i + batch_size]
                    
                    # Process batch
                    batch_results = self.process_chunk_batch(batch_chunk_ids)
                    
                    # Update counters
                    for result in batch_results:
                        processed_chunks += 1
                        if result['success']:
                            successful_chunks += 1
                        else:
                            failed_chunks += 1
                    
                    # Update progress
                    progress = int((processed_chunks / total_chunks) * 100)
                    job.progress = progress
                    db.session.commit()
                    
                    # Small delay to prevent rate limiting
                    time.sleep(0.1)
                
                # Update job with final results
                job.status = 'completed'
                job.progress = 100
                job.output_data = {
                    'total_chunks': total_chunks,
                    'successful_chunks': successful_chunks,
                    'failed_chunks': failed_chunks,
                    'success_rate': round((successful_chunks / total_chunks * 100) if total_chunks > 0 else 0, 2)
                }
                job.completed_at = datetime.utcnow()
                db.session.commit()
                
            except Exception as e:
                # Update with error
                job = ProcessingJob.query.filter_by(job_id=job_id).first()
                if job:
                    job.status = 'failed'
                    job.error_message = str(e)
                    job.completed_at = datetime.utcnow()
                    db.session.commit()
            
            finally:
                # Clean up thread reference
                if job_id in self.embedding_threads:
                    del self.embedding_threads[job_id]
        
        # Start processing in separate thread
        thread = threading.Thread(target=generate_embeddings, daemon=True)
        thread.start()
        self.embedding_threads[job_id] = thread
    
    def process_chunk_batch(self, chunk_ids: List[str]) -> List[Dict[str, Any]]:
        """Process a batch of chunks for embedding generation"""
        results = []
        
        for chunk_id in chunk_ids:
            result = self.generate_single_embedding(chunk_id)
            results.append({
                'chunk_id': chunk_id,
                'success': result['success'],
                'error': result.get('error')
            })
        
        return results
    
    def generate_single_embedding(self, chunk_id: str, model: str = None) -> Dict[str, Any]:
        """Generate embedding for a single chunk"""
        try:
            if not self.client:
                return {'success': False, 'error': 'OpenAI client not available'}
            
            # Get chunk from database
            chunk = DocumentChunk.query.filter_by(chunk_id=chunk_id).first()
            if not chunk:
                return {'success': False, 'error': 'Chunk not found'}
            
            # Use default model if not specified
            if not model:
                model = self.default_model
            
            # Update status
            chunk.embedding_status = 'processing'
            db.session.commit()
            
            # Generate embedding
            response = self.client.embeddings.create(
                input=chunk.content,
                model=model
            )
            
            # Extract embedding vector
            embedding_vector = response.data[0].embedding
            
            # Save embedding to chunk
            chunk.embedding_vector = json.dumps(embedding_vector)
            chunk.embedding_model = model
            chunk.embedding_status = 'completed'
            chunk.embedded_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'success': True,
                'model': model,
                'dimension': len(embedding_vector)
            }
            
        except Exception as e:
            # Update chunk with error
            chunk = DocumentChunk.query.filter_by(chunk_id=chunk_id).first()
            if chunk:
                chunk.embedding_status = 'failed'
                db.session.commit()
            
            return {'success': False, 'error': str(e)}
    
    def search_similar_chunks(self, query_text: str, kb_id: str = None, document_id: str = None,
                            similarity_threshold: float = 0.7, max_results: int = 10,
                            include_embeddings: bool = False) -> List[Dict[str, Any]]:
        """Search for similar chunks using embedding similarity"""
        try:
            if not self.client:
                print("Warning: OpenAI client not available for similarity search")
                return []
            
            # Generate embedding for query
            response = self.client.embeddings.create(
                input=query_text,
                model=self.default_model
            )
            
            query_embedding = response.data[0].embedding
            
            # Get chunks with embeddings
            query = DocumentChunk.query.filter_by(embedding_status='completed')
            
            # Filter by knowledge base or document if specified
            if kb_id or document_id:
                query = query.join(Document)
                if kb_id:
                    query = query.filter(Document.kb_id == kb_id)
                if document_id:
                    query = query.filter(Document.document_id == document_id)
            
            chunks = query.all()
            
            # Calculate similarities
            similarities = []
            
            for chunk in chunks:
                if not chunk.embedding_vector:
                    continue
                
                chunk_embedding = json.loads(chunk.embedding_vector)
                similarity = self.cosine_similarity(query_embedding, chunk_embedding)
                
                if similarity >= similarity_threshold:
                    result = {
                        'chunk_id': chunk.chunk_id,
                        'document_id': chunk.document_id,
                        'content': chunk.content,
                        'similarity_score': float(similarity),
                        'chunk_index': chunk.chunk_index,
                        'chunk_type': chunk.chunk_type,
                        'meta_data': chunk.meta_data
                    }
                    
                    # Include document info
                    if chunk.document:
                        result['document_title'] = chunk.document.title
                        result['document_source'] = chunk.document.source_path
                    
                    # Include embedding if requested
                    if include_embeddings:
                        result['embedding_vector'] = chunk_embedding
                    
                    similarities.append(result)
            
            # Sort by similarity score (descending) and limit results
            similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similarities[:max_results]
            
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []
    
    def find_similar_to_chunk(self, chunk_id: str, similarity_threshold: float = 0.7,
                            max_results: int = 10, exclude_same_document: bool = True) -> List[Dict[str, Any]]:
        """Find chunks similar to a specific chunk"""
        try:
            # Get source chunk
            source_chunk = DocumentChunk.query.filter_by(chunk_id=chunk_id).first()
            if not source_chunk or not source_chunk.embedding_vector:
                return []
            
            source_embedding = json.loads(source_chunk.embedding_vector)
            
            # Get all other chunks with embeddings
            query = DocumentChunk.query.filter_by(embedding_status='completed')
            
            # Exclude the source chunk itself
            query = query.filter(DocumentChunk.chunk_id != chunk_id)
            
            # Exclude same document if requested
            if exclude_same_document:
                query = query.filter(DocumentChunk.document_id != source_chunk.document_id)
            
            chunks = query.all()
            
            # Calculate similarities
            similarities = []
            
            for chunk in chunks:
                if not chunk.embedding_vector:
                    continue
                
                chunk_embedding = json.loads(chunk.embedding_vector)
                similarity = self.cosine_similarity(source_embedding, chunk_embedding)
                
                if similarity >= similarity_threshold:
                    result = {
                        'chunk_id': chunk.chunk_id,
                        'document_id': chunk.document_id,
                        'content': chunk.content,
                        'similarity_score': float(similarity),
                        'chunk_index': chunk.chunk_index,
                        'chunk_type': chunk.chunk_type,
                        'meta_data': chunk.meta_data
                    }
                    
                    # Include document info
                    if chunk.document:
                        result['document_title'] = chunk.document.title
                        result['document_source'] = chunk.document.source_path
                    
                    similarities.append(result)
            
            # Sort by similarity score (descending) and limit results
            similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similarities[:max_results]
            
        except Exception as e:
            print(f"Error finding similar chunks: {e}")
            return []
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            # Convert to numpy arrays
            a = np.array(vec1)
            b = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)
            
        except Exception as e:
            print(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available embedding models"""
        return [
            {
                'model': model,
                'is_default': model == self.default_model,
                'description': self.get_model_description(model)
            }
            for model in self.available_models
        ]
    
    def get_model_description(self, model: str) -> str:
        """Get description for an embedding model"""
        descriptions = {
            'text-embedding-ada-002': 'OpenAI Ada v2 - General purpose embedding model',
            'text-embedding-3-small': 'OpenAI v3 Small - Improved performance, smaller size',
            'text-embedding-3-large': 'OpenAI v3 Large - Best performance, larger size'
        }
        return descriptions.get(model, 'Unknown model')
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get embedding statistics"""
        try:
            # Count chunks by embedding status
            total_chunks = DocumentChunk.query.count()
            embedded_chunks = DocumentChunk.query.filter_by(embedding_status='completed').count()
            pending_chunks = DocumentChunk.query.filter_by(embedding_status='pending').count()
            failed_chunks = DocumentChunk.query.filter_by(embedding_status='failed').count()
            
            # Get model distribution
            from sqlalchemy import func
            model_stats = db.session.query(
                DocumentChunk.embedding_model,
                func.count(DocumentChunk.id).label('count')
            ).filter_by(embedding_status='completed').group_by(
                DocumentChunk.embedding_model
            ).all()
            
            return {
                'total_chunks': total_chunks,
                'embedded_chunks': embedded_chunks,
                'pending_chunks': pending_chunks,
                'failed_chunks': failed_chunks,
                'completion_rate': round((embedded_chunks / total_chunks * 100) if total_chunks > 0 else 0, 2),
                'model_distribution': [
                    {'model': model, 'count': count} for model, count in model_stats
                ]
            }
            
        except Exception as e:
            print(f"Error getting embedding stats: {e}")
            return {}
    
    def batch_generate_embeddings(self, chunk_ids: List[str], model: str = None) -> Dict[str, Any]:
        """Generate embeddings for multiple chunks"""
        if not model:
            model = self.default_model
        
        successful = 0
        failed = 0
        errors = []
        
        for chunk_id in chunk_ids:
            result = self.generate_single_embedding(chunk_id, model)
            if result['success']:
                successful += 1
            else:
                failed += 1
                errors.append({
                    'chunk_id': chunk_id,
                    'error': result.get('error')
                })
        
        return {
            'total_processed': len(chunk_ids),
            'successful': successful,
            'failed': failed,
            'success_rate': round((successful / len(chunk_ids) * 100) if chunk_ids else 0, 2),
            'errors': errors
        }
    
    def recompute_embeddings(self, model: str = None, force: bool = False) -> Dict[str, Any]:
        """Recompute embeddings for all chunks"""
        if not model:
            model = self.default_model
        
        # Get chunks to recompute
        query = DocumentChunk.query
        
        if not force:
            # Only recompute failed or pending embeddings
            query = query.filter(DocumentChunk.embedding_status.in_(['pending', 'failed']))
        
        chunks = query.all()
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        
        if not chunk_ids:
            return {
                'message': 'No chunks to recompute',
                'total_processed': 0
            }
        
        # Start batch processing
        return self.batch_generate_embeddings(chunk_ids, model)

