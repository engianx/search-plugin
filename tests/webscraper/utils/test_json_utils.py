"""Unit tests for json_utils module."""
import pytest
import json
from search.utils.json_utils import load_json

def test_load_json_plain():
    """Test loading plain JSON string."""
    json_str = '{"name": "test", "value": 123}'
    result = load_json(json_str)
    assert result == {"name": "test", "value": 123}

def test_load_json_with_markdown():
    """Test loading JSON string with markdown backticks."""
    json_str = """```json
    {
        "name": "test",
        "value": 123
    }
    ```"""
    result = load_json(json_str)
    assert result == {"name": "test", "value": 123}

def test_load_json_with_backticks_no_lang():
    """Test loading JSON string with backticks but no language specifier."""
    json_str = """```
    {
        "name": "test",
        "value": 123
    }
    ```"""
    result = load_json(json_str)
    assert result == {"name": "test", "value": 123}

def test_load_json_with_whitespace():
    """Test loading JSON string with extra whitespace."""
    json_str = """
    {
        "name": "test",
        "value": 123
    }
    """
    result = load_json(json_str)
    assert result == {"name": "test", "value": 123}

def test_load_json_invalid():
    """Test loading invalid JSON string raises error."""
    json_str = '{"name": "test", invalid}'
    with pytest.raises(json.JSONDecodeError):
        load_json(json_str)

def test_load_json_invalid_in_markdown():
    """Test loading invalid JSON string in markdown raises error."""
    json_str = """```json
    {"name": "test", invalid}
    ```"""
    with pytest.raises(json.JSONDecodeError):
        load_json(json_str)

def test_load_json_complex():
    """Test loading complex JSON structure."""
    json_str = """```json
    {
        "name": "test",
        "values": [1, 2, 3],
        "nested": {
            "key": "value",
            "list": ["a", "b", "c"]
        },
        "null": null,
        "bool": true
    }
    ```"""
    result = load_json(json_str)
    assert result == {
        "name": "test",
        "values": [1, 2, 3],
        "nested": {
            "key": "value",
            "list": ["a", "b", "c"]
        },
        "null": None,
        "bool": True
    }