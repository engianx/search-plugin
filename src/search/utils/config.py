"""Configuration utilities."""
import os
from pathlib import Path
import yaml

def load_config(domain: str = None) -> dict:
    """Load configuration from YAML files.

    Args:
        domain: Optional domain name for domain-specific config, if not provided, only project-wide default config will be used

    Returns:
        dict: Merged configuration
    """
    # Get config directory
    config_dir = Path(__file__).parent.parent.parent.parent / 'config'

    # Load default config
    default_config_path = config_dir / 'default.yaml'
    if not default_config_path.exists():
        raise FileNotFoundError(f"Default config not found: {default_config_path}")

    with open(default_config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Load domain config if specified
    if domain:
        domain_config_path = config_dir / domain / 'config.yaml'
        if domain_config_path.exists():
            with open(domain_config_path, 'r', encoding='utf-8') as f:
                domain_config = yaml.safe_load(f)
                # Merge domain config into default config
                config.update(domain_config)

    # Expand environment variables in data_dir
    if 'data_dir' in config:
        config['data_dir'] = os.path.expandvars(config['data_dir'])

    return config