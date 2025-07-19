"""
Session Manager Service for Agent 1: Web Scraper & Data Collector
"""

import os
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import TimeoutException, WebDriverException

class SessionManager:
    """Manages persistent browser sessions"""
    
    def __init__(self):
        self.sessions = {}
        self.config = {
            'browser': 'chrome',
            'headless': True,
            'timeout': 30,
            'implicit_wait': 10,
            'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'window_size': '1920,1080',
            'session_timeout': 3600,  # 1 hour
            'screenshots_dir': '/home/ubuntu/multi_agent_mcp/shared/storage/screenshots'
        }
        
        # Ensure screenshots directory exists
        os.makedirs(self.config['screenshots_dir'], exist_ok=True)
    
    def create_session(self, session_id: str, browser_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new browser session"""
        try:
            config = self.config.copy()
            if browser_config:
                config.update(browser_config)
            
            # Create WebDriver
            if config['browser'].lower() == 'firefox':
                options = FirefoxOptions()
                if config['headless']:
                    options.add_argument('--headless')
                options.add_argument(f'--width={config["window_size"].split(",")[0]}')
                options.add_argument(f'--height={config["window_size"].split(",")[1]}')
                
                driver = webdriver.Firefox(options=options)
            else:
                options = ChromeOptions()
                if config['headless']:
                    options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument(f'--window-size={config["window_size"]}')
                options.add_argument(f'--user-agent={config["user_agent"]}')
                
                driver = webdriver.Chrome(options=options)
            
            # Set timeouts
            driver.set_page_load_timeout(config['timeout'])
            driver.implicitly_wait(config['implicit_wait'])
            
            # Store session
            self.sessions[session_id] = {
                'driver': driver,
                'config': config,
                'created_at': datetime.utcnow(),
                'last_used': datetime.utcnow(),
                'is_authenticated': False,
                'current_url': None
            }
            
            return {
                'success': True,
                'session_id': session_id,
                'message': 'Session created successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def close_session(self, session_id: str) -> Dict[str, Any]:
        """Close a browser session"""
        try:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session['driver'].quit()
                del self.sessions[session_id]
                
                return {
                    'success': True,
                    'message': 'Session closed successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Session not found'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get session status"""
        if session_id not in self.sessions:
            return {
                'exists': False,
                'error': 'Session not found'
            }
        
        session = self.sessions[session_id]
        
        try:
            # Check if driver is still alive
            current_url = session['driver'].current_url
            
            return {
                'exists': True,
                'is_alive': True,
                'current_url': current_url,
                'created_at': session['created_at'].isoformat(),
                'last_used': session['last_used'].isoformat(),
                'is_authenticated': session['is_authenticated']
            }
            
        except Exception:
            # Driver is dead, clean up
            try:
                session['driver'].quit()
            except:
                pass
            del self.sessions[session_id]
            
            return {
                'exists': False,
                'is_alive': False,
                'error': 'Session driver is no longer alive'
            }
    
    def navigate(self, session_id: str, url: str, wait_for: str = None, timeout: int = 30) -> Dict[str, Any]:
        """Navigate to a URL in a session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {'success': False, 'error': 'Session not found'}
            
            driver = session['driver']
            
            # Navigate to URL
            driver.get(url)
            
            # Wait for specific element if specified
            if wait_for:
                try:
                    WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
                    )
                except TimeoutException:
                    return {
                        'success': False,
                        'error': f'Timeout waiting for element: {wait_for}'
                    }
            
            # Update session info
            session['last_used'] = datetime.utcnow()
            session['current_url'] = driver.current_url
            
            return {
                'success': True,
                'url': driver.current_url,
                'title': driver.title
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def perform_login(self, session_id: str, login_url: str, credentials: Dict[str, str], 
                     login_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Perform login for a session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {'success': False, 'error': 'Session not found'}
            
            driver = session['driver']
            config = login_config or {}
            
            # Navigate to login page
            driver.get(login_url)
            
            # Wait for login form
            login_form_selector = config.get('login_form_selector', 'form')
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, login_form_selector))
                )
            except TimeoutException:
                return {
                    'success': False,
                    'error': 'Login form not found'
                }
            
            # Fill in credentials
            username_selector = config.get('username_selector', 'input[type="email"], input[name="username"], input[name="email"]')
            password_selector = config.get('password_selector', 'input[type="password"]')
            submit_selector = config.get('submit_selector', 'button[type="submit"], input[type="submit"]')
            
            # Enter username
            if 'username' in credentials or 'email' in credentials:
                username = credentials.get('username') or credentials.get('email')
                username_field = driver.find_element(By.CSS_SELECTOR, username_selector)
                username_field.clear()
                username_field.send_keys(username)
            
            # Enter password
            if 'password' in credentials:
                password_field = driver.find_element(By.CSS_SELECTOR, password_selector)
                password_field.clear()
                password_field.send_keys(credentials['password'])
            
            # Submit form
            submit_button = driver.find_element(By.CSS_SELECTOR, submit_selector)
            submit_button.click()
            
            # Wait for login to complete
            success_indicator = config.get('success_indicator')
            error_indicator = config.get('error_indicator')
            
            if success_indicator:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, success_indicator))
                    )
                    session['is_authenticated'] = True
                    session['last_used'] = datetime.utcnow()
                    
                    return {
                        'success': True,
                        'message': 'Login successful',
                        'current_url': driver.current_url
                    }
                except TimeoutException:
                    pass
            
            if error_indicator:
                try:
                    error_element = driver.find_element(By.CSS_SELECTOR, error_indicator)
                    if error_element.is_displayed():
                        return {
                            'success': False,
                            'error': f'Login failed: {error_element.text}'
                        }
                except:
                    pass
            
            # Generic success check - URL change or no error messages
            time.sleep(2)  # Wait a bit for page to load
            current_url = driver.current_url
            
            if current_url != login_url:
                session['is_authenticated'] = True
                session['last_used'] = datetime.utcnow()
                
                return {
                    'success': True,
                    'message': 'Login appears successful (URL changed)',
                    'current_url': current_url
                }
            else:
                return {
                    'success': False,
                    'error': 'Login may have failed (URL unchanged)'
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def take_screenshot(self, session_id: str, filename: str = None) -> Dict[str, Any]:
        """Take a screenshot of the current page"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {'success': False, 'error': 'Session not found'}
            
            driver = session['driver']
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'screenshot_{session_id}_{timestamp}.png'
            
            # Ensure .png extension
            if not filename.endswith('.png'):
                filename += '.png'
            
            screenshot_path = os.path.join(self.config['screenshots_dir'], filename)
            
            # Take screenshot
            driver.save_screenshot(screenshot_path)
            
            session['last_used'] = datetime.utcnow()
            
            return {
                'success': True,
                'screenshot_path': screenshot_path,
                'filename': filename
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_script(self, session_id: str, script: str) -> Dict[str, Any]:
        """Execute JavaScript in a session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {'success': False, 'error': 'Session not found'}
            
            driver = session['driver']
            
            # Execute script
            result = driver.execute_script(script)
            
            session['last_used'] = datetime.utcnow()
            
            return {
                'success': True,
                'result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_cookies(self, session_id: str) -> List[Dict[str, Any]]:
        """Get cookies from a session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return []
            
            driver = session['driver']
            cookies = driver.get_cookies()
            
            session['last_used'] = datetime.utcnow()
            
            return cookies
            
        except Exception as e:
            return []
    
    def set_cookies(self, session_id: str, cookies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Set cookies for a session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {'success': False, 'error': 'Session not found'}
            
            driver = session['driver']
            
            # Clear existing cookies
            driver.delete_all_cookies()
            
            # Add new cookies
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Failed to add cookie {cookie.get('name', 'unknown')}: {e}")
            
            session['last_used'] = datetime.utcnow()
            
            return {
                'success': True,
                'message': f'Set {len(cookies)} cookies'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_session_data(self, session_id: str) -> Dict[str, Any]:
        """Get session data (cookies, local storage, etc.)"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {}
            
            driver = session['driver']
            
            # Get cookies
            cookies = driver.get_cookies()
            
            # Get local storage
            local_storage = {}
            try:
                local_storage = driver.execute_script("return window.localStorage;")
            except:
                pass
            
            # Get session storage
            session_storage = {}
            try:
                session_storage = driver.execute_script("return window.sessionStorage;")
            except:
                pass
            
            session['last_used'] = datetime.utcnow()
            
            return {
                'cookies': cookies,
                'local_storage': local_storage,
                'session_storage': session_storage
            }
            
        except Exception as e:
            return {}
    
    def restore_session_data(self, session_id: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Restore session data"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {'success': False, 'error': 'Session not found'}
            
            driver = session['driver']
            
            # Restore cookies
            if 'cookies' in session_data and session_data['cookies']:
                self.set_cookies(session_id, session_data['cookies'])
            
            # Restore local storage
            if 'local_storage' in session_data and session_data['local_storage']:
                for key, value in session_data['local_storage'].items():
                    try:
                        driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")
                    except:
                        pass
            
            # Restore session storage
            if 'session_storage' in session_data and session_data['session_storage']:
                for key, value in session_data['session_storage'].items():
                    try:
                        driver.execute_script(f"window.sessionStorage.setItem('{key}', '{value}');")
                    except:
                        pass
            
            session['last_used'] = datetime.utcnow()
            
            return {
                'success': True,
                'message': 'Session data restored'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            time_diff = (current_time - session['last_used']).total_seconds()
            if time_diff > self.config['session_timeout']:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.close_session(session_id)
        
        return len(expired_sessions)

