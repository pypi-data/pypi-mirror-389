"""
Configuration loading utilities.
"""
import os
import json
import sys
from argparse import Namespace
from typing import Dict
from pathlib import Path


def load_config(config_path: str = 'config.json') -> Dict:
    """
    Load configuration from environment variables or JSON file.
    Priority: Environment variables > JSON file
    
    Args:
        config_path (str): Path to the configuration file (fallback)
        
    Returns:
        dict: Configuration dictionary
    """
    # Priority 1: Try to load from environment variables
    env_config = {
        'orthanc_base_url': os.getenv('ORTHANC_BASE_URL'),
        'cookie': os.getenv('ORTHANC_COOKIE'),
        'max_workers': os.getenv('MAX_WORKERS', '4'),
        'max_retries': os.getenv('MAX_RETRIES', '3'),
        'DEFAULT_CONNECT_TIMEOUT': os.getenv('DEFAULT_CONNECT_TIMEOUT', '10'),
        'DEFAULT_READ_TIMEOUT': os.getenv('DEFAULT_READ_TIMEOUT', '300'),
        'DEFAULT_RETRY_DELAY': os.getenv('DEFAULT_RETRY_DELAY', '2'),
        'DEFAULT_BATCH_SIZE': os.getenv('DEFAULT_BATCH_SIZE', '10')
    }
    
    # If required environment variables are set, use env config
    if env_config['orthanc_base_url'] and env_config['cookie']:
        # Convert string numbers to integers
        for key in ['max_workers', 'max_retries', 'DEFAULT_CONNECT_TIMEOUT', 
                    'DEFAULT_READ_TIMEOUT', 'DEFAULT_RETRY_DELAY', 'DEFAULT_BATCH_SIZE']:
            env_config[key] = int(env_config[key])
        return env_config
    
    # Priority 2: Try to load from config file
    config_file = None
    
    # Search locations in order:
    # 1. Current working directory (most common for MCP usage)
    cwd_config = os.path.join(os.getcwd(), config_path)
    if os.path.exists(cwd_config):
        config_file = cwd_config
    
    # 2. Development location (project root)
    if config_file is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        dev_config = os.path.join(project_root, config_path)
        if os.path.exists(dev_config):
            config_file = dev_config
    
    # 3. Installed package location (site-packages)
    if config_file is None:
        try:
            module_dir = Path(__file__).resolve().parent  # src/utils/
            search_paths = [
                module_dir.parent.parent / config_path,  # Go up from src/utils to package root
                Path(sys.prefix) / config_path,  # Python prefix directory
                Path(sys.prefix) / 'Lib' / 'site-packages' / config_path,
            ]
            
            for candidate in search_paths:
                if candidate.exists():
                    config_file = str(candidate)
                    break
        except Exception:
            pass
    
    # If config file found, load it
    if config_file is not None:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # If neither environment variables nor config file found, raise error
    raise FileNotFoundError(
        f"Configuration not found. Please either:\n"
        f"  1. Set environment variables: ORTHANC_BASE_URL and ORTHANC_COOKIE\n"
        f"  2. Create {config_path} file in:\n"
        f"     - Current directory: {os.getcwd()}\n"
        f"     - Or set environment variables instead\n\n"
        f"Example environment variables:\n"
        f"  ORTHANC_BASE_URL=http://your-server:8042\n"
        f"  ORTHANC_COOKIE=your-cookie-value"
    )


def create_upload_config(config: Dict) -> Namespace:
    """
    Create upload configuration namespace from config dictionary.
    
    Args:
        config (dict): Configuration dictionary
        
    Returns:
        Namespace: Upload configuration namespace
    """
    return Namespace(
        orthanc_base_url=config['orthanc_base_url'],
        cookie=config['cookie'],
        max_workers=config['max_workers'],
        max_retries=config['max_retries'],
        DEFAULT_CONNECT_TIMEOUT=config['DEFAULT_CONNECT_TIMEOUT'],
        DEFAULT_READ_TIMEOUT=config['DEFAULT_READ_TIMEOUT'],
        DEFAULT_RETRY_DELAY=config['DEFAULT_RETRY_DELAY'],
        DEFAULT_BATCH_SIZE=config['DEFAULT_BATCH_SIZE']
    )
