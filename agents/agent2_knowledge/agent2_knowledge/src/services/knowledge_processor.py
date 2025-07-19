"""
Knowledge Processor Service for Agent 2: Knowledge Base Creator
"""

import uuid
import threading
import time
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
import re
from src.models.knowledge import db, Document, DocumentChunk, ProcessingJob, KnowledgeBase

class KnowledgeProcessorService:
    """Service for processing documents into knowledge base format"""
    
    def __init__(self):
        self.processing_threads = {}
        self.chunk_size = 1000
        self.chunk_overlap = 200
        
    def start_processing_job(self, job_id: str):
        """Start processing a job asynchronously"""
        def process_job():
            try:
                # Get job from database
                job = ProcessingJob.query.filter_by(job_id=job_id).first()
                if not job:
                    return
                
                # Update status
                job.status = 'running'
                job.started_at = datetime.utcnow()
                db.session.commit()
                
                # Process based on job type
                if job.job_type == 'document_processing':
                    result = self.process_document_job(job)
                elif job.job_type == 'knowledge_import':
                    result = self.process_import_job(job)
                else:
                    result = {'success': False, 'error': f'Unknown job type: {job.job_type}'}
                
                # Update job with results
                if result['success']:
                    job.status = 'completed'
                    job.output_data = result.get('output', {})
                    job.progress = 100
                else:
                    job.status = 'failed'
                    job.error_message = result.get('error')
                
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
                if job_id in self.processing_threads:
                    del self.processing_threads[job_id]
        
        # Start processing in separate thread
        thread = threading.Thread(target=process_job, daemon=True)
        thread.start()
        self.processing_threads[job_id] = thread
    
    def process_document_job(self, job: ProcessingJob) -> Dict[str, Any]:
        """Process a document processing job"""
        try:
            input_data = job.input_data
            document_id = input_data.get('document_id')
            content = input_data.get('content')
            kb_config = input_data.get('kb_config', {})
            
            if document_id:
                return self.process_document_by_id(document_id, kb_config)
            elif content:
                return self.process_content_directly(content, kb_config)
            else:
                return {'success': False, 'error': 'No document ID or content provided'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def process_import_job(self, job: ProcessingJob) -> Dict[str, Any]:
        """Process a knowledge import job"""
        try:
            import_data = job.input_data
            kb_data = import_data.get('knowledge_base')
            documents_data = import_data.get('documents', [])
            
            # Create or update knowledge base
            kb = self.import_knowledge_base(kb_data)
            
            # Import documents
            imported_docs = []
            for doc_data in documents_data:
                doc = self.import_document(doc_data, kb.kb_id)
                if doc:
                    imported_docs.append(doc.document_id)
            
            return {
                'success': True,
                'output': {
                    'kb_id': kb.kb_id,
                    'imported_documents': imported_docs,
                    'document_count': len(imported_docs)
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def process_document_by_id(self, document_id: str, kb_config: Dict[str, Any]) -> Dict[str, Any]:
        """Process a document by its ID"""
        try:
            document = Document.query.filter_by(document_id=document_id).first()
            if not document:
                return {'success': False, 'error': 'Document not found'}
            
            # Update processing status
            document.processing_status = 'processing'
            db.session.commit()
            
            # Get content
            content = document.processed_content or document.raw_content
            if not content:
                document.processing_status = 'failed'
                document.error_message = 'No content to process'
                db.session.commit()
                return {'success': False, 'error': 'No content to process'}
            
            # Process content into chunks
            chunks = self.create_chunks(content, kb_config)
            
            # Save chunks to database
            chunk_count = 0
            for i, chunk_data in enumerate(chunks):
                chunk = DocumentChunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document_id,
                    chunk_index=i,
                    chunk_type=chunk_data.get('type', 'text'),
                    content=chunk_data['content'],
                    content_length=len(chunk_data['content']),
                    start_position=chunk_data.get('start_position'),
                    end_position=chunk_data.get('end_position'),
                    meta_data=chunk_data.get('metadata', {})
                )
                
                db.session.add(chunk)
                chunk_count += 1
            
            # Update document
            document.processing_status = 'completed'
            document.chunk_count = chunk_count
            document.processed_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'success': True,
                'output': {
                    'document_id': document_id,
                    'chunk_count': chunk_count,
                    'processing_time': (datetime.utcnow() - document.created_at).total_seconds()
                }
            }
            
        except Exception as e:
            # Update document with error
            document = Document.query.filter_by(document_id=document_id).first()
            if document:
                document.processing_status = 'failed'
                document.error_message = str(e)
                db.session.commit()
            
            return {'success': False, 'error': str(e)}
    
    def process_content_directly(self, content: str, kb_config: Dict[str, Any]) -> Dict[str, Any]:
        """Process content directly without saving to database"""
        try:
            chunks = self.create_chunks(content, kb_config)
            
            return {
                'success': True,
                'output': {
                    'chunks': chunks,
                    'chunk_count': len(chunks)
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_chunks(self, content: str, kb_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks from content"""
        chunk_size = kb_config.get('chunk_size', self.chunk_size)
        chunk_overlap = kb_config.get('chunk_overlap', self.chunk_overlap)
        
        # Clean and prepare content
        cleaned_content = self.clean_content(content)
        
        # Split into chunks
        chunks = []
        
        # Try to split by semantic boundaries first
        semantic_chunks = self.split_by_semantic_boundaries(cleaned_content)
        
        # Further split large chunks if needed
        for semantic_chunk in semantic_chunks:
            if len(semantic_chunk['content']) <= chunk_size:
                chunks.append(semantic_chunk)
            else:
                # Split large chunk into smaller pieces
                sub_chunks = self.split_large_chunk(semantic_chunk['content'], chunk_size, chunk_overlap)
                for i, sub_chunk in enumerate(sub_chunks):
                    chunks.append({
                        'content': sub_chunk,
                        'type': semantic_chunk.get('type', 'text'),
                        'metadata': {
                            **semantic_chunk.get('metadata', {}),
                            'sub_chunk_index': i,
                            'parent_chunk': True
                        }
                    })
        
        # Add position information
        current_position = 0
        for chunk in chunks:
            chunk['start_position'] = current_position
            chunk['end_position'] = current_position + len(chunk['content'])
            current_position = chunk['end_position']
        
        return chunks
    
    def clean_content(self, content: str) -> str:
        """Clean and normalize content"""
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove HTML tags if present
        content = re.sub(r'<[^>]+>', '', content)
        
        # Normalize line breaks
        content = re.sub(r'\r\n|\r|\n', '\n', content)
        
        # Remove excessive line breaks
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        return content.strip()
    
    def split_by_semantic_boundaries(self, content: str) -> List[Dict[str, Any]]:
        """Split content by semantic boundaries (paragraphs, sections, etc.)"""
        chunks = []
        
        # Split by double line breaks (paragraphs)
        paragraphs = content.split('\n\n')
        
        current_chunk = ""
        current_metadata = {}
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Detect headers
            if self.is_header(paragraph):
                # Save current chunk if it exists
                if current_chunk:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'type': 'text',
                        'metadata': current_metadata
                    })
                
                # Start new chunk with header
                current_chunk = paragraph + '\n\n'
                current_metadata = {
                    'has_header': True,
                    'header_text': paragraph
                }
            else:
                # Add paragraph to current chunk
                current_chunk += paragraph + '\n\n'
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'content': current_chunk.strip(),
                'type': 'text',
                'metadata': current_metadata
            })
        
        return chunks
    
    def is_header(self, text: str) -> bool:
        """Detect if text is likely a header"""
        # Simple heuristics for header detection
        if len(text) > 100:  # Headers are usually short
            return False
        
        # Check for common header patterns
        header_patterns = [
            r'^#{1,6}\s+',  # Markdown headers
            r'^[A-Z][A-Z\s]+$',  # ALL CAPS
            r'^\d+\.\s+[A-Z]',  # Numbered sections
            r'^[A-Z][^.!?]*$'  # Title case without punctuation
        ]
        
        for pattern in header_patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def split_large_chunk(self, content: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """Split large content into smaller chunks with overlap"""
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(content):
                # Look for sentence endings within the last 200 characters
                search_start = max(end - 200, start)
                sentence_end = self.find_sentence_boundary(content, search_start, end)
                if sentence_end > start:
                    end = sentence_end
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = max(start + 1, end - chunk_overlap)
            
            # Prevent infinite loop
            if start >= len(content):
                break
        
        return chunks
    
    def find_sentence_boundary(self, content: str, start: int, end: int) -> int:
        """Find the best sentence boundary within a range"""
        # Look for sentence endings
        sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
        
        best_pos = -1
        for ending in sentence_endings:
            pos = content.rfind(ending, start, end)
            if pos > best_pos:
                best_pos = pos + len(ending)
        
        return best_pos if best_pos > start else end
    
    def import_knowledge_base(self, kb_data: Dict[str, Any]) -> KnowledgeBase:
        """Import or create knowledge base"""
        kb_id = kb_data.get('kb_id')
        
        # Check if knowledge base already exists
        kb = KnowledgeBase.query.filter_by(kb_id=kb_id).first()
        
        if kb:
            # Update existing knowledge base
            kb.name = kb_data.get('name', kb.name)
            kb.description = kb_data.get('description', kb.description)
            kb.updated_at = datetime.utcnow()
        else:
            # Create new knowledge base
            kb = KnowledgeBase(
                kb_id=kb_id or str(uuid.uuid4()),
                name=kb_data['name'],
                description=kb_data.get('description', ''),
                embedding_model=kb_data.get('embedding_model', 'text-embedding-ada-002'),
                chunk_size=kb_data.get('chunk_size', 1000),
                chunk_overlap=kb_data.get('chunk_overlap', 200)
            )
            db.session.add(kb)
        
        db.session.commit()
        return kb
    
    def import_document(self, doc_data: Dict[str, Any], kb_id: str) -> Optional[Document]:
        """Import a document with its chunks"""
        try:
            document_id = doc_data.get('document_id')
            
            # Check if document already exists
            document = Document.query.filter_by(document_id=document_id).first()
            
            if document:
                # Update existing document
                document.title = doc_data.get('title', document.title)
                document.meta_data = doc_data.get('meta_data', document.meta_data)
            else:
                # Create new document
                document = Document(
                    document_id=document_id or str(uuid.uuid4()),
                    title=doc_data['title'],
                    source_type=doc_data.get('source_type', 'imported'),
                    source_path=doc_data.get('source_path'),
                    content_type=doc_data.get('content_type'),
                    raw_content=doc_data.get('raw_content'),
                    processed_content=doc_data.get('processed_content'),
                    meta_data=doc_data.get('meta_data', {}),
                    content_hash=doc_data.get('content_hash'),
                    processing_status='completed'
                )
                db.session.add(document)
            
            # Import chunks
            chunks_data = doc_data.get('chunks', [])
            chunk_count = 0
            
            for chunk_data in chunks_data:
                chunk_id = chunk_data.get('chunk_id')
                
                # Check if chunk already exists
                chunk = DocumentChunk.query.filter_by(chunk_id=chunk_id).first()
                
                if not chunk:
                    chunk = DocumentChunk(
                        chunk_id=chunk_id or str(uuid.uuid4()),
                        document_id=document.document_id,
                        chunk_index=chunk_data.get('chunk_index', 0),
                        chunk_type=chunk_data.get('chunk_type', 'text'),
                        content=chunk_data['content'],
                        content_length=chunk_data.get('content_length', len(chunk_data['content'])),
                        start_position=chunk_data.get('start_position'),
                        end_position=chunk_data.get('end_position'),
                        embedding_vector=chunk_data.get('embedding_vector'),
                        embedding_model=chunk_data.get('embedding_model'),
                        embedding_status=chunk_data.get('embedding_status', 'pending'),
                        meta_data=chunk_data.get('meta_data', {})
                    )
                    db.session.add(chunk)
                    chunk_count += 1
            
            # Update document chunk count
            document.chunk_count = chunk_count
            document.processed_at = datetime.utcnow()
            
            db.session.commit()
            return document
            
        except Exception as e:
            print(f"Error importing document: {e}")
            return None
    
    def start_import_job(self, job_id: str):
        """Start an import job asynchronously"""
        self.start_processing_job(job_id)

