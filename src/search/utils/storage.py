"""Storage utilities."""
import json
import os

def save_metadata(data, filepath):
    """Save metadata to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def load_metadata(filepath):
    """Load metadata from JSON file.

    Args:
        filepath: Path to the JSON metadata file

    Returns:
        dict: Loaded metadata

    Raises:
        FileNotFoundError: If the metadata file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    with open(filepath, 'r') as f:
        return json.load(f)

def save_stats(stats, filepath):
    """Save stats to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(stats, f, indent=2)