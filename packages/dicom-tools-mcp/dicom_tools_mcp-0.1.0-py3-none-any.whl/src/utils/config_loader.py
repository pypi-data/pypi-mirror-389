"""
Configuration loading utilities.
"""
import os
import json
from argparse import Namespace
from typing import Dict


def load_config(config_path: str = 'config.json') -> Dict:
    """
    Load configuration from JSON file.
    
    Args:
        config_path (str): Path to the configuration file
        
    Returns:
        dict: Configuration dictionary
    """
    # Get the project root directory (two levels up from this file)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    config_file = os.path.join(project_root, config_path)
    
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
