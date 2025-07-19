"""
Session management routes for Agent 1: Web Scraper & Data Collector
"""

import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from src.models.scraper import db, BrowserSession
from src.services.session_manager import SessionManager

sessions_bp = Blueprint('sessions', __name__)

# Initialize session manager
session_manager = SessionManager()

@sessions_bp.route('/', methods=['POST'])
def create_session():
    """Create a new browser session"""
    try:
        data = request.get_json() or {}
        
        session_name = data.get('session_name', f'Session_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        domain = data.get('domain')
        expires_hours = data.get('expires_hours', 24)
        notes = data.get('notes', '')
        
        # Create session
        session = BrowserSession(
            session_id=str(uuid.uuid4()),
            session_name=session_name,
            domain=domain,
            expires_at=datetime.utcnow() + timedelta(hours=expires_hours),
            notes=notes
        )
        
        db.session.add(session)
        db.session.commit()
        
        # Initialize browser session
        session_manager.create_session(session.session_id, data.get('browser_config', {}))
        
        return jsonify({
            'session_id': session.session_id,
            'session_name': session.session_name,
            'status': 'created',
            'message': 'Browser session created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session information"""
    try:
        session = BrowserSession.query.filter_by(session_id=session_id).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get session status from session manager
        status = session_manager.get_session_status(session_id)
        
        response = session.to_dict()
        response['browser_status'] = status
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/', methods=['GET'])
def list_sessions():
    """List all browser sessions"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        domain = request.args.get('domain')
        
        query = BrowserSession.query
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        if domain:
            query = query.filter_by(domain=domain)
        
        sessions = query.order_by(BrowserSession.last_used.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'sessions': [session.to_dict() for session in sessions.items],
            'total': sessions.total,
            'pages': sessions.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/<session_id>', methods=['PUT'])
def update_session(session_id):
    """Update session information"""
    try:
        session = BrowserSession.query.filter_by(session_id=session_id).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        data = request.get_json() or {}
        
        # Update allowed fields
        if 'session_name' in data:
            session.session_name = data['session_name']
        
        if 'domain' in data:
            session.domain = data['domain']
        
        if 'notes' in data:
            session.notes = data['notes']
        
        if 'is_active' in data:
            session.is_active = data['is_active']
        
        if 'expires_hours' in data:
            session.expires_at = datetime.utcnow() + timedelta(hours=data['expires_hours'])
        
        session.last_used = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Session updated successfully',
            'session': session.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a browser session"""
    try:
        session = BrowserSession.query.filter_by(session_id=session_id).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Close browser session
        session_manager.close_session(session_id)
        
        # Delete database record
        db.session.delete(session)
        db.session.commit()
        
        return jsonify({'message': 'Session deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/<session_id>/login', methods=['POST'])
def login_session(session_id):
    """Perform login for a session"""
    try:
        session = BrowserSession.query.filter_by(session_id=session_id).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        data = request.get_json()
        
        if not data or 'login_url' not in data:
            return jsonify({'error': 'Login URL is required'}), 400
        
        login_url = data['login_url']
        credentials = data.get('credentials', {})
        login_config = data.get('config', {})
        
        # Perform login
        result = session_manager.perform_login(session_id, login_url, credentials, login_config)
        
        if result['success']:
            # Update session status
            session.is_authenticated = True
            session.domain = data.get('domain', session.domain)
            session.last_used = datetime.utcnow()
            
            # Save session data
            session_data = session_manager.get_session_data(session_id)
            session.cookies = session_data.get('cookies')
            session.local_storage = session_data.get('local_storage')
            session.session_storage = session_data.get('session_storage')
            
            db.session.commit()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/<session_id>/navigate', methods=['POST'])
def navigate_session(session_id):
    """Navigate to a URL in a session"""
    try:
        session = BrowserSession.query.filter_by(session_id=session_id).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url']
        wait_for = data.get('wait_for')
        timeout = data.get('timeout', 30)
        
        # Navigate to URL
        result = session_manager.navigate(session_id, url, wait_for, timeout)
        
        # Update session
        session.last_used = datetime.utcnow()
        db.session.commit()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/<session_id>/screenshot', methods=['POST'])
def take_screenshot(session_id):
    """Take a screenshot of the current page"""
    try:
        session = BrowserSession.query.filter_by(session_id=session_id).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        data = request.get_json() or {}
        filename = data.get('filename')
        
        # Take screenshot
        result = session_manager.take_screenshot(session_id, filename)
        
        # Update session
        session.last_used = datetime.utcnow()
        db.session.commit()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/<session_id>/execute', methods=['POST'])
def execute_script(session_id):
    """Execute JavaScript in a session"""
    try:
        session = BrowserSession.query.filter_by(session_id=session_id).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        data = request.get_json()
        
        if not data or 'script' not in data:
            return jsonify({'error': 'Script is required'}), 400
        
        script = data['script']
        
        # Execute script
        result = session_manager.execute_script(session_id, script)
        
        # Update session
        session.last_used = datetime.utcnow()
        db.session.commit()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/<session_id>/cookies', methods=['GET'])
def get_cookies(session_id):
    """Get cookies from a session"""
    try:
        session = BrowserSession.query.filter_by(session_id=session_id).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get current cookies
        cookies = session_manager.get_cookies(session_id)
        
        return jsonify({
            'session_id': session_id,
            'cookies': cookies
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/<session_id>/cookies', methods=['POST'])
def set_cookies(session_id):
    """Set cookies for a session"""
    try:
        session = BrowserSession.query.filter_by(session_id=session_id).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        data = request.get_json()
        
        if not data or 'cookies' not in data:
            return jsonify({'error': 'Cookies are required'}), 400
        
        cookies = data['cookies']
        
        # Set cookies
        result = session_manager.set_cookies(session_id, cookies)
        
        # Update session
        session.last_used = datetime.utcnow()
        db.session.commit()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/<session_id>/save', methods=['POST'])
def save_session(session_id):
    """Save current session state"""
    try:
        session = BrowserSession.query.filter_by(session_id=session_id).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get and save session data
        session_data = session_manager.get_session_data(session_id)
        
        session.cookies = session_data.get('cookies')
        session.local_storage = session_data.get('local_storage')
        session.session_storage = session_data.get('session_storage')
        session.last_used = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Session state saved successfully',
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/<session_id>/restore', methods=['POST'])
def restore_session(session_id):
    """Restore session state"""
    try:
        session = BrowserSession.query.filter_by(session_id=session_id).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Restore session data
        session_data = {
            'cookies': session.cookies,
            'local_storage': session.local_storage,
            'session_storage': session.session_storage
        }
        
        result = session_manager.restore_session_data(session_id, session_data)
        
        # Update session
        session.last_used = datetime.utcnow()
        db.session.commit()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/cleanup', methods=['POST'])
def cleanup_expired_sessions():
    """Clean up expired sessions"""
    try:
        # Find expired sessions
        expired_sessions = BrowserSession.query.filter(
            BrowserSession.expires_at < datetime.utcnow()
        ).all()
        
        cleaned_count = 0
        
        for session in expired_sessions:
            try:
                # Close browser session
                session_manager.close_session(session.session_id)
                
                # Delete database record
                db.session.delete(session)
                cleaned_count += 1
                
            except Exception as e:
                print(f"Error cleaning up session {session.session_id}: {e}")
        
        db.session.commit()
        
        return jsonify({
            'message': f'Cleaned up {cleaned_count} expired sessions',
            'cleaned_count': cleaned_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

