"""
Utilities for MyTecZ OmniToken.

This module provides helper functions for input detection, preprocessing,
text processing, and token visualization.
"""

import re
import unicodedata
from typing import List, Dict, Any, Tuple, Optional
import json
import os
from pathlib import Path
from collections import Counter


class InputDetector:
    """Utility class for detecting and processing various input formats."""
    
    @staticmethod
    def detect_input_type(data: Any) -> str:
        """
        Detect the type of input data.
        
        Args:
            data: Input data to analyze
        
        Returns:
            Type string: "file", "files", "json", "string", "list"
        """
        if isinstance(data, str):
            # Check if it's a file path
            if os.path.exists(data) and os.path.isfile(data):
                return "file"
            else:
                return "string"
        elif isinstance(data, list):
            if all(isinstance(item, str) for item in data):
                # Check if all items are file paths
                if all(os.path.exists(item) and os.path.isfile(item) for item in data):
                    return "files"
                else:
                    return "list"
            else:
                return "list"
        elif isinstance(data, dict):
            return "json"
        else:
            return "unknown"
    
    @staticmethod
    def extract_text_from_file(filepath: str) -> List[str]:
        """
        Extract text content from a file based on its extension.
        
        Args:
            filepath: Path to the file
        
        Returns:
            List of text strings
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_ext = Path(filepath).suffix.lower()
            
            if file_ext == '.json':
                try:
                    json_data = json.loads(content)
                    return InputDetector.extract_text_from_json(json_data)
                except json.JSONDecodeError:
                    return [content]
            elif file_ext in ['.txt', '.md', '.py', '.js', '.java', '.cpp', '.c', '.h']:
                # Text-based files
                return [content]
            else:
                # Default: treat as text
                return [content]
        
        except Exception as e:
            print(f"Warning: Could not read file {filepath}: {e}")
            return []
    
    @staticmethod
    def extract_text_from_json(json_data: Any) -> List[str]:
        """
        Recursively extract all string values from JSON data.
        
        Args:
            json_data: JSON data structure
        
        Returns:
            List of text strings found in the JSON
        """
        texts = []
        
        def extract_strings(obj):
            if isinstance(obj, str):
                texts.append(obj)
            elif isinstance(obj, dict):
                for value in obj.values():
                    extract_strings(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_strings(item)
        
        extract_strings(json_data)
        return texts


class TextProcessor:
    """Utility class for text preprocessing and normalization."""
    
    @staticmethod
    def normalize_unicode(text: str) -> str:
        """
        Normalize Unicode text using NFC normalization.
        
        Args:
            text: Input text to normalize
        
        Returns:
            Normalized text
        """
        return unicodedata.normalize('NFC', text)
    
    @staticmethod
    def clean_text(text: str, preserve_case: bool = True) -> str:
        """
        Clean and preprocess text.
        
        Args:
            text: Input text to clean
            preserve_case: Whether to preserve original case
        
        Returns:
            Cleaned text
        """
        # Normalize Unicode
        text = TextProcessor.normalize_unicode(text)
        
        # Normalize whitespace (but preserve structure)
        text = re.sub(r'\s+', ' ', text.strip())
        
        if not preserve_case:
            text = text.lower()
        
        return text
    
    @staticmethod
    def extract_words(text: str) -> List[str]:
        """
        Extract words from text using basic tokenization.
        
        Args:
            text: Input text
        
        Returns:
            List of words
        """
        # Simple word extraction - can be enhanced
        words = re.findall(r'\b\w+\b|[^\w\s]', text)
        return [word for word in words if word.strip()]
    
    @staticmethod
    def extract_characters(text: str) -> List[str]:
        """
        Extract user-perceived characters (grapheme clusters) from text.
        
        Args:
            text: Input text
        
        Returns:
            List of grapheme clusters (attempted without external deps).
        """
        clusters: List[str] = []
        i = 0
        while i < len(text):
            ch = text[i]
            # Regional indicator (flags come in pairs)
            code = ord(ch)
            if 0x1F1E6 <= code <= 0x1F1FF:
                # Try to pair with next regional indicator
                if (i + 1 < len(text) and 0x1F1E6 <= ord(text[i+1]) <= 0x1F1FF):
                    clusters.append(ch + text[i+1])
                    i += 2
                    continue
            # Zero-width joiner sequence (e.g., family / profession emojis)
            j = i + 1
            seq = ch
            while j + 1 <= len(text) and j < len(text) and ord(text[j]) == 0x200D:
                # Append ZWJ + next char
                if j + 1 < len(text):
                    seq += text[j] + text[j+1]
                    j += 2
                else:
                    break
            if len(seq) > 1:
                clusters.append(seq)
                i = j
                continue
            clusters.append(ch)
            i += 1
        return clusters
    
    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """
        Split text into sentences using basic rules.
        
        Args:
            text: Input text
        
        Returns:
            List of sentences
        """
        # Simple sentence splitting - can be enhanced
        sentences = re.split(r'[.!?]+\s+', text)
        return [sent.strip() for sent in sentences if sent.strip()]
    
    @staticmethod
    def contains_emoji(text: str) -> bool:
        """
        Check if text contains emoji characters.
        
        Args:
            text: Input text to check
        
        Returns:
            True if text contains emojis, False otherwise
        """
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return bool(emoji_pattern.search(text))
    
    @staticmethod
    def extract_emojis(text: str) -> List[str]:
        """
        Extract emoji characters from text.
        
        Args:
            text: Input text
        
        Returns:
            List of emoji characters found
        """
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.findall(text)


class TokenVisualizer:
    """Utility class for visualizing tokens and tokenization results."""
    
    @staticmethod
    def visualize_tokens(
        text: str, 
        tokens: List[str], 
        token_ids: Optional[List[int]] = None,
        max_width: int = 80
    ) -> str:
        """
        Create a visual representation of tokenization.
        
        Args:
            text: Original text
            tokens: List of tokens
            token_ids: Optional list of token IDs
            max_width: Maximum width for display
        
        Returns:
            Formatted visualization string
        """
        lines = ["=" * max_width]
        lines.append("TOKENIZATION VISUALIZATION")
        lines.append("=" * max_width)
        lines.append(f"Original text: {text[:max_width-15]}{'...' if len(text) > max_width-15 else ''}")
        lines.append(f"Number of tokens: {len(tokens)}")
        lines.append("-" * max_width)
        
        # Show tokens with IDs if available
        if token_ids and len(token_ids) == len(tokens):
            lines.append("Tokens with IDs:")
            for i, (token, token_id) in enumerate(zip(tokens, token_ids)):
                line = f"  {i:3d}: [{token_id:4d}] '{token}'"
                if len(line) > max_width:
                    line = line[:max_width-3] + "..."
                lines.append(line)
        else:
            lines.append("Tokens:")
            for i, token in enumerate(tokens):
                line = f"  {i:3d}: '{token}'"
                if len(line) > max_width:
                    line = line[:max_width-3] + "..."
                lines.append(line)
        
        lines.append("=" * max_width)
        return "\n".join(lines)
    
    @staticmethod
    def show_vocabulary_stats(vocab: Dict[str, int], top_n: int = 20) -> str:
        """
        Display vocabulary statistics.
        
        Args:
            vocab: Token to ID mapping
            top_n: Number of top tokens to show
        
        Returns:
            Formatted statistics string
        """
        lines = ["VOCABULARY STATISTICS"]
        lines.append("=" * 50)
        lines.append(f"Total vocabulary size: {len(vocab)}")
        
        # Token length distribution
        token_lengths = [len(token) for token in vocab.keys()]
        if token_lengths:
            lines.append(f"Average token length: {sum(token_lengths) / len(token_lengths):.2f}")
            lines.append(f"Min token length: {min(token_lengths)}")
            lines.append(f"Max token length: {max(token_lengths)}")
        
        # Show some example tokens
        lines.append(f"\nFirst {min(top_n, len(vocab))} tokens (by ID):")
        sorted_vocab = sorted(vocab.items(), key=lambda x: x[1])
        for token, token_id in sorted_vocab[:top_n]:
            lines.append(f"  [{token_id:4d}] '{token}'")
        
        return "\n".join(lines)
    
    @staticmethod
    def compare_tokenizations(
        text: str,
        tokenizations: Dict[str, List[str]],
        max_width: int = 80
    ) -> str:
        """
        Compare different tokenization results for the same text.
        
        Args:
            text: Original text
            tokenizations: Dictionary mapping method names to token lists
            max_width: Maximum width for display
        
        Returns:
            Formatted comparison string
        """
        lines = ["=" * max_width]
        lines.append("TOKENIZATION COMPARISON")
        lines.append("=" * max_width)
        lines.append(f"Text: {text[:max_width-6]}{'...' if len(text) > max_width-6 else ''}")
        lines.append("-" * max_width)
        
        for method_name, tokens in tokenizations.items():
            lines.append(f"\n{method_name.upper()} ({len(tokens)} tokens):")
            token_line = " | ".join(f"'{token}'" for token in tokens)
            if len(token_line) > max_width:
                token_line = token_line[:max_width-3] + "..."
            lines.append(f"  {token_line}")
        
        lines.append("=" * max_width)
        return "\n".join(lines)


class FrequencyAnalyzer:
    """Utility class for analyzing token and character frequencies."""
    
    @staticmethod
    def analyze_character_frequency(texts: List[str]) -> Counter:
        """
        Analyze character frequency across texts.
        
        Args:
            texts: List of text strings to analyze
        
        Returns:
            Counter object with character frequencies
        """
        char_counts = Counter()
        for text in texts:
            char_counts.update(text)
        return char_counts
    
    @staticmethod
    def analyze_word_frequency(texts: List[str]) -> Counter:
        """
        Analyze word frequency across texts.
        
        Args:
            texts: List of text strings to analyze
        
        Returns:
            Counter object with word frequencies
        """
        word_counts = Counter()
        for text in texts:
            words = TextProcessor.extract_words(text)
            word_counts.update(words)
        return word_counts
    
    @staticmethod
    def get_most_frequent(counter: Counter, n: int = 100) -> List[Tuple[str, int]]:
        """
        Get the most frequent items from a counter.
        
        Args:
            counter: Counter object
            n: Number of top items to return
        
        Returns:
            List of (item, count) tuples
        """
        return counter.most_common(n)
    
    @staticmethod
    def filter_by_frequency(
        counter: Counter, 
        min_freq: int = 2, 
        max_freq: Optional[int] = None
    ) -> Counter:
        """
        Filter counter items by frequency range.
        
        Args:
            counter: Counter object to filter
            min_freq: Minimum frequency to include
            max_freq: Maximum frequency to include (None for no limit)
        
        Returns:
            Filtered Counter object
        """
        filtered = Counter()
        for item, count in counter.items():
            if count >= min_freq:
                if max_freq is None or count <= max_freq:
                    filtered[item] = count
        return filtered


# Helper functions for common operations
def create_character_vocab(texts: List[str], min_freq: int = 1) -> Dict[str, int]:
    """
    Create a character-based vocabulary from texts.
    
    Args:
        texts: List of text strings
        min_freq: Minimum frequency for inclusion
    
    Returns:
        Character to ID mapping
    """
    char_freq = FrequencyAnalyzer.analyze_character_frequency(texts)
    filtered_chars = FrequencyAnalyzer.filter_by_frequency(char_freq, min_freq)
    
    vocab = {}
    for i, (char, _) in enumerate(filtered_chars.most_common()):
        vocab[char] = i
    
    return vocab


def create_word_vocab(texts: List[str], min_freq: int = 2, max_vocab: int = 10000) -> Dict[str, int]:
    """
    Create a word-based vocabulary from texts.
    
    Args:
        texts: List of text strings
        min_freq: Minimum frequency for inclusion
        max_vocab: Maximum vocabulary size
    
    Returns:
        Word to ID mapping
    """
    word_freq = FrequencyAnalyzer.analyze_word_frequency(texts)
    filtered_words = FrequencyAnalyzer.filter_by_frequency(word_freq, min_freq)
    
    vocab = {}
    for i, (word, _) in enumerate(filtered_words.most_common(max_vocab)):
        vocab[word] = i
    
    return vocab