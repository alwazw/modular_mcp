"""
Web Scraper Service for Agent 1: Web Scraper & Data Collector
"""

import os
import json
import time
import threading
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import hashlib
import uuid

class WebScraperService:
    """Service for web scraping operations"""
    
    def __init__(self):
        self.config = {
            'browser': 'chrome',  # chrome, firefox
            'headless': True,
            'timeout': 30,
            'page_load_timeout': 60,
            'implicit_wait': 10,
            'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'window_size': '1920,1080',
            'download_dir': '/home/ubuntu/multi_agent_mcp/shared/storage/raw',
            'max_retries': 3,
            'retry_delay': 2,
            'respect_robots_txt': True,
            'rate_limit_delay': 1.0
        }
        self.active_drivers = {}
        self.job_threads = {}
        
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration"""
        self.config.update(new_config)
        return self.config.copy()
    
    def create_driver(self, session_id: str = None, custom_config: Dict[str, Any] = None) -> webdriver:
        """Create a new WebDriver instance"""
        config = self.config.copy()
        if custom_config:
            config.update(custom_config)
        
        if config['browser'].lower() == 'firefox':
            options = FirefoxOptions()
            if config['headless']:
                options.add_argument('--headless')
            options.add_argument(f'--width={config["window_size"].split(",")[0]}')
            options.add_argument(f'--height={config["window_size"].split(",")[1]}')
            
            # Set download directory
            options.set_preference('browser.download.folderList', 2)
            options.set_preference('browser.download.dir', config['download_dir'])
            options.set_preference('browser.helperApps.neverAsk.saveToDisk', 
                                 'application/pdf,application/octet-stream,text/csv,application/vnd.ms-excel')
            
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
            
            # Set download directory
            prefs = {
                'download.default_directory': config['download_dir'],
                'download.prompt_for_download': False,
                'download.directory_upgrade': True,
                'safebrowsing.enabled': True
            }
            options.add_experimental_option('prefs', prefs)
            
            driver = webdriver.Chrome(options=options)
        
        # Set timeouts
        driver.set_page_load_timeout(config['page_load_timeout'])
        driver.implicitly_wait(config['implicit_wait'])
        
        if session_id:
            self.active_drivers[session_id] = driver
        
        return driver
    
    def get_driver(self, session_id: str) -> Optional[webdriver]:
        """Get existing driver for session"""
        return self.active_drivers.get(session_id)
    
    def close_driver(self, session_id: str):
        """Close driver for session"""
        if session_id in self.active_drivers:
            try:
                self.active_drivers[session_id].quit()
            except Exception:
                pass
            del self.active_drivers[session_id]
    
    def scrape_url(self, url: str, config: Dict[str, Any] = None, 
                   browser_session = None) -> Dict[str, Any]:
        """Scrape a single URL"""
        try:
            session_id = browser_session.session_id if browser_session else str(uuid.uuid4())
            
            # Get or create driver
            driver = self.get_driver(session_id)
            if not driver:
                driver = self.create_driver(session_id, config)
            
            # Restore session if available
            if browser_session and browser_session.cookies:
                driver.get(url)
                for cookie in browser_session.cookies:
                    try:
                        driver.add_cookie(cookie)
                    except Exception:
                        pass
                driver.refresh()
            else:
                driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, self.config['timeout']).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            
            # Get page source and metadata
            page_source = driver.page_source
            title = driver.title
            current_url = driver.current_url
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                absolute_url = urljoin(current_url, link['href'])
                links.append({
                    'text': link.get_text(strip=True),
                    'url': absolute_url
                })
            
            # Extract images
            images = []
            for img in soup.find_all('img', src=True):
                absolute_url = urljoin(current_url, img['src'])
                images.append({
                    'alt': img.get('alt', ''),
                    'url': absolute_url
                })
            
            # Extract metadata
            metadata = {
                'title': title,
                'url': current_url,
                'scraped_at': datetime.utcnow().isoformat(),
                'page_size': len(page_source),
                'text_length': len(text_content),
                'links_count': len(links),
                'images_count': len(images)
            }
            
            # Extract meta tags
            meta_tags = {}
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property')
                content = meta.get('content')
                if name and content:
                    meta_tags[name] = content
            
            metadata['meta_tags'] = meta_tags
            
            # Calculate content hash
            content_hash = hashlib.sha256(text_content.encode()).hexdigest()
            
            result = {
                'success': True,
                'url': current_url,
                'title': title,
                'content': {
                    'raw_html': page_source,
                    'text': text_content,
                    'links': links,
                    'images': images
                },
                'metadata': metadata,
                'content_hash': content_hash
            }
            
            # Don't close driver if it's a session
            if not browser_session:
                self.close_driver(session_id)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def extract_data(self, url: str, selectors: Dict[str, str], 
                    browser_session = None) -> Dict[str, Any]:
        """Extract specific data using CSS selectors"""
        try:
            session_id = browser_session.session_id if browser_session else str(uuid.uuid4())
            
            # Get or create driver
            driver = self.get_driver(session_id)
            if not driver:
                driver = self.create_driver(session_id)
            
            # Navigate to URL
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, self.config['timeout']).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            
            # Extract data using selectors
            extracted_data = {}
            
            for field_name, selector in selectors.items():
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if len(elements) == 1:
                        # Single element
                        element = elements[0]
                        extracted_data[field_name] = {
                            'text': element.text.strip(),
                            'html': element.get_attribute('outerHTML'),
                            'attributes': {
                                attr: element.get_attribute(attr)
                                for attr in ['href', 'src', 'alt', 'title', 'class', 'id']
                                if element.get_attribute(attr)
                            }
                        }
                    elif len(elements) > 1:
                        # Multiple elements
                        extracted_data[field_name] = []
                        for element in elements:
                            extracted_data[field_name].append({
                                'text': element.text.strip(),
                                'html': element.get_attribute('outerHTML'),
                                'attributes': {
                                    attr: element.get_attribute(attr)
                                    for attr in ['href', 'src', 'alt', 'title', 'class', 'id']
                                    if element.get_attribute(attr)
                                }
                            })
                    else:
                        # No elements found
                        extracted_data[field_name] = None
                        
                except Exception as e:
                    extracted_data[field_name] = {'error': str(e)}
            
            result = {
                'success': True,
                'url': url,
                'extracted_data': extracted_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Don't close driver if it's a session
            if not browser_session:
                self.close_driver(session_id)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def download_file(self, url: str, filename: str = None, 
                     browser_session = None) -> Dict[str, Any]:
        """Download a file from URL"""
        try:
            # Ensure download directory exists
            os.makedirs(self.config['download_dir'], exist_ok=True)
            
            # Use requests for file download (more reliable than browser)
            headers = {
                'User-Agent': self.config['user_agent']
            }
            
            # Add session cookies if available
            cookies = None
            if browser_session and browser_session.cookies:
                cookies = {cookie['name']: cookie['value'] for cookie in browser_session.cookies}
            
            response = requests.get(url, headers=headers, cookies=cookies, stream=True, timeout=self.config['timeout'])
            response.raise_for_status()
            
            # Determine filename
            if not filename:
                # Try to get filename from Content-Disposition header
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"')
                else:
                    # Extract from URL
                    parsed_url = urlparse(url)
                    filename = os.path.basename(parsed_url.path) or 'downloaded_file'
            
            # Ensure safe filename
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            if not filename:
                filename = f"download_{int(time.time())}"
            
            # Handle filename conflicts
            file_path = os.path.join(self.config['download_dir'], filename)
            counter = 1
            while os.path.exists(file_path):
                name, ext = os.path.splitext(filename)
                file_path = os.path.join(self.config['download_dir'], f"{name}_{counter}{ext}")
                counter += 1
            
            # Download file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
            
            return {
                'success': True,
                'url': url,
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'file_size': file_size,
                'file_hash': file_hash.hexdigest(),
                'content_type': response.headers.get('Content-Type'),
                'downloaded_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def start_scraping_job(self, job_id: str):
        """Start a scraping job asynchronously"""
        def run_job():
            from src.models.scraper import db, ScrapingJob, ScrapedContent
            
            try:
                # Get job from database
                job = ScrapingJob.query.filter_by(job_id=job_id).first()
                if not job:
                    return
                
                # Update job status
                job.status = 'running'
                job.started_at = datetime.utcnow()
                db.session.commit()
                
                # Perform scraping based on job type
                if job.job_type == 'single_page':
                    result = self.scrape_url(job.url, job.scraping_config)
                elif job.job_type == 'file_download':
                    result = self.download_file(job.url)
                else:
                    result = {'success': False, 'error': f'Unknown job type: {job.job_type}'}
                
                if result['success']:
                    # Save scraped content
                    content = ScrapedContent(
                        content_id=str(uuid.uuid4()),
                        job_id=job_id,
                        url=result['url'],
                        title=result.get('title'),
                        content_type='text' if 'content' in result else 'file',
                        raw_content=result.get('content', {}).get('raw_html'),
                        cleaned_content=result.get('content', {}).get('text'),
                        structured_data=result.get('content'),
                        meta_data=result.get('metadata'),
                        content_hash=result.get('content_hash')
                    )
                    
                    db.session.add(content)
                    
                    # Update job
                    job.status = 'completed'
                    job.extracted_data = result
                    job.output_path = result.get('file_path')
                else:
                    job.status = 'failed'
                    job.error_message = result.get('error')
                
                job.completed_at = datetime.utcnow()
                db.session.commit()
                
            except Exception as e:
                # Update job with error
                job = ScrapingJob.query.filter_by(job_id=job_id).first()
                if job:
                    job.status = 'failed'
                    job.error_message = str(e)
                    job.completed_at = datetime.utcnow()
                    db.session.commit()
            
            finally:
                # Clean up thread reference
                if job_id in self.job_threads:
                    del self.job_threads[job_id]
        
        # Start job in separate thread
        thread = threading.Thread(target=run_job, daemon=True)
        thread.start()
        self.job_threads[job_id] = thread
    
    def start_batch_scraping(self, job_ids: List[str], session_id: str = None):
        """Start batch scraping for multiple jobs"""
        def run_batch():
            for job_id in job_ids:
                self.start_scraping_job(job_id)
                # Add delay between jobs to be respectful
                time.sleep(self.config['rate_limit_delay'])
        
        thread = threading.Thread(target=run_batch, daemon=True)
        thread.start()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status information"""
        return {
            'active_drivers': len(self.active_drivers),
            'running_jobs': len(self.job_threads),
            'config': self.config,
            'timestamp': datetime.utcnow().isoformat()
        }

