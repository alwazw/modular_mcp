"""
Common utility functions for the Multi-Agent MCP System
"""

import os
import hashlib
import json
import logging
import mimetypes
import shutil
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from urllib.parse import urlparse, urljoin
import requests
from PIL import Image
import magic

# Logging setup
def setup_logging(agent_id: str, log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Set up logging for an agent"""
    logger = logging.getLogger(agent_id)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# File utilities
def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """Calculate hash of a file"""
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get comprehensive file information"""
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    stat = path.stat()
    
    # Get MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        # Fallback to python-magic for better detection
        try:
            mime_type = magic.from_file(file_path, mime=True)
        except:
            mime_type = "application/octet-stream"
    
    info = {
        'path': str(path.absolute()),
        'name': path.name,
        'stem': path.stem,
        'suffix': path.suffix,
        'size': stat.st_size,
        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'mime_type': mime_type,
        'hash': calculate_file_hash(file_path)
    }
    
    # Additional info for images
    if mime_type.startswith('image/'):
        try:
            with Image.open(file_path) as img:
                info['image_info'] = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode
                }
        except Exception:
            pass
    
    return info

def ensure_directory(directory: str) -> str:
    """Ensure directory exists, create if it doesn't"""
    Path(directory).mkdir(parents=True, exist_ok=True)
    return directory

def safe_filename(filename: str) -> str:
    """Create a safe filename by removing/replacing problematic characters"""
    # Remove or replace problematic characters
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    safe_name = ''.join(c if c in safe_chars else '_' for c in filename)
    
    # Ensure it doesn't start with a dot
    if safe_name.startswith('.'):
        safe_name = 'file_' + safe_name
    
    # Limit length
    if len(safe_name) > 255:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:255-len(ext)] + ext
    
    return safe_name

def copy_file_to_storage(source_path: str, storage_dir: str, 
                        preserve_name: bool = True) -> Tuple[str, Dict[str, Any]]:
    """Copy file to storage directory and return new path and metadata"""
    ensure_directory(storage_dir)
    
    source_info = get_file_info(source_path)
    
    if preserve_name:
        filename = safe_filename(source_info['name'])
    else:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        extension = source_info['suffix']
        filename = f"{file_id}{extension}"
    
    # Handle filename conflicts
    dest_path = os.path.join(storage_dir, filename)
    counter = 1
    while os.path.exists(dest_path):
        name, ext = os.path.splitext(filename)
        dest_path = os.path.join(storage_dir, f"{name}_{counter}{ext}")
        counter += 1
    
    # Copy file
    shutil.copy2(source_path, dest_path)
    
    # Update metadata with new path
    dest_info = get_file_info(dest_path)
    dest_info['original_path'] = source_path
    dest_info['copied_at'] = datetime.utcnow().isoformat()
    
    return dest_path, dest_info

# URL utilities
def is_valid_url(url: str) -> bool:
    """Check if a URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def normalize_url(url: str, base_url: str = None) -> str:
    """Normalize a URL, handling relative URLs"""
    if base_url and not is_valid_url(url):
        url = urljoin(base_url, url)
    
    # Remove fragment
    parsed = urlparse(url)
    return parsed._replace(fragment='').geturl()

def download_file(url: str, dest_dir: str, filename: str = None, 
                 timeout: int = 30, headers: Dict[str, str] = None) -> Tuple[str, Dict[str, Any]]:
    """Download file from URL and save to destination directory"""
    ensure_directory(dest_dir)
    
    if headers is None:
        headers = {
            'User-Agent': 'Multi-Agent-MCP-Bot/1.0'
        }
    
    response = requests.get(url, headers=headers, timeout=timeout, stream=True)
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
    
    filename = safe_filename(filename)
    
    # Handle filename conflicts
    dest_path = os.path.join(dest_dir, filename)
    counter = 1
    while os.path.exists(dest_path):
        name, ext = os.path.splitext(filename)
        dest_path = os.path.join(dest_dir, f"{name}_{counter}{ext}")
        counter += 1
    
    # Download file
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    # Get file info
    file_info = get_file_info(dest_path)
    file_info['source_url'] = url
    file_info['downloaded_at'] = datetime.utcnow().isoformat()
    file_info['content_type'] = response.headers.get('Content-Type')
    file_info['content_length'] = response.headers.get('Content-Length')
    
    return dest_path, file_info

# Data utilities
def serialize_data(data: Any) -> str:
    """Serialize data to JSON string with datetime handling"""
    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    return json.dumps(data, default=json_serializer, indent=2)

def deserialize_data(json_str: str) -> Any:
    """Deserialize JSON string to Python object"""
    return json.loads(json_str)

def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Recursively merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """Flatten a nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

# Text processing utilities
def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    return text.strip()

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text (simple implementation)"""
    # This is a basic implementation - in production, you might want to use
    # more sophisticated NLP libraries like spaCy or NLTK
    
    # Common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
        'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
    }
    
    # Simple keyword extraction
    words = text.lower().split()
    words = [word.strip('.,!?;:"()[]{}') for word in words]
    words = [word for word in words if len(word) > 2 and word not in stop_words]
    
    # Count frequency
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:max_keywords]]

# Validation utilities
def validate_email(email: str) -> bool:
    """Validate email address format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    import re
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    # Check if it's a valid length (7-15 digits)
    return 7 <= len(digits) <= 15

def validate_json(json_str: str) -> Tuple[bool, Optional[str]]:
    """Validate JSON string"""
    try:
        json.loads(json_str)
        return True, None
    except json.JSONDecodeError as e:
        return False, str(e)

# Performance utilities
def measure_time(func):
    """Decorator to measure function execution time"""
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Log execution time
        logger = logging.getLogger(func.__module__)
        logger.debug(f"{func.__name__} executed in {execution_time:.4f} seconds")
        
        return result
    
    return wrapper

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator to retry function on failure"""
    import time
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        raise e
                    
                    logger = logging.getLogger(func.__module__)
                    logger.warning(f"{func.__name__} failed (attempt {retries}/{max_retries}): {e}")
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        
        return wrapper
    
    return decorator

# System utilities
def get_system_info() -> Dict[str, Any]:
    """Get system information"""
    import platform
    import psutil
    
    return {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_total': psutil.virtual_memory().total,
        'memory_available': psutil.virtual_memory().available,
        'disk_usage': {
            'total': psutil.disk_usage('/').total,
            'used': psutil.disk_usage('/').used,
            'free': psutil.disk_usage('/').free
        },
        'timestamp': datetime.utcnow().isoformat()
    }

def create_temp_file(suffix: str = '', prefix: str = 'mcp_', content: str = None) -> str:
    """Create a temporary file and return its path"""
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    
    if content:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
    else:
        os.close(fd)
    
    return path

def cleanup_temp_files(file_paths: List[str]):
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to cleanup temp file {file_path}: {e}")

# Error handling utilities
class MCPError(Exception):
    """Base exception for MCP system errors"""
    pass

class ConfigurationError(MCPError):
    """Configuration-related errors"""
    pass

class AgentError(MCPError):
    """Agent-related errors"""
    pass

class DataProcessingError(MCPError):
    """Data processing errors"""
    pass

class NetworkError(MCPError):
    """Network-related errors"""
    pass

def handle_error(error: Exception, context: str = "", logger: logging.Logger = None) -> Dict[str, Any]:
    """Handle and format error information"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    error_info = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.error(f"Error in {context}: {error_info}")
    
    return error_info

