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
    
    Args:
        config_path (str): Path to the configuration file (fallback)
        
    Returns:
        dict: Configuration dictionary
    """
    # Try multiple locations for config file
    config_file = None
    
    # 1. First try: same directory as this file (development)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    dev_config = os.path.join(project_root, config_path)
    
    # 2. Second try: installed package location (site-packages)
    # Find the actual package installation directory
    try:
        # Get the directory where this module is installed
        module_dir = Path(__file__).resolve().parent  # src/utils/
        # Go up to find site-packages or the package root
        search_paths = [
            module_dir.parent.parent,  # Go up from src/utils to package root
            Path(sys.prefix) / 'Lib' / 'site-packages',  # Standard site-packages
            Path(sys.prefix) / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages',  # Unix-like
        ]
        
        for search_path in search_paths:
            candidate = search_path / config_path
            if candidate.exists():
                config_file = str(candidate)
                break
    except Exception:
        pass
    
    # 3. Third try: development location
    if config_file is None and os.path.exists(dev_config):
        config_file = dev_config
    
    # 4. Fourth try: current working directory
    if config_file is None:
        cwd_config = os.path.join(os.getcwd(), config_path)
        if os.path.exists(cwd_config):
            config_file = cwd_config
    
    # If still not found, raise a helpful error
    if config_file is None:
        raise FileNotFoundError(
            f"Configuration file '{config_path}' not found. Searched in:\n"
            f"  1. Development: {dev_config}\n"
            f"  2. Site-packages locations\n"
            f"  3. Current directory: {os.path.join(os.getcwd(), config_path)}\n"
            f"Please ensure the config file exists in one of these locations."
        )
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


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
