"""
TokenizerBase - Abstract base class for all tokenizers in MyTecZ OmniToken.

This module defines the core interface that all tokenizer implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any, Optional
from collections import Counter
import json
import os
from pathlib import Path


class TokenizerConfig:
    """Configuration class for tokenizer parameters."""
    
    def __init__(
        self,
        vocab_size: int = 10000,
        min_frequency: int = 2,
        special_tokens: Optional[List[str]] = None,
        unk_token: str = "[UNK]",
        pad_token: str = "[PAD]",
        bos_token: str = "[BOS]",
        eos_token: str = "[EOS]",
        max_token_length: int = 100,
        case_sensitive: bool = True,
        **kwargs
    ):
        """
        Initialize tokenizer configuration.
        
        Args:
            vocab_size: Maximum vocabulary size
            min_frequency: Minimum token frequency to include in vocabulary
            special_tokens: List of special tokens to preserve
            unk_token: Token for unknown/out-of-vocabulary words
            pad_token: Padding token
            bos_token: Beginning of sequence token
            eos_token: End of sequence token
            max_token_length: Maximum length of individual tokens
            case_sensitive: Whether tokenization is case sensitive
            **kwargs: Additional configuration parameters
        """
        # Basic validation
        if vocab_size <= 0:
            raise ValueError("vocab_size must be > 0")
        if min_frequency < 1:
            raise ValueError("min_frequency must be >= 1")
        if 'dropout' in kwargs:
            dropout_val = kwargs['dropout']
            if not (0.0 <= dropout_val <= 1.0):
                raise ValueError("dropout must be between 0.0 and 1.0")

        self.vocab_size = vocab_size
        self.min_frequency = min_frequency
        self.special_tokens = special_tokens or []
        self.unk_token = unk_token
        self.pad_token = pad_token
        self.bos_token = bos_token
        self.eos_token = eos_token
        self.max_token_length = max_token_length
        self.case_sensitive = case_sensitive
        
        # Add special tokens to the list
        for token in [unk_token, pad_token, bos_token, eos_token]:
            if token not in self.special_tokens:
                self.special_tokens.append(token)
        
        # Store additional parameters
        for key, value in kwargs.items():
            setattr(self, key, value)


class TokenizerBase(ABC):
    """
    Abstract base class for all tokenizers.
    
    All tokenizer implementations must inherit from this class and implement
    the abstract methods: fit(), encode(), and decode().
    """
    
    def __init__(self, config: Optional[TokenizerConfig] = None, **kwargs):
        """
        Initialize the tokenizer with configuration.
        
        Args:
            config: TokenizerConfig instance or None to use defaults
            **kwargs: Additional configuration parameters
        """
        if config is None:
            config = TokenizerConfig(**kwargs)
        elif kwargs:
            # Merge kwargs into existing config
            for key, value in kwargs.items():
                setattr(config, key, value)
        
        self.config = config
        self.vocab = {}
        self.reverse_vocab = {}
        self.token_to_id = {}
        self.id_to_token = {}
        self.is_trained = False
        # Token frequency counter (populated after training via _build_frequency_map)
        self.token_frequencies: Counter[str] = Counter()

        # Initialize special tokens
        self._initialize_special_tokens()
    
    def _initialize_special_tokens(self):
        """Initialize special tokens in vocabulary."""
        for i, token in enumerate(self.config.special_tokens):
            self.token_to_id[token] = i
            self.id_to_token[i] = token
    
    @abstractmethod
    def fit(self, data: Union[str, List[str], Dict, List[Dict]]) -> 'TokenizerBase':
        """
        Train the tokenizer on the provided data.
        
        Args:
            data: Training data in various formats:
                  - String: raw text
                  - List[str]: list of texts or file paths
                  - Dict: JSON object with text content
                  - List[Dict]: list of JSON objects
        
        Returns:
            Self for method chaining
        """
        pass
    
    @abstractmethod
    def encode(self, text: str) -> List[int]:
        """
        Encode text into token IDs.
        
        Args:
            text: Input text to tokenize
        
        Returns:
            List of token IDs
        """
        pass
    
    @abstractmethod
    def decode(self, token_ids: List[int]) -> str:
        """
        Decode token IDs back to text.
        
        Args:
            token_ids: List of token IDs to decode
        
        Returns:
            Decoded text string
        """
        pass
    
    def encode_batch(self, texts: List[str]) -> List[List[int]]:
        """
        Encode a batch of texts.
        
        Args:
            texts: List of text strings to encode
        
        Returns:
            List of token ID lists
        """
        return [self.encode(text) for text in texts]
    
    def decode_batch(self, token_ids_batch: List[List[int]]) -> List[str]:
        """
        Decode a batch of token ID sequences.
        
        Args:
            token_ids_batch: List of token ID lists to decode
        
        Returns:
            List of decoded text strings
        """
        return [self.decode(token_ids) for token_ids in token_ids_batch]
    
    def get_vocab_size(self) -> int:
        """Get the current vocabulary size."""
        return len(self.token_to_id)
    
    def get_vocab(self) -> Dict[str, int]:
        """Get the token to ID mapping."""
        return self.token_to_id.copy()

    def get_token_frequencies(self) -> Dict[str, int]:
        """
        Get observed token frequency counts from the training data (if available).

        Returns:
            A copy of the token -> frequency mapping. Empty if frequencies were
            not (yet) computed (e.g., fit not called or skipped).
        """
        return dict(self.token_frequencies)

    def get_most_common_tokens(self, n: int = 20) -> List[tuple]:
        """Return the n most common (token, frequency) pairs."""
        return self.token_frequencies.most_common(n)
    
    # ------------------------------------------------------------------
    # Special token handling utilities
    # ------------------------------------------------------------------
    def _merge_with_special_tokens(self, trained_vocab: Dict[str, int]) -> Dict[str, int]:
        """Merge a freshly trained vocabulary with existing special tokens.

        Ensures special tokens occupy the lowest ID range and are not duplicated.
        """
        merged: Dict[str, int] = {}
        # Preserve insertion order of special tokens
        for idx, token in enumerate(self.config.special_tokens):
            merged[token] = idx
        next_id = len(merged)
        for token, _ in sorted(trained_vocab.items(), key=lambda x: x[1]):
            if token not in merged:
                merged[token] = next_id
                next_id += 1
        return merged
    
    def save_vocabulary(self, filepath: str) -> None:
        """
        Save the vocabulary to a JSON file.
        
        Args:
            filepath: Path to save the vocabulary
        """
        vocab_data = {
            "token_to_id": self.token_to_id,
            "config": self.config.__dict__,
            "tokenizer_type": self.__class__.__name__
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(vocab_data, f, ensure_ascii=False, indent=2)
    
    def load_vocabulary(self, filepath: str) -> None:
        """
        Load vocabulary from a JSON file.
        
        Args:
            filepath: Path to the vocabulary file
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            vocab_data = json.load(f)
        
        self.token_to_id = vocab_data["token_to_id"]
        self.id_to_token = {int(id_): token for token, id_ in self.token_to_id.items()}
        
        # Update config if present
        if "config" in vocab_data:
            for key, value in vocab_data["config"].items():
                setattr(self.config, key, value)
        
        self.is_trained = True
    
    def _detect_input_type(self, data: Any) -> str:
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
    
    def _extract_text_from_input(self, data: Any) -> List[str]:
        """
        Extract text content from various input formats.
        
        Args:
            data: Input data in various formats
        
        Returns:
            List of text strings
        """
        input_type = self._detect_input_type(data)
        texts = []
        
        if input_type == "string":
            # Heuristic: if looks like a path but doesn't exist, raise
            if (('/' in data or '\\' in data or data.endswith(('.txt', '.json', '.md'))) 
                and not os.path.exists(data)):
                raise FileNotFoundError(data)
            texts.append(data)
        
        elif input_type == "file":
            texts.extend(self._read_file(data))
        
        elif input_type == "files":
            for filepath in data:
                texts.extend(self._read_file(filepath))
        
        elif input_type == "list":
            for item in data:
                if isinstance(item, str):
                    texts.append(item)
                elif isinstance(item, dict):
                    texts.extend(self._extract_text_from_json(item))
        
        elif input_type == "json":
            texts.extend(self._extract_text_from_json(data))
        
        return texts
    
    def _read_file(self, filepath: str) -> List[str]:
        """
        Read text content from a file.
        
        Args:
            filepath: Path to the file
        
        Returns:
            List of text lines or content
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(filepath)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detect file type and parse accordingly
            file_ext = Path(filepath).suffix.lower()
            
            if file_ext == '.json':
                try:
                    json_data = json.loads(content)
                    return self._extract_text_from_json(json_data)
                except json.JSONDecodeError:
                    return [content]
            else:
                # For text, markdown, code files, etc.
                return [content]
        
        except Exception as e:
            print(f"Warning: Could not read file {filepath}: {e}")
            return []
    
    def _extract_text_from_json(self, json_data: Union[Dict, List]) -> List[str]:
        """
        Extract text content from JSON data.
        
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
    
    def verify_round_trip(self, text: str) -> bool:
        """
        Verify that encoding and then decoding returns the original text.
        
        Args:
            text: Original text to test
        
        Returns:
            True if round-trip is successful, False otherwise
        """
        try:
            tokens = self.encode(text)
            decoded = self.decode(tokens)
            return text == decoded
        except Exception:
            return False

    # ---------------------------------------------------------------------
    # Internal helpers for frequency accounting
    # ---------------------------------------------------------------------
    def _build_frequency_map(self, texts: List[str]) -> None:
        """
        Build a token frequency map from a list of raw training texts using the
        tokenizer's encode/decode pipeline. This is a post-training step and
        will no-op if the tokenizer is not yet trained.

        Args:
            texts: List of raw text strings used during training.
        """
        if not self.is_trained:
            return
        freq: Counter[str] = Counter()
        for t in texts:
            try:
                token_ids = self.encode(t)
                # Convert IDs back to token strings for frequency accounting
                for tid in token_ids:
                    token = self.id_to_token.get(tid)
                    if token is not None:
                        freq[token] += 1
            except Exception:
                # Skip problematic lines but continue (robustness over strictness)
                continue
        self.token_frequencies = freq
    
    def __repr__(self) -> str:
        """String representation of the tokenizer."""
        return f"{self.__class__.__name__}(vocab_size={self.get_vocab_size()}, trained={self.is_trained})"