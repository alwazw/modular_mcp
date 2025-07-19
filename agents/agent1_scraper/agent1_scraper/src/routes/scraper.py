"""
Scraper routes for Agent 1: Web Scraper & Data Collector
"""

import uuid
import json
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from src.models.scraper import db, ScrapingJob, ScrapedContent, BrowserSession
from src.services.web_scraper import WebScraperService
from src.services.session_manager import SessionManager

scraper_bp = Blueprint('scraper', __name__)

# Initialize services
web_scraper = WebScraperService()
session_manager = SessionManager()

@scraper_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'agent': 'agent1_scraper',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@scraper_bp.route('/jobs', methods=['POST'])
def create_scraping_job():
    """Create a new scraping job"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        # Create job
        job = ScrapingJob(
            job_id=str(uuid.uuid4()),
            url=data['url'],
            job_type=data.get('job_type', 'single_page'),
            priority=data.get('priority', 5),
            scraping_config=data.get('config', {}),
            output_format=data.get('output_format', 'json'),
            max_retries=data.get('max_retries', 3)
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Start scraping asynchronously
        web_scraper.start_scraping_job(job.job_id)
        
        return jsonify({
            'job_id': job.job_id,
            'status': 'created',
            'message': 'Scraping job created and started'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scraper_bp.route('/jobs/<job_id>', methods=['GET'])
def get_scraping_job(job_id):
    """Get scraping job status and results"""
    try:
        job = ScrapingJob.query.filter_by(job_id=job_id).first()
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Get associated content
        content = ScrapedContent.query.filter_by(job_id=job_id).all()
        
        response = job.to_dict()
        response['content'] = [c.to_dict() for c in content]
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scraper_bp.route('/jobs', methods=['GET'])
def list_scraping_jobs():
    """List all scraping jobs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        
        query = ScrapingJob.query
        
        if status:
            query = query.filter_by(status=status)
        
        jobs = query.order_by(ScrapingJob.created_at.desc()).paginate(
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

@scraper_bp.route('/jobs/<job_id>', methods=['DELETE'])
def delete_scraping_job(job_id):
    """Delete a scraping job and its content"""
    try:
        job = ScrapingJob.query.filter_by(job_id=job_id).first()
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Delete associated content
        ScrapedContent.query.filter_by(job_id=job_id).delete()
        
        # Delete job
        db.session.delete(job)
        db.session.commit()
        
        return jsonify({'message': 'Job deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scraper_bp.route('/scrape', methods=['POST'])
def scrape_url():
    """Immediate scraping endpoint (synchronous)"""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url']
        config = data.get('config', {})
        session_id = data.get('session_id')
        
        # Use session if provided
        browser_session = None
        if session_id:
            browser_session = BrowserSession.query.filter_by(session_id=session_id).first()
        
        # Perform scraping
        result = web_scraper.scrape_url(url, config, browser_session)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scraper_bp.route('/extract', methods=['POST'])
def extract_data():
    """Extract specific data from a URL using selectors"""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data or 'selectors' not in data:
            return jsonify({'error': 'URL and selectors are required'}), 400
        
        url = data['url']
        selectors = data['selectors']
        session_id = data.get('session_id')
        
        # Use session if provided
        browser_session = None
        if session_id:
            browser_session = BrowserSession.query.filter_by(session_id=session_id).first()
        
        # Extract data
        result = web_scraper.extract_data(url, selectors, browser_session)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scraper_bp.route('/download', methods=['POST'])
def download_file():
    """Download a file from a URL"""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url']
        filename = data.get('filename')
        session_id = data.get('session_id')
        
        # Use session if provided
        browser_session = None
        if session_id:
            browser_session = BrowserSession.query.filter_by(session_id=session_id).first()
        
        # Download file
        result = web_scraper.download_file(url, filename, browser_session)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scraper_bp.route('/batch', methods=['POST'])
def batch_scrape():
    """Batch scraping for multiple URLs"""
    try:
        data = request.get_json()
        
        if not data or 'urls' not in data:
            return jsonify({'error': 'URLs list is required'}), 400
        
        urls = data['urls']
        config = data.get('config', {})
        session_id = data.get('session_id')
        
        if not isinstance(urls, list) or len(urls) == 0:
            return jsonify({'error': 'URLs must be a non-empty list'}), 400
        
        # Create batch job
        batch_job_id = str(uuid.uuid4())
        jobs = []
        
        for url in urls:
            job = ScrapingJob(
                job_id=str(uuid.uuid4()),
                url=url,
                job_type='batch',
                scraping_config=config,
                metadata={'batch_id': batch_job_id}
            )
            db.session.add(job)
            jobs.append(job.job_id)
        
        db.session.commit()
        
        # Start batch scraping
        web_scraper.start_batch_scraping(jobs, session_id)
        
        return jsonify({
            'batch_id': batch_job_id,
            'job_ids': jobs,
            'status': 'started',
            'message': f'Batch scraping started for {len(urls)} URLs'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scraper_bp.route('/monitor', methods=['GET'])
def monitor_scraping():
    """Get scraping statistics and monitoring info"""
    try:
        # Get job statistics
        total_jobs = ScrapingJob.query.count()
        pending_jobs = ScrapingJob.query.filter_by(status='pending').count()
        running_jobs = ScrapingJob.query.filter_by(status='running').count()
        completed_jobs = ScrapingJob.query.filter_by(status='completed').count()
        failed_jobs = ScrapingJob.query.filter_by(status='failed').count()
        
        # Get recent jobs
        recent_jobs = ScrapingJob.query.order_by(
            ScrapingJob.created_at.desc()
        ).limit(10).all()
        
        # Get active sessions
        active_sessions = BrowserSession.query.filter_by(is_active=True).count()
        
        return jsonify({
            'statistics': {
                'total_jobs': total_jobs,
                'pending_jobs': pending_jobs,
                'running_jobs': running_jobs,
                'completed_jobs': completed_jobs,
                'failed_jobs': failed_jobs,
                'active_sessions': active_sessions
            },
            'recent_jobs': [job.to_dict() for job in recent_jobs],
            'system_status': web_scraper.get_system_status()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scraper_bp.route('/config', methods=['GET'])
def get_scraper_config():
    """Get current scraper configuration"""
    try:
        config = web_scraper.get_config()
        return jsonify(config)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scraper_bp.route('/config', methods=['PUT'])
def update_scraper_config():
    """Update scraper configuration"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Configuration data is required'}), 400
        
        result = web_scraper.update_config(data)
        
        return jsonify({
            'message': 'Configuration updated successfully',
            'config': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

