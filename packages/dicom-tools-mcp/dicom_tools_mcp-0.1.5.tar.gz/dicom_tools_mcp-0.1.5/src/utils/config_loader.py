"""
Configuration loading utilities.
"""
import os
import json
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
    # When installed via pip, config.json should be in the package root
    package_root = Path(__file__).parent.parent.parent  # Go up to package root
    installed_config = package_root / config_path
    
    # 3. Third try: current working directory
    cwd_config = os.path.join(os.getcwd(), config_path)
    
    # Check which config file exists
    if os.path.exists(dev_config):
        config_file = dev_config
    elif os.path.exists(installed_config):
        config_file = str(installed_config)
    elif os.path.exists(cwd_config):
        config_file = cwd_config
    else:
        # If no config file found, raise a helpful error
        raise FileNotFoundError(
            f"Configuration file '{config_path}' not found in any of these locations:\n"
            f"  1. Development: {dev_config}\n"
            f"  2. Installed: {installed_config}\n"
            f"  3. Current directory: {cwd_config}\n"
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
