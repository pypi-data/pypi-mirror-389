"""
Hybrid Tokenizer for MyTecZ OmniToken.

This module implements an experimental hybrid tokenizer that combines multiple
tokenization strategies (character, word, subword) for optimal performance
across different types of text.
"""

import re
from typing import List, Dict, Optional, Tuple, Set, Any
from enum import Enum
from .tokenizer_base import TokenizerBase, TokenizerConfig
from .tokenizer_bpe import BPETokenizer
from .tokenizer_wordpiece import WordPieceTokenizer
from .tokenizer_sentencepiece import SentencePieceTokenizer
from .trainer import HybridTrainer
from .utils import TextProcessor, FrequencyAnalyzer


class TokenizationStrategy(Enum):
    """Enumeration of different tokenization strategies."""
    CHARACTER = "character"
    WORD = "word"
    BPE = "bpe"
    WORDPIECE = "wordpiece"
    SENTENCEPIECE = "sentencepiece"
    ADAPTIVE = "adaptive"


class HybridTokenizer(TokenizerBase):
    """
    Hybrid tokenizer that combines multiple tokenization strategies.
    
    This tokenizer can adaptively choose the best tokenization strategy
    based on the input text characteristics, or use a fixed combination
    of different strategies.
    """
    
    def __init__(self, config: Optional[TokenizerConfig] = None, **kwargs):
        """
        Initialize Hybrid tokenizer.
        
        Args:
            config: TokenizerConfig instance
            **kwargs: Additional configuration parameters
        """
        super().__init__(config, **kwargs)
        
        # Hybrid-specific configuration
        self.strategies = getattr(self.config, 'strategies', ['character', 'word', 'bpe'])
        self.strategy_weights = getattr(self.config, 'strategy_weights', None)
        self.adaptive_mode = getattr(self.config, 'adaptive_mode', True)
        self.fallback_strategy = getattr(self.config, 'fallback_strategy', 'character')
        self.char_ratio = getattr(self.config, 'char_ratio', 0.3)
        self.word_ratio = getattr(self.config, 'word_ratio', 0.4)
        self.subword_ratio = getattr(self.config, 'subword_ratio', 0.3)
        
        # Initialize strategy-specific vocabularies
        self.char_vocab = {}
        self.word_vocab = {}
        self.subword_vocab = {}
        self.strategy_vocabs = {}
        
        # Token type markers
        self.char_prefix = getattr(self.config, 'char_prefix', '<CHAR>')
        self.word_prefix = getattr(self.config, 'word_prefix', '<WORD>')
        self.subword_prefix = getattr(self.config, 'subword_prefix', '<SUB>')
        
        # Adaptive thresholds
        self.word_frequency_threshold = getattr(self.config, 'word_frequency_threshold', 10)
        self.char_fallback_ratio = getattr(self.config, 'char_fallback_ratio', 0.3)
        
        # Cache for tokenization decisions
        self.tokenization_cache = {}
    
    def fit(self, data) -> 'HybridTokenizer':
        """
        Train the hybrid tokenizer on provided data.
        
        Args:
            data: Training data in various formats
        
        Returns:
            Self for method chaining
        """
        # Extract text from various input formats
        texts = self._extract_text_from_input(data)
        
        if not texts:
            raise ValueError("No text data found for training")
        
        # Train hybrid vocabulary
        trainer = HybridTrainer(
            vocab_size=self.config.vocab_size,
            char_ratio=self.char_ratio,
            word_ratio=self.word_ratio,
            subword_ratio=self.subword_ratio
        )
        
        vocab = trainer.train(texts)
        
        # Separate vocabularies by type
        self._separate_vocabularies(vocab, texts)

        # Update main vocabulary (merge special tokens)
        merged_vocab = self._merge_with_special_tokens(vocab)
        self.token_to_id = merged_vocab
        self.id_to_token = {id_: token for token, id_ in merged_vocab.items()}
        self.is_trained = True
        # Build frequency map from training texts
        self._build_frequency_map(texts)
        
        return self
    
    def _separate_vocabularies(self, vocab: Dict[str, int], texts: List[str]):
        """
        Separate the main vocabulary into strategy-specific vocabularies.
        
        Args:
            vocab: Main vocabulary
            texts: Training texts for analysis
        """
        # Analyze character and word frequencies
        char_freq = FrequencyAnalyzer.analyze_character_frequency(texts)
        word_freq = FrequencyAnalyzer.analyze_word_frequency(texts)
        
        # Classify tokens by type
        for token, token_id in vocab.items():
            if len(token) == 1 and not token.isalnum():
                # Single character (punctuation, symbols)
                self.char_vocab[token] = token_id
            elif len(token) == 1 and token.isalnum():
                # Single alphanumeric character
                self.char_vocab[token] = token_id
            elif token in word_freq and word_freq[token] >= self.word_frequency_threshold:
                # High-frequency word
                self.word_vocab[token] = token_id
            elif ' ' not in token and len(token) > 1:
                # Subword token
                self.subword_vocab[token] = token_id
            else:
                # Default to character vocab
                self.char_vocab[token] = token_id
        
        # Store strategy vocabularies
        self.strategy_vocabs = {
            'character': self.char_vocab,
            'word': self.word_vocab,
            'subword': self.subword_vocab
        }
    
    def encode(self, text: str) -> List[int]:
        """
        Encode text using hybrid tokenization strategy.
        
        Args:
            text: Input text to tokenize
        
        Returns:
            List of token IDs
        """
        if not self.is_trained:
            raise ValueError("Tokenizer must be trained before encoding")
        
        # Normalize text
        text = TextProcessor.normalize_unicode(text)
        
        # Choose tokenization strategy
        if self.adaptive_mode:
            tokens = self._adaptive_tokenize(text)
        else:
            tokens = self._fixed_strategy_tokenize(text)
        
        # Convert to IDs
        token_ids = []
        for token in tokens:
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
        
        # Join tokens intelligently
        text = self._intelligent_detokenize(tokens)
        if not text.strip():
            # Simple fallback: concatenate tokens ignoring padding/sequence tokens but keep UNK
            non_padding_tokens = [t for t in tokens if t not in ['[PAD]', '[BOS]', '[EOS]']]
            text = ''.join(non_padding_tokens)
            # If still empty, return UNK as last resort
            if not text.strip() and tokens:
                text = self.config.unk_token
        
        return text
    
    def _adaptive_tokenize(self, text: str) -> List[str]:
        """
        Adaptively tokenize text based on content characteristics.
        
        Args:
            text: Input text
        
        Returns:
            List of tokens
        """
        # Analyze text characteristics
        text_stats = self._analyze_text_characteristics(text)
        
        # Choose optimal strategy based on characteristics
        strategy = self._choose_optimal_strategy(text_stats)
        
        # Apply the chosen strategy
        return self._apply_strategy(text, strategy, text_stats)
    
    def _analyze_text_characteristics(self, text: str) -> Dict[str, Any]:
        """
        Analyze characteristics of the input text.
        
        Args:
            text: Input text to analyze
        
        Returns:
            Dictionary with text characteristics
        """
        words = TextProcessor.extract_words(text)
        chars = list(text)
        
        stats = {
            'length': len(text),
            'num_words': len(words),
            'num_chars': len(chars),
            'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'has_punctuation': bool(re.search(r'[^\w\s]', text)),
            'has_numbers': bool(re.search(r'\d', text)),
            'has_uppercase': bool(re.search(r'[A-Z]', text)),
            'has_emojis': TextProcessor.contains_emoji(text),
            'whitespace_ratio': len(re.findall(r'\s', text)) / len(text) if text else 0,
            'alpha_ratio': len(re.findall(r'[a-zA-Z]', text)) / len(text) if text else 0,
            'digit_ratio': len(re.findall(r'\d', text)) / len(text) if text else 0,
            'punct_ratio': len(re.findall(r'[^\w\s]', text)) / len(text) if text else 0
        }
        
        return stats
    
    def _choose_optimal_strategy(self, text_stats: Dict[str, Any]) -> TokenizationStrategy:
        """
        Choose the optimal tokenization strategy based on text characteristics.
        
        Args:
            text_stats: Text statistics
        
        Returns:
            Chosen tokenization strategy
        """
        # Decision rules based on text characteristics
        
        # Very short text - use character level
        if text_stats['length'] < 10:
            return TokenizationStrategy.CHARACTER
        
        # High punctuation or symbols - use character level
        if text_stats['punct_ratio'] > 0.3:
            return TokenizationStrategy.CHARACTER
        
        # Code-like text (high digit ratio) - use subword
        if text_stats['digit_ratio'] > 0.2:
            return TokenizationStrategy.BPE
        
        # Normal text with good word structure - use word level
        if (text_stats['avg_word_length'] > 3 and 
            text_stats['avg_word_length'] < 15 and
            text_stats['alpha_ratio'] > 0.7):
            return TokenizationStrategy.WORD
        
        # Mixed content - use BPE
        return TokenizationStrategy.BPE
    
    def _apply_strategy(self, text: str, strategy: TokenizationStrategy, text_stats: Dict[str, Any]) -> List[str]:
        """
        Apply the chosen tokenization strategy.
        
        Args:
            text: Input text
            strategy: Chosen strategy
            text_stats: Text statistics
        
        Returns:
            List of tokens
        """
        if strategy == TokenizationStrategy.CHARACTER:
            return self._tokenize_character_level(text)
        elif strategy == TokenizationStrategy.WORD:
            return self._tokenize_word_level(text)
        elif strategy == TokenizationStrategy.BPE:
            return self._tokenize_bpe_level(text)
        else:
            # Fallback to character level
            return self._tokenize_character_level(text)
    
    def _tokenize_character_level(self, text: str) -> List[str]:
        """
        Tokenize text at character level.
        
        Args:
            text: Input text
        
        Returns:
            List of character tokens
        """
        chars = list(text)
        tokens = []
        
        for char in chars:
            if char in self.char_vocab:
                tokens.append(char)
            else:
                tokens.append(self.config.unk_token)
        
        return tokens
    
    def _tokenize_word_level(self, text: str) -> List[str]:
        """
        Tokenize text at word level with character fallback.
        
        Args:
            text: Input text
        
        Returns:
            List of word and character tokens
        """
        tokens = []
        i = 0
        
        while i < len(text):
            # Skip whitespace and punctuation by adding them as individual characters
            if text[i].isspace() or not text[i].isalnum():
                if text[i] in self.char_vocab:
                    tokens.append(text[i])
                else:
                    tokens.append(self.config.unk_token)
                i += 1
                continue
            
            # Extract word starting at position i
            word_start = i
            while i < len(text) and text[i].isalnum():
                i += 1
            word = text[word_start:i]
            
            # Check if word is in vocabulary
            if word in self.word_vocab:
                tokens.append(word)
            else:
                # Fall back to character level for unknown words
                char_tokens = self._tokenize_character_level(word)
                tokens.extend(char_tokens)
        
        return tokens
    
    def _tokenize_bpe_level(self, text: str) -> List[str]:
        """
        Tokenize text using BPE-like subword approach.
        
        Args:
            text: Input text
        
        Returns:
            List of subword tokens
        """
        # This is a simplified BPE implementation
        # In a full implementation, we'd use the actual BPE merges
        
        words = TextProcessor.extract_words(text)
        tokens = []
        
        for word in words:
            word_tokens = self._segment_word_subwords(word)
            tokens.extend(word_tokens)
        
        return tokens
    
    def _segment_word_subwords(self, word: str) -> List[str]:
        """
        Segment a word into subword tokens.
        
        Args:
            word: Word to segment
        
        Returns:
            List of subword tokens
        """
        if word in self.word_vocab:
            return [word]
        
        # Greedy segmentation using subword vocabulary
        tokens = []
        i = 0
        
        while i < len(word):
            # Find longest matching subword
            best_match = None
            best_length = 0
            
            for j in range(i + 1, min(i + 10, len(word) + 1)):
                substring = word[i:j]
                if substring in self.subword_vocab:
                    if len(substring) > best_length:
                        best_match = substring
                        best_length = len(substring)
            
            if best_match:
                tokens.append(best_match)
                i += best_length
            else:
                # Fall back to character
                if word[i] in self.char_vocab:
                    tokens.append(word[i])
                else:
                    tokens.append(self.config.unk_token)
                i += 1
        
        return tokens
    
    def _fixed_strategy_tokenize(self, text: str) -> List[str]:
        """
        Tokenize using a fixed combination of strategies.
        
        Args:
            text: Input text
        
        Returns:
            List of tokens
        """
        # Use the primary strategy from config
        primary_strategy = self.strategies[0] if self.strategies else 'bpe'
        
        if primary_strategy == 'character':
            return self._tokenize_character_level(text)
        elif primary_strategy == 'word':
            return self._tokenize_word_level(text)
        elif primary_strategy == 'bpe':
            return self._tokenize_bpe_level(text)
        else:
            return self._tokenize_character_level(text)
    
    def _intelligent_detokenize(self, tokens: List[str]) -> str:
        """
        Intelligently join tokens back to text.
        
        Args:
            tokens: List of tokens
        
        Returns:
            Joined text
        """
        if not tokens:
            return ""
        
        text = ""
        
        for i, token in enumerate(tokens):
            # Skip special tokens
            if token in self.config.special_tokens:
                continue
            
            # Add token
            text += token
            
            # Decide whether to add space
            if i < len(tokens) - 1:
                next_token = tokens[i + 1]
                
                # Don't add space before punctuation
                if next_token in '.,!?;:':
                    continue
                
                # Don't add space if current token is punctuation
                if token in '.,!?;:':
                    text += ' '
                    continue
                
                # Add space between word-like tokens
                if (len(token) > 1 and len(next_token) > 1 and 
                    token.isalnum() and next_token.isalnum()):
                    text += ' '
        
        return text.strip()
    
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
        
        text = TextProcessor.normalize_unicode(text)
        
        if self.adaptive_mode:
            return self._adaptive_tokenize(text)
        else:
            return self._fixed_strategy_tokenize(text)
    
    def get_tokenization_strategy(self, text: str) -> TokenizationStrategy:
        """
        Get the tokenization strategy that would be used for given text.
        
        Args:
            text: Input text
        
        Returns:
            Tokenization strategy
        """
        if not self.adaptive_mode:
            return TokenizationStrategy.BPE  # Default
        
        text_stats = self._analyze_text_characteristics(text)
        return self._choose_optimal_strategy(text_stats)
    
    def get_strategy_distribution(self, texts: List[str]) -> Dict[str, int]:
        """
        Get distribution of strategies across multiple texts.
        
        Args:
            texts: List of texts to analyze
        
        Returns:
            Dictionary with strategy counts
        """
        strategy_counts = {}
        
        for text in texts:
            strategy = self.get_tokenization_strategy(text)
            strategy_name = strategy.value
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
        
        return strategy_counts
    
    def get_tokenization_info(self, text: str) -> Dict[str, Any]:
        """
        Get detailed tokenization information for analysis.
        
        Args:
            text: Input text to analyze
        
        Returns:
            Dictionary with tokenization details
        """
        if not self.is_trained:
            raise ValueError("Tokenizer must be trained before analysis")
        
        text_stats = self._analyze_text_characteristics(text)
        strategy = self.get_tokenization_strategy(text)
        tokens = self.tokenize(text)
        token_ids = self.encode(text)
        
        # Count token types
        char_tokens = sum(1 for t in tokens if len(t) == 1)
        word_tokens = sum(1 for t in tokens if t in self.word_vocab)
        subword_tokens = sum(1 for t in tokens if t in self.subword_vocab)
        unk_tokens = sum(1 for t in tokens if t == self.config.unk_token)
        
        info = {
            "original_text": text,
            "text_stats": text_stats,
            "chosen_strategy": strategy.value,
            "tokens": tokens,
            "token_ids": token_ids,
            "num_tokens": len(tokens),
            "char_tokens": char_tokens,
            "word_tokens": word_tokens,
            "subword_tokens": subword_tokens,
            "unk_tokens": unk_tokens,
            "compression_ratio": len(text) / len(tokens) if tokens else 0,
            "adaptive_mode": self.adaptive_mode,
            "vocab_distribution": {
                "character": len(self.char_vocab),
                "word": len(self.word_vocab),
                "subword": len(self.subword_vocab)
            }
        }
        
        return info