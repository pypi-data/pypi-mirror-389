"""
BPE (Byte Pair Encoding) Tokenizer for MyTecZ OmniToken.

This module implements a BPE tokenizer that learns merge operations
to create subword tokens, providing a balance between vocabulary size
and representation capability.
"""

import re
from typing import List, Dict, Tuple, Optional
from collections import Counter
from .tokenizer_base import TokenizerBase, TokenizerConfig
from .trainer import BPETrainer
from .utils import TextProcessor


class BPETokenizer(TokenizerBase):
    """
    Byte Pair Encoding (BPE) tokenizer implementation.
    
    BPE learns merge operations to iteratively combine the most frequent
    adjacent pairs of tokens, creating a subword vocabulary that balances
    between character-level and word-level tokenization.
    """
    
    def __init__(self, config: Optional[TokenizerConfig] = None, **kwargs):
        """
        Initialize BPE tokenizer.
        
        Args:
            config: TokenizerConfig instance
            **kwargs: Additional configuration parameters
        """
        super().__init__(config, **kwargs)
        self.merges = []  # List of merge operations (pair tuples)
        self.cache = {}   # Cache for tokenized words
        
        # BPE-specific config
        self.dropout = getattr(self.config, 'dropout', 0.0)
        self.continuing_subword_prefix = getattr(self.config, 'continuing_subword_prefix', '')
        self.end_of_word_suffix = getattr(self.config, 'end_of_word_suffix', '</w>')
    
    def fit(self, data) -> 'BPETokenizer':
        """
        Train the BPE tokenizer on provided data.
        
        Args:
            data: Training data in various formats
        
        Returns:
            Self for method chaining
        """
        # Extract text from various input formats
        texts = self._extract_text_from_input(data)
        
        if not texts:
            raise ValueError("No text data found for training")
        
        # Initialize BPE trainer
        trainer = BPETrainer(
            vocab_size=self.config.vocab_size,
            min_frequency=self.config.min_frequency
        )
        
        # Train BPE vocabulary and get merge operations
        vocab, merges = trainer.train(texts)
        
        # Update tokenizer state (merge in special tokens first)
        merged_vocab = self._merge_with_special_tokens(vocab)
        self.token_to_id = merged_vocab
        self.id_to_token = {id_: token for token, id_ in merged_vocab.items()}
        self.merges = merges
        self.is_trained = True
        # Build frequency map from training texts
        self._build_frequency_map(texts)
        
        return self
    
    def encode(self, text: str) -> List[int]:
        """
        Encode text into token IDs using BPE.
        
        Args:
            text: Input text to tokenize
        
        Returns:
            List of token IDs
        """
        if not self.is_trained:
            raise ValueError("Tokenizer must be trained before encoding")
        if text in self.token_to_id:
            return [self.token_to_id[text]]
        
        # Normalize and clean text
        text = TextProcessor.normalize_unicode(text)
        
        # Extract words and tokenize each
        words = self._extract_words_for_bpe(text)
        token_ids = []
        
        for word in words:
            # Add end-of-word marker
            word_with_eow = word + self.end_of_word_suffix
            
            # Get BPE tokens for the word
            bpe_tokens = self._get_word_tokens(word_with_eow)
            
            # Convert tokens to IDs
            for token in bpe_tokens:
                token_id = self.token_to_id.get(token, self.token_to_id.get(self.config.unk_token, 0))
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
            token = self.id_to_token.get(token_id, self.config.unk_token)
            tokens.append(token)
        
        # Join tokens and clean up
        text = ''.join(tokens)
        
        # Remove end-of-word markers
        text = text.replace(self.end_of_word_suffix, ' ')
        
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def _extract_words_for_bpe(self, text: str) -> List[str]:
        """
        Extract words from text for BPE processing.
        
        Args:
            text: Input text
        
        Returns:
            List of words
        """
        # Use a more sophisticated word extraction that preserves punctuation context
        # This regex captures words, punctuation, and whitespace patterns
        pattern = r'\b\w+\b|[^\w\s]'
        tokens = re.findall(pattern, text)
        
        # Filter out empty tokens
        return [token for token in tokens if token.strip()]
    
    def _get_word_tokens(self, word: str) -> List[str]:
        """
        Get BPE tokens for a single word using learned merges.
        
        Args:
            word: Word to tokenize (with end-of-word marker)
        
        Returns:
            List of BPE tokens
        """
        # Check cache first
        if word in self.cache:
            return self.cache[word]
        
        # Initialize with individual characters
        tokens = list(word)
        
        # Apply merge operations
        for merge_pair in self.merges:
            tokens = self._apply_merge(tokens, merge_pair)
        
        # Cache the result
        self.cache[word] = tokens
        
        return tokens
    
    def _apply_merge(self, tokens: List[str], merge_pair: Tuple[str, str]) -> List[str]:
        """
        Apply a single merge operation to a list of tokens.
        
        Args:
            tokens: Current list of tokens
            merge_pair: Pair of tokens to merge
        
        Returns:
            Updated list of tokens after merge
        """
        if len(tokens) < 2:
            return tokens
        
        new_tokens = []
        i = 0
        
        while i < len(tokens):
            if (i < len(tokens) - 1 and 
                tokens[i] == merge_pair[0] and 
                tokens[i + 1] == merge_pair[1]):
                # Merge the pair
                merged_token = merge_pair[0] + merge_pair[1]
                new_tokens.append(merged_token)
                i += 2  # Skip both tokens
            else:
                new_tokens.append(tokens[i])
                i += 1
        
        return new_tokens
    
    def get_merge_operations(self) -> List[Tuple[str, str]]:
        """
        Get the learned merge operations.
        
        Returns:
            List of merge operation pairs
        """
        return self.merges.copy()
    
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
        
        # Normalize text
        text = TextProcessor.normalize_unicode(text)
        
        # Extract words and tokenize
        words = self._extract_words_for_bpe(text)
        all_tokens = []
        
        for word in words:
            word_with_eow = word + self.end_of_word_suffix
            bpe_tokens = self._get_word_tokens(word_with_eow)
            all_tokens.extend(bpe_tokens)
        
        return all_tokens
    
    def apply_dropout(self, tokens: List[str], dropout_rate: Optional[float] = None) -> List[str]:
        """
        Apply BPE dropout for regularization during training.
        
        Args:
            tokens: List of tokens
            dropout_rate: Dropout rate (if None, uses config value)
        
        Returns:
            List of tokens with dropout applied
        """
        import random
        
        if dropout_rate is None:
            dropout_rate = self.dropout
        
        if dropout_rate <= 0.0:
            return tokens
        
        # Randomly skip some merge operations
        modified_merges = []
        for merge in self.merges:
            if random.random() > dropout_rate:
                modified_merges.append(merge)
        
        # Re-tokenize with modified merges
        original_merges = self.merges
        self.merges = modified_merges
        
        result = []
        for token in tokens:
            if token.endswith(self.end_of_word_suffix):
                word_tokens = self._get_word_tokens(token)
                result.extend(word_tokens)
            else:
                result.append(token)
        
        # Restore original merges
        self.merges = original_merges
        
        return result
    
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
        
        tokens = self.tokenize(text)
        token_ids = self.encode(text)
        
        info = {
            "original_text": text,
            "tokens": tokens,
            "token_ids": token_ids,
            "num_tokens": len(tokens),
            "compression_ratio": len(text) / len(tokens) if tokens else 0,
            "avg_token_length": sum(len(token) for token in tokens) / len(tokens) if tokens else 0,
            "oov_tokens": [token for token in tokens if token not in self.token_to_id],
            "merge_operations_used": len(self.merges)
        }
        
        return info
    
    def save_model(self, filepath: str) -> None:
        """
        Save the complete BPE model (vocabulary + merges).
        
        Args:
            filepath: Path to save the model
        """
        import json
        
        model_data = {
            "vocab": self.token_to_id,
            "merges": self.merges,
            "config": self.config.__dict__,
            "tokenizer_type": "BPE"
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, ensure_ascii=False, indent=2)
    
    def load_model(self, filepath: str) -> None:
        """
        Load a complete BPE model.
        
        Args:
            filepath: Path to the model file
        """
        import json
        
        with open(filepath, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        
        self.token_to_id = model_data["vocab"]
        self.id_to_token = {int(id_): token for token, id_ in self.token_to_id.items()}
        self.merges = [tuple(merge) for merge in model_data["merges"]]
        
        # Update config
        if "config" in model_data:
            for key, value in model_data["config"].items():
                setattr(self.config, key, value)
        
        self.is_trained = True
        self.cache = {}  # Clear cache
    
    def clear_cache(self) -> None:
        """Clear the tokenization cache."""
        self.cache = {}
    
    def get_cache_size(self) -> int:
        """Get the current cache size."""
        return len(self.cache)