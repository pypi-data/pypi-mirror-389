"""
WordPiece Tokenizer for MyTecZ OmniToken.

This module implements a WordPiece tokenizer similar to the one used in BERT,
which uses a greedy longest-match-first approach and ## prefixes for subword tokens.
"""

import re
from typing import List, Dict, Optional, Set
from .tokenizer_base import TokenizerBase, TokenizerConfig
from .trainer import WordPieceTrainer
from .utils import TextProcessor


class WordPieceTokenizer(TokenizerBase):
    """
    WordPiece tokenizer implementation similar to BERT's tokenizer.
    
    WordPiece uses a greedy longest-match-first algorithm to tokenize text,
    with ## prefixes to indicate subword continuation tokens.
    """
    
    def __init__(self, config: Optional[TokenizerConfig] = None, **kwargs):
        """
        Initialize WordPiece tokenizer.
        
        Args:
            config: TokenizerConfig instance
            **kwargs: Additional configuration parameters
        """
        super().__init__(config, **kwargs)
        
        # WordPiece-specific config
        self.continuation_prefix = getattr(self.config, 'continuation_prefix', '##')
        self.max_input_chars_per_word = getattr(self.config, 'max_input_chars_per_word', 100)
        self.do_lower_case = getattr(self.config, 'do_lower_case', True)
        
        # Special WordPiece tokens
        wordpiece_special_tokens = ['[CLS]', '[SEP]', '[MASK]']
        for token in wordpiece_special_tokens:
            if token not in self.config.special_tokens:
                self.config.special_tokens.append(token)
    
    def fit(self, data) -> 'WordPieceTokenizer':
        """
        Train the WordPiece tokenizer on provided data.
        
        Args:
            data: Training data in various formats
        
        Returns:
            Self for method chaining
        """
        # Extract text from various input formats
        texts = self._extract_text_from_input(data)
        
        if not texts:
            raise ValueError("No text data found for training")
        
        # Initialize WordPiece trainer
        trainer = WordPieceTrainer(
            vocab_size=self.config.vocab_size,
            min_frequency=self.config.min_frequency
        )
        
        # Train WordPiece vocabulary
        vocab = trainer.train(texts)

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
        Encode text into token IDs using WordPiece.
        
        Args:
            text: Input text to tokenize
        
        Returns:
            List of token IDs
        """
        if not self.is_trained:
            raise ValueError("Tokenizer must be trained before encoding")
        if text in self.token_to_id:
            return [self.token_to_id[text]]
        
        # Normalize text
        text = TextProcessor.normalize_unicode(text)
        if self.do_lower_case:
            text = text.lower()
        
        # Basic tokenization (split on whitespace and punctuation)
        tokens = self._basic_tokenize(text)
        
        # WordPiece tokenization
        wordpiece_tokens = []
        for token in tokens:
            wordpiece_tokens.extend(self._wordpiece_tokenize(token))
        
        # Convert to IDs
        token_ids = []
        for token in wordpiece_tokens:
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
        
        # Join tokens and handle subword prefixes
        text = self._detokenize_wordpiece(tokens)
        if not text.strip():
            # Fallback reconstruction to avoid empty decode edge case
            rebuilt = []
            for t in tokens:
                if t in self.config.special_tokens:
                    continue
                if t.startswith(self.continuation_prefix):
                    rebuilt.append(t[len(self.continuation_prefix):])
                else:
                    if rebuilt and not rebuilt[-1].endswith(' '):
                        rebuilt.append(' ')
                    rebuilt.append(t)
            text = ''.join(rebuilt).strip()
            if not text and any(t == self.config.unk_token for t in tokens):
                text = self.config.unk_token
        
        return text
    
    def _basic_tokenize(self, text: str) -> List[str]:
        """
        Basic tokenization: split on whitespace and punctuation.
        
        Args:
            text: Input text
        
        Returns:
            List of basic tokens
        """
        # Strip and normalize whitespace
        text = text.strip()
        
        if not text:
            return []
        
        # Split on whitespace
        tokens = text.split()
        
        # Further split on punctuation
        final_tokens = []
        for token in tokens:
            final_tokens.extend(self._split_on_punctuation(token))
        
        return final_tokens
    
    def _split_on_punctuation(self, text: str) -> List[str]:
        """
        Split text on punctuation characters.
        
        Args:
            text: Input text
        
        Returns:
            List of tokens split on punctuation
        """
        chars = list(text)
        tokens = []
        current_token = []
        
        for char in chars:
            if self._is_punctuation(char):
                if current_token:
                    tokens.append(''.join(current_token))
                    current_token = []
                tokens.append(char)
            else:
                current_token.append(char)
        
        if current_token:
            tokens.append(''.join(current_token))
        
        return tokens
    
    def _is_punctuation(self, char: str) -> bool:
        """
        Check if a character is punctuation.
        
        Args:
            char: Character to check
        
        Returns:
            True if punctuation, False otherwise
        """
        cp = ord(char)
        # Characters in these ranges are punctuation
        if ((cp >= 33 and cp <= 47) or (cp >= 58 and cp <= 64) or
            (cp >= 91 and cp <= 96) or (cp >= 123 and cp <= 126)):
            return True
        
        # Unicode categories for punctuation
        import unicodedata
        cat = unicodedata.category(char)
        if cat.startswith("P"):
            return True
        
        return False
    
    def _wordpiece_tokenize(self, word: str) -> List[str]:
        """
        Tokenize a word using WordPiece algorithm.
        
        Args:
            word: Word to tokenize
        
        Returns:
            List of WordPiece tokens
        """
        if len(word) > self.max_input_chars_per_word:
            return [self.config.unk_token]
        
        is_bad = False
        start = 0
        sub_tokens = []
        
        while start < len(word):
            end = len(word)
            cur_substr = None
            
            # Greedy longest-match-first
            while start < end:
                substr = word[start:end]
                if start > 0:
                    substr = self.continuation_prefix + substr
                
                if substr in self.token_to_id:
                    cur_substr = substr
                    break
                end -= 1
            
            if cur_substr is None:
                is_bad = True
                break
            
            sub_tokens.append(cur_substr)
            start = end
        
        if is_bad:
            return [self.config.unk_token]
        else:
            return sub_tokens
    
    def _detokenize_wordpiece(self, tokens: List[str]) -> str:
        """
        Convert WordPiece tokens back to text.
        
        Args:
            tokens: List of WordPiece tokens
        
        Returns:
            Detokenized text
        """
        text = ""
        for i, token in enumerate(tokens):
            # Skip special tokens in basic detokenization
            if token in self.config.special_tokens:
                continue
            
            if token.startswith(self.continuation_prefix):
                # Continuation token - remove prefix and append without space
                text += token[len(self.continuation_prefix):]
            else:
                # Regular token - add space before if not first token
                if text and not text.endswith(' '):
                    text += ' '
                text += token
        
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
        
        # Normalize text
        text = TextProcessor.normalize_unicode(text)
        if self.do_lower_case:
            text = text.lower()
        
        # Basic tokenization
        tokens = self._basic_tokenize(text)
        
        # WordPiece tokenization
        wordpiece_tokens = []
        for token in tokens:
            wordpiece_tokens.extend(self._wordpiece_tokenize(token))
        
        return wordpiece_tokens
    
    def tokenize_with_offsets(self, text: str) -> List[tuple]:
        """
        Tokenize text and return tokens with character offsets.
        
        Args:
            text: Input text to tokenize
        
        Returns:
            List of (token, start_offset, end_offset) tuples
        """
        if not self.is_trained:
            raise ValueError("Tokenizer must be trained before tokenizing")
        
        # This is a simplified implementation
        # A full implementation would track character positions through all transformations
        tokens = self.tokenize(text)
        
        # Reconstruct approximate offsets
        tokens_with_offsets = []
        current_pos = 0
        
        for token in tokens:
            # Skip special tokens for offset calculation
            if token in self.config.special_tokens:
                tokens_with_offsets.append((token, -1, -1))
                continue
            
            # Find token in remaining text
            clean_token = token.replace(self.continuation_prefix, '')
            
            # Find position of this token
            remaining_text = text[current_pos:]
            token_start = remaining_text.find(clean_token)
            
            if token_start != -1:
                start_pos = current_pos + token_start
                end_pos = start_pos + len(clean_token)
                tokens_with_offsets.append((token, start_pos, end_pos))
                current_pos = end_pos
            else:
                # Fallback for tokens that can't be found
                tokens_with_offsets.append((token, -1, -1))
        
        return tokens_with_offsets
    
    def convert_tokens_to_string(self, tokens: List[str]) -> str:
        """
        Convert a list of tokens back to a string.
        
        Args:
            tokens: List of tokens
        
        Returns:
            Converted string
        """
        return self._detokenize_wordpiece(tokens)
    
    def get_special_tokens_mask(self, token_ids: List[int]) -> List[int]:
        """
        Get a mask indicating which tokens are special tokens.
        
        Args:
            token_ids: List of token IDs
        
        Returns:
            List of 1s and 0s (1 for special tokens)
        """
        special_token_ids = {
            self.token_to_id.get(token, -1) 
            for token in self.config.special_tokens
        }
        
        mask = []
        for token_id in token_ids:
            mask.append(1 if token_id in special_token_ids else 0)
        
        return mask
    
    def get_vocab_words(self) -> Set[str]:
        """
        Get all vocabulary words (tokens without ## prefix).
        
        Returns:
            Set of vocabulary words
        """
        words = set()
        for token in self.token_to_id.keys():
            if not token.startswith(self.continuation_prefix) and token not in self.config.special_tokens:
                words.add(token)
        return words
    
    def get_subword_tokens(self) -> Set[str]:
        """
        Get all subword tokens (tokens with ## prefix).
        
        Returns:
            Set of subword tokens
        """
        subwords = set()
        for token in self.token_to_id.keys():
            if token.startswith(self.continuation_prefix):
                subwords.add(token)
        return subwords
    
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
        
        # Count different token types
        regular_tokens = sum(1 for t in tokens if not t.startswith(self.continuation_prefix) and t not in self.config.special_tokens)
        subword_tokens = sum(1 for t in tokens if t.startswith(self.continuation_prefix))
        special_tokens = sum(1 for t in tokens if t in self.config.special_tokens)
        unk_tokens = sum(1 for t in tokens if t == self.config.unk_token)
        
        info = {
            "original_text": text,
            "tokens": tokens,
            "token_ids": token_ids,
            "num_tokens": len(tokens),
            "regular_tokens": regular_tokens,
            "subword_tokens": subword_tokens,
            "special_tokens": special_tokens,
            "unk_tokens": unk_tokens,
            "compression_ratio": len(text) / len(tokens) if tokens else 0,
            "subword_ratio": subword_tokens / len(tokens) if tokens else 0,
            "continuation_prefix": self.continuation_prefix
        }
        
        return info