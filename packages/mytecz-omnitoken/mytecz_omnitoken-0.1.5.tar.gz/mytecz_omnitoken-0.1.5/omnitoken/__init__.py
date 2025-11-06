"""
MyTecZ OmniToken - Universal Tokenizer

A modular, extensible tokenizer supporting multiple tokenization strategies:
- Character-based
- BPE (Byte Pair Encoding)
- WordPiece
- SentencePiece
- Hybrid experimental mode

Features:
- Deterministic and reversible tokenization
- Unicode and emoji support
- Multi-language support
- Multiple input formats (files, JSON, raw strings)
- Configurable parameters
- Built-in visualizer
"""

from .tokenizer_base import TokenizerBase
from .tokenizer_bpe import BPETokenizer
from .tokenizer_wordpiece import WordPieceTokenizer
from .tokenizer_sentencepiece import SentencePieceTokenizer
from .tokenizer_hybrid import HybridTokenizer
from .trainer import Trainer
from .utils import InputDetector, TokenVisualizer

__version__ = "0.1.5"
__author__ = "MyTecZ"
__description__ = "Universal tokenizer with modular architecture"

# Main interface
class OmniToken:
    """
    Main interface for the OmniToken universal tokenizer.
    
    Supports multiple tokenization methods and input formats.
    """
    
    def __init__(self, method: str = "bpe", mode: str | None = None, **kwargs):
        """
        Initialize OmniToken with specified tokenization method.
        
        Args:
            method: Tokenization method ("bpe", "wordpiece", "sentencepiece", "hybrid").
            mode: Alias for method (takes precedence if provided). Useful for
                  ergonomics / backwards compatibility with configs using 'mode'.
            **kwargs: Additional configuration parameters
        """
        if mode is not None:
            if method != "bpe" and mode != method:
                raise ValueError(f"Conflicting values provided: method={method} vs mode={mode}")
            self.method = mode
        else:
            self.method = method
        self.config = kwargs
        self._tokenizer = self._create_tokenizer()
    
    def _create_tokenizer(self) -> TokenizerBase:
        """Create the appropriate tokenizer based on method."""
        method_map = {
            "bpe": BPETokenizer,
            "wordpiece": WordPieceTokenizer,
            "sentencepiece": SentencePieceTokenizer,
            "hybrid": HybridTokenizer
        }
        
        if self.method not in method_map:
            raise ValueError(f"Unknown tokenization method: {self.method}")
        
        return method_map[self.method](**self.config)
    
    def fit(self, data):
        """Train the tokenizer on provided data."""
        return self._tokenizer.fit(data)
    
    def encode(self, text: str):
        """Encode text into tokens."""
        return self._tokenizer.encode(text)
    
    def decode(self, tokens):
        """Decode tokens back to text."""
        return self._tokenizer.decode(tokens)

    # ------------------------------------------------------------------
    # Convenience pass-through APIs
    # ------------------------------------------------------------------
    def get_vocab(self):
        """Return the underlying tokenizer vocabulary mapping (token -> id)."""
        return self._tokenizer.get_vocab()

    def get_token_frequencies(self):
        """Return token frequency counts gathered during training (if available)."""
        if hasattr(self._tokenizer, "get_token_frequencies"):
            return self._tokenizer.get_token_frequencies()
        return {}

__all__ = [
    "OmniToken",
    "TokenizerBase",
    "BPETokenizer",
    "WordPieceTokenizer", 
    "SentencePieceTokenizer",
    "HybridTokenizer",
    "Trainer",
    "InputDetector",
    "TokenVisualizer"
]