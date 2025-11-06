"""
SentencePiece-like Tokenizer for MyTecZ OmniToken.

This module implements a SentencePiece-inspired tokenizer that treats text as
a sequence of characters and uses subword segmentation without explicit word boundaries.
"""

import re
from typing import List, Dict, Optional, Set, Tuple
from .tokenizer_base import TokenizerBase, TokenizerConfig
from .trainer import SentencePieceTrainer
from .utils import TextProcessor


class SentencePieceTokenizer(TokenizerBase):
    """
    SentencePiece-like tokenizer implementation.
    
    This tokenizer treats text as a raw sequence of characters and learns
    subword units without relying on pre-tokenization or word boundaries.
    """
    
    def __init__(self, config: Optional[TokenizerConfig] = None, **kwargs):
        """
        Initialize SentencePiece tokenizer.
        
        Args:
            config: TokenizerConfig instance
            **kwargs: Additional configuration parameters
        """
        super().__init__(config, **kwargs)
        
        # SentencePiece-specific config
        self.character_coverage = getattr(self.config, 'character_coverage', 0.9995)
        self.model_type = getattr(self.config, 'model_type', 'unigram')  # unigram, bpe
        self.split_by_whitespace = getattr(self.config, 'split_by_whitespace', True)
        self.split_by_unicode_script = getattr(self.config, 'split_by_unicode_script', True)
        self.split_by_number = getattr(self.config, 'split_by_number', True)
        self.remove_extra_whitespaces = getattr(self.config, 'remove_extra_whitespaces', True)
        self.normalization_rule_name = getattr(self.config, 'normalization_rule_name', 'nfc')
        
        # Special SentencePiece tokens
        sp_special_tokens = ['<s>', '</s>', '<unk>', '<pad>']
        for token in sp_special_tokens:
            if token not in self.config.special_tokens:
                self.config.special_tokens.append(token)
        
        # Character-to-byte mapping for handling any Unicode
        self.char_to_byte = {}
        self.byte_to_char = {}
        self._initialize_byte_mapping()
    
    def _initialize_byte_mapping(self):
        """Initialize character to byte mapping for robust Unicode handling."""
        # Create a mapping for bytes 0-255 to Unicode characters
        for i in range(256):
            # Use a safe Unicode range that won't conflict with normal text
            if i < 128:
                # ASCII characters map to themselves
                char = chr(i)
            else:
                # Map high bytes to private use area
                char = chr(0xE000 + i - 128)  # Private Use Area
            
            self.char_to_byte[char] = i
            self.byte_to_char[i] = char
    
    def fit(self, data) -> 'SentencePieceTokenizer':
        """
        Train the SentencePiece tokenizer on provided data.
        
        Args:
            data: Training data in various formats
        
        Returns:
            Self for method chaining
        """
        # Extract text from various input formats
        texts = self._extract_text_from_input(data)
        
        if not texts:
            raise ValueError("No text data found for training")
        
        # Preprocess texts
        processed_texts = []
        for text in texts:
            processed_text = self._preprocess_text(text)
            processed_texts.append(processed_text)
        
        # Initialize SentencePiece trainer
        trainer = SentencePieceTrainer(
            vocab_size=self.config.vocab_size,
            character_coverage=self.character_coverage
        )
        
        # Train vocabulary
        vocab = trainer.train(processed_texts)

        # Update tokenizer state (merge in special tokens)
        merged_vocab = self._merge_with_special_tokens(vocab)
        self.token_to_id = merged_vocab
        self.id_to_token = {id_: token for token, id_ in merged_vocab.items()}
        self.is_trained = True
        # Build frequency map from training texts
        self._build_frequency_map(texts)
        
        return self
    
    def encode(self, text: str) -> List[int]:
        """
        Encode text into token IDs using SentencePiece.
        
        Args:
            text: Input text to tokenize
        
        Returns:
            List of token IDs
        """
        if not self.is_trained:
            raise ValueError("Tokenizer must be trained before encoding")
        
        # Preprocess text
        text = self._preprocess_text(text)
        
        # Tokenize using the learned vocabulary
        tokens = self._tokenize_text(text)
        
        # Convert to IDs
        token_ids = []
        for token in tokens:
            token_id = self.token_to_id.get(token, self.token_to_id.get('<unk>', 0))
            token_ids.append(token_id)
        
        return token_ids
    
    def decode(self, token_ids: List[int]) -> str:
        """
        Decode token IDs back to text.
        
        Args:
            token_ids: List of token IDs to decode
        
        Returns:
            Decoded text string
        """
        if not self.is_trained:
            raise ValueError("Tokenizer must be trained before decoding")
        
        # Convert IDs to tokens
        tokens = []
        for token_id in token_ids:
            token = self.id_to_token.get(token_id, '<unk>')
            tokens.append(token)
        
        # Join tokens and decode
        text = self._detokenize(tokens)
        
        return text
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text according to SentencePiece rules.
        
        Args:
            text: Input text
        
        Returns:
            Preprocessed text
        """
        # Unicode normalization
        if self.normalization_rule_name == 'nfc':
            text = TextProcessor.normalize_unicode(text)
        
        # Remove extra whitespaces
        if self.remove_extra_whitespaces:
            text = re.sub(r'\s+', ' ', text.strip())
        
        # Convert to raw byte sequence for robust handling
        text = self._encode_as_bytes(text)
        
        return text
    
    def _encode_as_bytes(self, text: str) -> str:
        """
        Encode text as a sequence of byte characters.
        
        Args:
            text: Input text
        
        Returns:
            Byte-encoded text
        """
        # Convert to UTF-8 bytes then to our character representation
        byte_sequence = text.encode('utf-8')
        char_sequence = ''.join(self.byte_to_char[byte] for byte in byte_sequence)
        return char_sequence
    
    def _decode_from_bytes(self, char_sequence: str) -> str:
        """
        Decode byte character sequence back to text.
        
        Args:
            char_sequence: Byte character sequence
        
        Returns:
            Decoded text
        """
        try:
            # Convert character sequence back to bytes
            byte_sequence = bytes(self.char_to_byte.get(char, 0) for char in char_sequence)
            # Decode UTF-8 bytes to text
            return byte_sequence.decode('utf-8', errors='replace')
        except Exception:
            return char_sequence  # Fallback
    
    def _tokenize_text(self, text: str) -> List[str]:
        """
        Tokenize preprocessed text using the learned vocabulary.
        
        Args:
            text: Preprocessed text
        
        Returns:
            List of tokens
        """
        if not text:
            return []
        
        # Use a greedy approach to segment text
        tokens = []
        i = 0
        
        while i < len(text):
            # Find the longest matching token starting at position i
            best_token = None
            best_length = 0
            
            # Check all possible substrings starting at i
            for j in range(i + 1, min(i + 50, len(text) + 1)):  # Limit max token length
                substring = text[i:j]
                if substring in self.token_to_id:
                    if len(substring) > best_length:
                        best_token = substring
                        best_length = len(substring)
            
            if best_token:
                tokens.append(best_token)
                i += best_length
            else:
                # Fall back to single character or unknown token
                char = text[i]
                if char in self.token_to_id:
                    tokens.append(char)
                else:
                    tokens.append('<unk>')
                i += 1
        
        return tokens
    
    def _detokenize(self, tokens: List[str]) -> str:
        """
        Convert tokens back to text.
        
        Args:
            tokens: List of tokens
        
        Returns:
            Detokenized text
        """
        # Join all tokens
        char_sequence = ''.join(tokens)
        
        # Decode from byte representation
        text = self._decode_from_bytes(char_sequence)
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text and return the actual tokens (not IDs).
        
        Args:
            text: Input text to tokenize
        
        Returns:
            List of token strings
        """
        if not self.is_trained:
            raise ValueError("Tokenizer must be trained before tokenizing")
        
        # Preprocess and tokenize
        processed_text = self._preprocess_text(text)
        tokens = self._tokenize_text(processed_text)
        
        return tokens
    
    def encode_as_pieces(self, text: str) -> List[str]:
        """
        Encode text as pieces (same as tokenize).
        
        Args:
            text: Input text
        
        Returns:
            List of pieces
        """
        return self.tokenize(text)
    
    def decode_pieces(self, pieces: List[str]) -> str:
        """
        Decode pieces back to text.
        
        Args:
            pieces: List of pieces
        
        Returns:
            Decoded text
        """
        return self._detokenize(pieces)
    
    def split_by_script(self, text: str) -> List[str]:
        """
        Split text by Unicode script (experimental).
        
        Args:
            text: Input text
        
        Returns:
            List of text segments
        """
        import unicodedata
        
        if not text:
            return []
        
        segments = []
        current_segment = ""
        current_script = None
        
        for char in text:
            try:
                script = unicodedata.name(char).split()[0] if unicodedata.name(char, None) else "UNKNOWN"
            except:
                script = "UNKNOWN"
            
            if current_script is None:
                current_script = script
                current_segment = char
            elif script == current_script:
                current_segment += char
            else:
                if current_segment:
                    segments.append(current_segment)
                current_segment = char
                current_script = script
        
        if current_segment:
            segments.append(current_segment)
        
        return segments
    
    def get_vocab_size(self) -> int:
        """Get vocabulary size."""
        return len(self.token_to_id)
    
    def is_unknown(self, token: str) -> bool:
        """
        Check if a token is unknown.
        
        Args:
            token: Token to check
        
        Returns:
            True if unknown, False otherwise
        """
        return token not in self.token_to_id
    
    def get_piece_size(self) -> int:
        """Get the number of pieces in vocabulary."""
        return len(self.token_to_id)
    
    def id_to_piece(self, token_id: int) -> str:
        """
        Convert token ID to piece.
        
        Args:
            token_id: Token ID
        
        Returns:
            Corresponding piece
        """
        return self.id_to_token.get(token_id, '<unk>')
    
    def piece_to_id(self, piece: str) -> int:
        """
        Convert piece to token ID.
        
        Args:
            piece: Piece string
        
        Returns:
            Corresponding token ID
        """
        return self.token_to_id.get(piece, self.token_to_id.get('<unk>', 0))
    
    def get_tokenization_info(self, text: str) -> Dict:
        """
        Get detailed tokenization information for analysis.
        
        Args:
            text: Input text to analyze
        
        Returns:
            Dictionary with tokenization details
        """
        if not self.is_trained:
            raise ValueError("Tokenizer must be trained before analysis")
        
        original_text = text
        processed_text = self._preprocess_text(text)
        tokens = self._tokenize_text(processed_text)
        token_ids = self.encode(text)
        
        # Count character types
        byte_tokens = sum(1 for t in tokens if len(t) == 1 and ord(t) >= 0xE000)
        unicode_tokens = sum(1 for t in tokens if len(t) == 1 and ord(t) < 0xE000)
        subword_tokens = sum(1 for t in tokens if len(t) > 1)
        unk_tokens = sum(1 for t in tokens if t == '<unk>')
        
        info = {
            "original_text": original_text,
            "processed_text": processed_text,
            "tokens": tokens,
            "token_ids": token_ids,
            "num_tokens": len(tokens),
            "byte_tokens": byte_tokens,
            "unicode_tokens": unicode_tokens,
            "subword_tokens": subword_tokens,
            "unk_tokens": unk_tokens,
            "compression_ratio": len(original_text) / len(tokens) if tokens else 0,
            "character_coverage": self.character_coverage,
            "model_type": self.model_type
        }
        
        return info
    
    def sample_encode(self, text: str, alpha: float = 0.1, nbest: int = 64) -> List[int]:
        """
        Sample-based encoding for regularization (simplified implementation).
        
        Args:
            text: Input text
            alpha: Sampling parameter
            nbest: Number of best candidates
        
        Returns:
            List of sampled token IDs
        """
        # For now, just return regular encoding
        # A full implementation would use probabilistic sampling
        return self.encode(text)
    
    def enable_sampling(self) -> None:
        """Enable sampling mode."""
        self._sampling_enabled = True
    
    def disable_sampling(self) -> None:
        """Disable sampling mode."""
        self._sampling_enabled = False