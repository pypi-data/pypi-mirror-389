"""
Trainer module for MyTecZ OmniToken.

This module provides training algorithms for different tokenization strategies
including BPE, WordPiece, and hybrid approaches.
"""

from typing import List, Dict, Tuple, Set, Counter as CounterType
from collections import Counter, defaultdict
import re
import heapq
from .utils import FrequencyAnalyzer, TextProcessor


class BPETrainer:
    """Trainer for Byte Pair Encoding (BPE) tokenization."""
    
    def __init__(self, vocab_size: int = 10000, min_frequency: int = 2):
        """
        Initialize BPE trainer.
        
        Args:
            vocab_size: Target vocabulary size
            min_frequency: Minimum frequency for pairs to be merged
        """
        self.vocab_size = vocab_size
        self.min_frequency = min_frequency
    
    def train(self, texts: List[str]) -> Tuple[Dict[str, int], List[Tuple[str, str]]]:
        """
        Train BPE on the provided texts.
        
        Args:
            texts: List of training texts
        
        Returns:
            Tuple of (vocabulary, merge_operations)
        """
        # Initialize with character-level vocabulary
        word_freq = self._get_word_frequencies(texts)
        vocab = self._initialize_vocab(word_freq)
        
        # Perform BPE merges
        merges = []
        current_vocab_size = len(vocab)
        
        while current_vocab_size < self.vocab_size:
            # Find the most frequent pair
            pairs = self._get_stats(word_freq)
            if not pairs:
                break
            
            best_pair = max(pairs, key=pairs.get)
            if pairs[best_pair] < self.min_frequency:
                break
            
            # Merge the best pair
            word_freq = self._merge_vocab(best_pair, word_freq)
            merges.append(best_pair)
            
            # Add new token to vocabulary
            new_token = ''.join(best_pair)
            vocab[new_token] = current_vocab_size
            current_vocab_size += 1
        
        return vocab, merges
    
    def _get_word_frequencies(self, texts: List[str]) -> Dict[str, int]:
        """Get word frequencies with end-of-word markers."""
        word_freq = Counter()
        
        for text in texts:
            words = TextProcessor.extract_words(text)
            for word in words:
                # Add end-of-word marker
                word_with_eow = word + '</w>'
                word_freq[word_with_eow] += 1
        
        return dict(word_freq)
    
    def _initialize_vocab(self, word_freq: Dict[str, int]) -> Dict[str, int]:
        """Initialize vocabulary with individual characters."""
        chars = set()
        for word in word_freq:
            chars.update(word)
        
        vocab = {}
        for i, char in enumerate(sorted(chars)):
            vocab[char] = i
        
        return vocab
    
    def _get_stats(self, word_freq: Dict[str, int]) -> Counter:
        """Get statistics of adjacent symbol pairs."""
        pairs = Counter()
        
        for word, freq in word_freq.items():
            symbols = word.split()
            for i in range(len(symbols) - 1):
                pairs[(symbols[i], symbols[i + 1])] += freq
        
        return pairs
    
    def _merge_vocab(self, pair: Tuple[str, str], word_freq: Dict[str, int]) -> Dict[str, int]:
        """Merge a pair in the vocabulary."""
        new_word_freq = {}
        bigram = re.escape(' '.join(pair))
        p = re.compile(r'(?<!\S)' + bigram + r'(?!\S)')
        
        for word in word_freq:
            new_word = p.sub(''.join(pair), word)
            new_word_freq[new_word] = word_freq[word]
        
        return new_word_freq


class WordPieceTrainer:
    """Trainer for WordPiece tokenization (similar to BERT)."""
    
    def __init__(self, vocab_size: int = 10000, min_frequency: int = 2):
        """
        Initialize WordPiece trainer.
        
        Args:
            vocab_size: Target vocabulary size
            min_frequency: Minimum frequency for subwords
        """
        self.vocab_size = vocab_size
        self.min_frequency = min_frequency
    
    def train(self, texts: List[str]) -> Dict[str, int]:
        """
        Train WordPiece vocabulary.
        
        Args:
            texts: List of training texts
        
        Returns:
            WordPiece vocabulary
        """
        # Get word frequencies
        word_freq = FrequencyAnalyzer.analyze_word_frequency(texts)
        
        # Initialize with characters
        vocab = set()
        for word in word_freq:
            vocab.update(word.lower())
        
        # Add special tokens
        vocab.update(['[UNK]', '[PAD]', '[CLS]', '[SEP]'])
        
        # Generate subwords
        subwords = self._generate_subwords(word_freq, vocab)
        
        # Select best subwords by frequency and likelihood
        final_vocab = self._select_vocabulary(subwords, self.vocab_size)
        
        # Convert to ID mapping
        vocab_dict = {}
        for i, token in enumerate(sorted(final_vocab)):
            vocab_dict[token] = i
        
        return vocab_dict
    
    def _generate_subwords(self, word_freq: CounterType, initial_vocab: Set[str]) -> Counter:
        """Generate all possible subwords from the corpus."""
        subwords = Counter()
        
        # Add initial characters
        for char in initial_vocab:
            subwords[char] = 1
        
        # Add full words first (both original case and lowercase)
        for word, freq in word_freq.items():
            # Add original case
            subwords[word] += freq
            # Add lowercase version if different
            word_lower = word.lower()
            if word_lower != word:
                subwords[word_lower] += freq
        
        # Generate subwords of length 2 to 10
        for word, freq in word_freq.items():
            word = word.lower()
            for length in range(2, min(len(word) + 1, 11)):
                for start in range(len(word) - length + 1):
                    subword = word[start:start + length]
                    # Add ## prefix for continuation pieces
                    if start > 0:
                        subword = '##' + subword
                    # Skip if this is the full word (already added above)
                    elif length == len(word):
                        continue
                    subwords[subword] += freq
        
        return subwords
    
    def _select_vocabulary(self, subwords: Counter, vocab_size: int) -> Set[str]:
        """Select the best vocabulary based on frequency and likelihood."""
        # Filter by minimum frequency
        filtered_subwords = {
            word: freq for word, freq in subwords.items()
            if freq >= self.min_frequency
        }
        
        # Sort by frequency and take top vocab_size
        sorted_subwords = sorted(
            filtered_subwords.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        selected_vocab = set()
        for word, _ in sorted_subwords[:vocab_size]:
            selected_vocab.add(word)
        
        return selected_vocab


class SentencePieceTrainer:
    """Trainer for SentencePiece-like tokenization."""
    
    def __init__(self, vocab_size: int = 10000, character_coverage: float = 0.9995):
        """
        Initialize SentencePiece trainer.
        
        Args:
            vocab_size: Target vocabulary size
            character_coverage: Character coverage for vocabulary
        """
        self.vocab_size = vocab_size
        self.character_coverage = character_coverage
    
    def train(self, texts: List[str]) -> Dict[str, int]:
        """
        Train SentencePiece vocabulary using character-based approach.
        
        Args:
            texts: List of training texts
        
        Returns:
            SentencePiece vocabulary
        """
        # Analyze character frequencies
        char_freq = FrequencyAnalyzer.analyze_character_frequency(texts)
        
        # Select characters by coverage
        total_chars = sum(char_freq.values())
        target_coverage = int(total_chars * self.character_coverage)
        
        selected_chars = []
        current_coverage = 0
        
        for char, freq in char_freq.most_common():
            selected_chars.append(char)
            current_coverage += freq
            if current_coverage >= target_coverage:
                break
        
        # Initialize vocabulary with selected characters
        vocab = set(selected_chars)
        
        # Add special tokens
        vocab.update(['<unk>', '<s>', '</s>', '<pad>'])
        
        # Generate byte-level pieces for remaining capacity
        if len(vocab) < self.vocab_size:
            byte_pieces = self._generate_byte_pieces(texts, vocab)
            remaining_capacity = self.vocab_size - len(vocab)
            vocab.update(list(byte_pieces)[:remaining_capacity])
        
        # Convert to ID mapping
        vocab_dict = {}
        for i, token in enumerate(sorted(vocab)):
            vocab_dict[token] = i
        
        return vocab_dict
    
    def _generate_byte_pieces(self, texts: List[str], existing_vocab: Set[str]) -> List[str]:
        """Generate byte-level pieces for characters not in existing vocabulary."""
        byte_pieces = []
        
        for text in texts:
            for char in text:
                if char not in existing_vocab:
                    # Convert to byte representation
                    byte_repr = char.encode('utf-8')
                    for byte_val in byte_repr:
                        byte_piece = f"<{byte_val:02X}>"
                        if byte_piece not in byte_pieces:
                            byte_pieces.append(byte_piece)
        
        return byte_pieces


class HybridTrainer:
    """Trainer for hybrid tokenization combining multiple approaches."""
    
    def __init__(
        self,
        vocab_size: int = 10000,
        char_ratio: float = 0.3,
        word_ratio: float = 0.4,
        subword_ratio: float = 0.3
    ):
        """
        Initialize hybrid trainer.
        
        Args:
            vocab_size: Target vocabulary size
            char_ratio: Proportion of vocabulary for character-level tokens
            word_ratio: Proportion of vocabulary for word-level tokens
            subword_ratio: Proportion of vocabulary for subword-level tokens
        """
        self.vocab_size = vocab_size
        self.char_ratio = char_ratio
        self.word_ratio = word_ratio
        self.subword_ratio = subword_ratio
        
        # Ensure ratios sum to 1
        total_ratio = char_ratio + word_ratio + subword_ratio
        self.char_ratio /= total_ratio
        self.word_ratio /= total_ratio
        self.subword_ratio /= total_ratio
    
    def train(self, texts: List[str]) -> Dict[str, int]:
        """
        Train hybrid vocabulary.
        
        Args:
            texts: List of training texts
        
        Returns:
            Hybrid vocabulary
        """
        vocab = set()
        
        # Character-level tokens
        char_vocab_size = int(self.vocab_size * self.char_ratio)
        char_freq = FrequencyAnalyzer.analyze_character_frequency(texts)
        char_tokens = [char for char, _ in char_freq.most_common(char_vocab_size)]
        vocab.update(char_tokens)
        
        # Word-level tokens
        word_vocab_size = int(self.vocab_size * self.word_ratio)
        word_freq = FrequencyAnalyzer.analyze_word_frequency(texts)
        word_tokens = [word for word, _ in word_freq.most_common(word_vocab_size)]
        vocab.update(word_tokens)
        
        # Subword-level tokens (BPE-style)
        subword_vocab_size = self.vocab_size - len(vocab)
        if subword_vocab_size > 0:
            bpe_trainer = BPETrainer(vocab_size=subword_vocab_size)
            bpe_vocab, _ = bpe_trainer.train(texts)
            vocab.update(bpe_vocab.keys())
        
        # Add special tokens
        special_tokens = ['[UNK]', '[PAD]', '[BOS]', '[EOS]']
        vocab.update(special_tokens)
        
        # Convert to ID mapping
        vocab_dict = {}
        for i, token in enumerate(sorted(vocab)):
            vocab_dict[token] = i
        
        return vocab_dict


class Trainer:
    """Main trainer class that orchestrates different training strategies."""
    
    def __init__(self, method: str = "bpe", **kwargs):
        """
        Initialize trainer with specified method.
        
        Args:
            method: Training method ("bpe", "wordpiece", "sentencepiece", "hybrid")
            **kwargs: Additional configuration parameters
        """
        self.method = method
        self.config = kwargs
        
        # Initialize the appropriate trainer
        if method == "bpe":
            self.trainer = BPETrainer(**kwargs)
        elif method == "wordpiece":
            self.trainer = WordPieceTrainer(**kwargs)
        elif method == "sentencepiece":
            self.trainer = SentencePieceTrainer(**kwargs)
        elif method == "hybrid":
            self.trainer = HybridTrainer(**kwargs)
        else:
            raise ValueError(f"Unknown training method: {method}")
    
    def train(self, texts: List[str]) -> Dict[str, int]:
        """
        Train vocabulary using the specified method.
        
        Args:
            texts: List of training texts
        
        Returns:
            Trained vocabulary mapping
        """
        if self.method == "bpe":
            vocab, _ = self.trainer.train(texts)
            return vocab
        else:
            return self.trainer.train(texts)
    
    def get_training_stats(self, texts: List[str]) -> Dict[str, any]:
        """
        Get training statistics for the provided texts.
        
        Args:
            texts: List of texts to analyze
        
        Returns:
            Dictionary with training statistics
        """
        total_chars = sum(len(text) for text in texts)
        total_words = sum(len(TextProcessor.extract_words(text)) for text in texts)
        
        char_freq = FrequencyAnalyzer.analyze_character_frequency(texts)
        word_freq = FrequencyAnalyzer.analyze_word_frequency(texts)
        
        stats = {
            "total_texts": len(texts),
            "total_characters": total_chars,
            "total_words": total_words,
            "unique_characters": len(char_freq),
            "unique_words": len(word_freq),
            "avg_chars_per_text": total_chars / len(texts) if texts else 0,
            "avg_words_per_text": total_words / len(texts) if texts else 0,
            "most_common_chars": char_freq.most_common(10),
            "most_common_words": word_freq.most_common(10),
            "training_method": self.method
        }
        
        return stats