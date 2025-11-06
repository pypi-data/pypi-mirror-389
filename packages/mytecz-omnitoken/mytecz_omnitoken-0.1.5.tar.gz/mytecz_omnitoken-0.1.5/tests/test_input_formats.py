"""
Input format handling tests for MyTecZ OmniToken.

This module tests different input formats including strings, lists,
files, JSON objects, and mixed content handling.
"""

import json
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any

import pytest

from omnitoken import OmniToken
from omnitoken.tokenizer_base import TokenizerConfig


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp(prefix="omnitoken_test_")
    yield temp_dir
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass


@pytest.fixture
def test_files(temp_dir: str):
    """Create test files for input format testing."""
    files = {}
    
    # Create text file
    text_file = os.path.join(temp_dir, "test.txt")
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write("This is test content from a file.")
    files['text'] = text_file
    
    # Create JSON file
    json_file = os.path.join(temp_dir, "test.json")
    test_json = {
        "text": "JSON content for testing",
        "data": ["item1", "item2", "item3"],
        "nested": {"key": "value"}
    }
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(test_json, f)
    files['json'] = json_file
    
    return files


class TestInputFormats:
    """Test different input format handling."""
    
    def test_string_input(self):
        """Test string input."""
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        tokenizer.fit("This is a simple string input.")
        
        result = tokenizer.encode("Test text")
        assert isinstance(result, list)
    
    def test_list_input(self):
        """Test list input."""
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        texts = ["First text", "Second text", "Third text"]
        tokenizer.fit(texts)
        
        result = tokenizer.encode("Test text")
        assert isinstance(result, list)
    
    def test_file_input(self, test_files: Dict[str, str]):
        """Test file input."""
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        tokenizer.fit(test_files['text'])
        
        result = tokenizer.encode("Test text")
        assert isinstance(result, list)
    
    def test_json_object_input(self):
        """Test JSON object input."""
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        json_data = {
            "content": "JSON test content",
            "items": ["item1", "item2"]
        }
        tokenizer.fit(json_data)
        
        result = tokenizer.encode("Test text")
        assert isinstance(result, list)
    
    def test_json_file_input(self, test_files: Dict[str, str]):
        """Test JSON file input."""
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        tokenizer.fit(test_files['json'])
        
        result = tokenizer.encode("Test text")
        assert isinstance(result, list)
    
    def test_mixed_input(self, test_files: Dict[str, str]):
        """Test mixed input formats."""
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        mixed_data = [
            "Direct string",
            test_files['text'],
            {"json": "object"},
            "Another string"
        ]
        tokenizer.fit(mixed_data)
        
        result = tokenizer.encode("Test text")
        assert isinstance(result, list)
    
    @pytest.mark.parametrize("input_type,test_data", [
        ("string", "Simple test string"),
        ("list", ["Text one", "Text two", "Text three"]),
        ("dict", {"content": "Dictionary content", "data": ["a", "b", "c"]}),
    ])
    def test_parametrized_inputs(self, input_type: str, test_data: Any):
        """Test various input types parametrically."""
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        tokenizer.fit(test_data)
        
        result = tokenizer.encode("Test encoding")
        assert isinstance(result, list)
        assert len(result) > 0


class TestFileHandling:
    """Test file handling functionality."""
    
    def test_large_file_handling(self, temp_dir: str):
        """Test handling of large files."""
        large_file = os.path.join(temp_dir, "large.txt")
        
        # Create a moderately large file
        with open(large_file, 'w', encoding='utf-8') as f:
            for i in range(1000):
                f.write(f"This is line {i} with some content to make it longer.\n")
        
        tokenizer = OmniToken(method="bpe", vocab_size=1000)
        tokenizer.fit(large_file)
        
        assert tokenizer._tokenizer.is_trained
        result = tokenizer.encode("Test text")
        assert isinstance(result, list)
    
    def test_empty_file_handling(self, temp_dir: str):
        """Test handling of empty files."""
        empty_file = os.path.join(temp_dir, "empty.txt")
        
        # Create empty file
        with open(empty_file, 'w', encoding='utf-8') as f:
            pass
        
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        
        # Should handle empty file gracefully
        try:
            tokenizer.fit(empty_file)
            # If it doesn't raise an exception, it should still work
            result = tokenizer.encode("Test text after empty file")
            assert isinstance(result, list)
        except ValueError:
            # It's acceptable to raise ValueError for empty training data
            pass
    
    def test_nonexistent_file_handling(self):
        """Test handling of non-existent files."""
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        
        with pytest.raises(FileNotFoundError):
            tokenizer.fit("/path/that/does/not/exist.txt")
    
    def test_binary_file_handling(self, temp_dir: str):
        """Test handling of binary files."""
        binary_file = os.path.join(temp_dir, "binary.bin")
        
        # Create binary file
        with open(binary_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\xff\xfe\xfd')
        
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        
        # Should handle binary files gracefully (might decode as best effort)
        try:
            tokenizer.fit(binary_file)
            result = tokenizer.encode("Test text")
            assert isinstance(result, list)
        except (UnicodeDecodeError, ValueError):
            # It's acceptable to fail on binary files
            pass


class TestJSONHandling:
    """Test JSON-specific handling functionality."""
    
    def test_nested_json_extraction(self):
        """Test extraction from deeply nested JSON."""
        nested_json = {
            "level1": {
                "level2": {
                    "level3": {
                        "text": "Deep nested text content",
                        "data": ["nested", "array", "content"]
                    },
                    "other": "Level 2 content"
                },
                "text": "Level 1 content"
            },
            "top_level": "Top level text"
        }
        
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        tokenizer.fit(nested_json)
        
        result = tokenizer.encode("Test text")
        assert isinstance(result, list)
    
    def test_json_array_handling(self):
        """Test handling of JSON arrays."""
        json_array = [
            {"text": "First item"},
            {"text": "Second item"},
            {"text": "Third item"},
            "Direct string in array",
            123,  # Non-string item
            ["nested", "array"]
        ]
        
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        tokenizer.fit(json_array)
        
        result = tokenizer.encode("Test text")
        assert isinstance(result, list)
    
    def test_invalid_json_file(self, temp_dir: str):
        """Test handling of invalid JSON files."""
        invalid_json_file = os.path.join(temp_dir, "invalid.json")
        
        # Create invalid JSON file
        with open(invalid_json_file, 'w', encoding='utf-8') as f:
            f.write('{"incomplete": "json",}')  # Trailing comma makes it invalid
        
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        
        # Should handle invalid JSON gracefully (treat as text)
        try:
            tokenizer.fit(invalid_json_file)
            result = tokenizer.encode("Test text")
            assert isinstance(result, list)
        except (json.JSONDecodeError, ValueError):
            # It's acceptable to fail on invalid JSON
            pass


class TestInputValidation:
    """Test input validation and edge cases."""
    
    def test_none_input(self):
        """Test handling of None input."""
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        
        with pytest.raises((ValueError, TypeError)):
            tokenizer.fit(None)
    
    def test_empty_list_input(self):
        """Test handling of empty list input."""
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        
        with pytest.raises(ValueError):
            tokenizer.fit([])
    
    def test_list_with_none_items(self):
        """Test handling of list with None items."""
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        
        # Should filter out None items
        mixed_list = ["Valid text", None, "Another valid text", None]
        tokenizer.fit(mixed_list)
        
        result = tokenizer.encode("Test text")
        assert isinstance(result, list)
    
    def test_numeric_input_handling(self):
        """Test handling of numeric inputs."""
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        
        # Numeric data should be converted to strings
        numeric_data = [123, 456.789, "text", 999]
        tokenizer.fit(numeric_data)
        
        result = tokenizer.encode("Test text")
        assert isinstance(result, list)
    
    @pytest.mark.parametrize("invalid_input", [
        123,  # Plain number
        45.67,  # Float
        True,  # Boolean
        object(),  # Random object
    ])
    def test_invalid_input_types(self, invalid_input: Any):
        """Test handling of invalid input types."""
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        
        # Should either convert to string or raise appropriate error
        try:
            tokenizer.fit(invalid_input)
            result = tokenizer.encode("Test text")
            assert isinstance(result, list)
        except (ValueError, TypeError):
            # It's acceptable to reject invalid input types
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])