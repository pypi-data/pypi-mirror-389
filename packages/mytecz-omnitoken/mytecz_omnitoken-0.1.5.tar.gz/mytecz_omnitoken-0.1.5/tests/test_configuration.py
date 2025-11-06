"""
Configuration and customization tests for MyTecZ OmniToken.

This module tests various configuration options, special tokens,
vocabulary size settings, and tokenizer customization features.
"""

from typing import List

import pytest

from omnitoken import OmniToken
from omnitoken.tokenizer_base import TokenizerConfig


@pytest.fixture
def sample_training_texts() -> List[str]:
    """Sample texts for configuration testing."""
    return [
        "The quick brown fox jumps over the lazy dog.",
        "Pack my box with five dozen liquor jugs.",
        "How vexingly quick daft zebras jump!",
        "Python programming language tutorial.",
        "Machine learning and artificial intelligence.",
        "Natural language processing with deep learning.",
        "Tokenization algorithms and implementations."
    ]


class TestConfigurationOptions:
    """Test various configuration options."""
    
    @pytest.mark.parametrize("vocab_size", [100, 500, 1000, 2000])
    def test_vocab_size_configuration(self, vocab_size: int, sample_training_texts: List[str]):
        """Test vocabulary size configuration."""
        config = TokenizerConfig(vocab_size=vocab_size)
        tokenizer = OmniToken(method="bpe", config=config)
        
        # Use repeated texts for more data
        training_texts = sample_training_texts * 10
        tokenizer.fit(training_texts)
        
        actual_size = tokenizer._tokenizer.get_vocab_size()
        # Actual size might be smaller than requested
        assert actual_size <= vocab_size
        assert actual_size > 0
    
    def test_special_tokens_configuration(self, sample_training_texts: List[str]):
        """Test special tokens configuration."""
        special_tokens = ["[CUSTOM]", "[SPECIAL]", "[TOKEN]"]
        
        config = TokenizerConfig(special_tokens=special_tokens)
        tokenizer = OmniToken(method="bpe", config=config)
        
        # Check that special tokens are included
        for token in special_tokens:
            assert token in tokenizer._tokenizer.config.special_tokens
        
        tokenizer.fit(sample_training_texts)
        
        # Test that special tokens can be encoded
        for token in special_tokens:
            token_ids = tokenizer.encode(token)
            assert isinstance(token_ids, list)
            assert len(token_ids) > 0
    
    def test_min_frequency_configuration(self, sample_training_texts: List[str]):
        """Test minimum frequency configuration."""
        config = TokenizerConfig(min_frequency=5, vocab_size=1000)
        tokenizer = OmniToken(method="bpe", config=config)
        
        # Use repeated text to ensure some tokens meet frequency threshold
        training_texts = sample_training_texts * 20
        
        tokenizer.fit(training_texts)
        assert tokenizer._tokenizer.is_trained
    
    @pytest.mark.parametrize("dropout", [0.0, 0.1, 0.5])
    def test_dropout_configuration(self, dropout: float, sample_training_texts: List[str]):
        """Test dropout configuration for training."""
        config = TokenizerConfig(dropout=dropout, vocab_size=500)
        tokenizer = OmniToken(method="bpe", config=config)
        
        tokenizer.fit(sample_training_texts)
        assert tokenizer._tokenizer.is_trained
        
        # Test that encoding still works with dropout
        result = tokenizer.encode("Test text with dropout")
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_normalization_configuration(self, sample_training_texts: List[str]):
        """Test text normalization configuration."""
        # Test with normalization enabled
        config_norm = TokenizerConfig(normalize_unicode=True, lowercase=True)
        tokenizer_norm = OmniToken(method="bpe", config=config_norm, vocab_size=500)
        
        # Test without normalization
        config_no_norm = TokenizerConfig(normalize_unicode=False, lowercase=False)
        tokenizer_no_norm = OmniToken(method="bpe", config=config_no_norm, vocab_size=500)
        
        for tokenizer in [tokenizer_norm, tokenizer_no_norm]:
            tokenizer.fit(sample_training_texts)
            result = tokenizer.encode("Test Text With Mixed Case")
            assert isinstance(result, list)
            assert len(result) > 0


class TestSpecialTokenHandling:
    """Test special token functionality."""
    
    def test_default_special_tokens(self, sample_training_texts: List[str]):
        """Test default special tokens."""
        tokenizer = OmniToken(method="bpe", vocab_size=500)
        tokenizer.fit(sample_training_texts)
        
        # Default special tokens should be present
        default_tokens = ["[UNK]", "[PAD]", "[BOS]", "[EOS]"]
        
        for token in default_tokens:
            assert token in tokenizer._tokenizer.config.special_tokens
    
    def test_custom_special_tokens(self, sample_training_texts: List[str]):
        """Test custom special tokens."""
        custom_tokens = ["[START]", "[END]", "[MASK]", "[SEP]"]
        config = TokenizerConfig(special_tokens=custom_tokens)
        tokenizer = OmniToken(method="wordpiece", config=config, vocab_size=500)
        
        tokenizer.fit(sample_training_texts)
        
        # Test encoding with special tokens
        text_with_special = "[START] Hello world [MASK] test [END]"
        token_ids = tokenizer.encode(text_with_special)
        decoded = tokenizer.decode(token_ids)
        
        assert isinstance(token_ids, list)
        assert isinstance(decoded, str)
    
    def test_special_token_vocabulary(self, sample_training_texts: List[str]):
        """Test that special tokens are in vocabulary."""
        special_tokens = ["[CLS]", "[SEP]", "[MASK]"]
        config = TokenizerConfig(special_tokens=special_tokens)
        tokenizer = OmniToken(method="bpe", config=config, vocab_size=500)
        
        tokenizer.fit(sample_training_texts)
        vocab = tokenizer._tokenizer.get_vocab()
        
        # Special tokens should be in vocabulary
        for token in special_tokens:
            assert token in vocab
    
    def test_special_token_ids(self, sample_training_texts: List[str]):
        """Test special token ID assignment."""
        special_tokens = ["[PAD]", "[UNK]", "[BOS]", "[EOS]"]
        config = TokenizerConfig(special_tokens=special_tokens)
        tokenizer = OmniToken(method="bpe", config=config, vocab_size=500)
        
        tokenizer.fit(sample_training_texts)
        
        # Special tokens should have consistent IDs
        for token in special_tokens:
            token_ids = tokenizer.encode(token)
            assert len(token_ids) == 1  # Should be single token
            assert isinstance(token_ids[0], int)


class TestMethodComparison:
    """Test different tokenization methods with same configuration."""
    
    @pytest.mark.parametrize("method", ["bpe", "wordpiece", "sentencepiece", "hybrid"])
    def test_method_consistency(self, method: str, sample_training_texts: List[str]):
        """Test that all methods work with same configuration."""
        config = TokenizerConfig(vocab_size=500, min_frequency=2)
        tokenizer = OmniToken(method=method, config=config)
        
        tokenizer.fit(sample_training_texts)
        
        test_text = "This is a consistency test."
        token_ids = tokenizer.encode(test_text)
        decoded = tokenizer.decode(token_ids)
        
        assert isinstance(token_ids, list)
        assert len(token_ids) > 0
        assert isinstance(decoded, str)
        assert len(decoded) > 0
    
    def test_method_comparison_same_input(self, sample_training_texts: List[str]):
        """Compare different methods on same input."""
        test_text = "Compare tokenization methods."
        methods = ["bpe", "wordpiece", "sentencepiece", "hybrid"]
        results = {}
        
        for method in methods:
            tokenizer = OmniToken(method=method, vocab_size=500)
            tokenizer.fit(sample_training_texts)
            
            token_ids = tokenizer.encode(test_text)
            decoded = tokenizer.decode(token_ids)
            
            results[method] = {
                'token_ids': token_ids,
                'decoded': decoded,
                'vocab_size': tokenizer._tokenizer.get_vocab_size()
            }
        
        # All methods should produce valid results
        for method, result in results.items():
            assert isinstance(result['token_ids'], list)
            assert len(result['token_ids']) > 0
            assert isinstance(result['decoded'], str)
            assert result['vocab_size'] > 0


class TestAdvancedConfiguration:
    """Test advanced configuration options."""
    
    def test_byte_level_configuration(self, sample_training_texts: List[str]):
        """Test byte-level processing configuration."""
        config = TokenizerConfig(
            byte_level=True,
            vocab_size=500
        )
        
        # SentencePiece supports byte-level best
        tokenizer = OmniToken(method="sentencepiece", config=config)
        tokenizer.fit(sample_training_texts)
        
        # Test with various inputs including Unicode
        test_texts = [
            "Hello world",
            "Café naïve",
            "🚀 emoji test",
        ]
        
        for text in test_texts:
            token_ids = tokenizer.encode(text)
            decoded = tokenizer.decode(token_ids)
            
            assert isinstance(token_ids, list)
            assert len(token_ids) > 0
            assert isinstance(decoded, str)
    
    def test_end_of_word_configuration(self, sample_training_texts: List[str]):
        """Test end-of-word suffix configuration."""
        config = TokenizerConfig(
            end_of_word_suffix="</w>",
            vocab_size=500
        )
        
        tokenizer = OmniToken(method="bpe", config=config)
        tokenizer.fit(sample_training_texts)
        
        result = tokenizer.encode("Test end of word handling")
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_continuing_subword_prefix(self, sample_training_texts: List[str]):
        """Test continuing subword prefix configuration."""
        config = TokenizerConfig(
            continuing_subword_prefix="##",
            vocab_size=500
        )
        
        tokenizer = OmniToken(method="wordpiece", config=config)
        tokenizer.fit(sample_training_texts)
        
        result = tokenizer.encode("Test subword prefix handling")
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_max_token_length(self, sample_training_texts: List[str]):
        """Test maximum token length configuration."""
        config = TokenizerConfig(
            max_token_length=10,
            vocab_size=500
        )
        
        tokenizer = OmniToken(method="bpe", config=config)
        tokenizer.fit(sample_training_texts)
        
        # Test with long words
        long_text = "supercalifragilisticexpialidocious"
        token_ids = tokenizer.encode(long_text)
        
        assert isinstance(token_ids, list)
        assert len(token_ids) > 0


class TestErrorHandling:
    """Test error handling in configuration."""
    
    def test_invalid_vocab_size(self):
        """Test invalid vocabulary size handling."""
        with pytest.raises(ValueError):
            TokenizerConfig(vocab_size=0)
        
        with pytest.raises(ValueError):
            TokenizerConfig(vocab_size=-100)
    
    def test_invalid_min_frequency(self):
        """Test invalid minimum frequency handling."""
        with pytest.raises(ValueError):
            TokenizerConfig(min_frequency=-1)
    
    def test_invalid_dropout(self):
        """Test invalid dropout value handling."""
        with pytest.raises(ValueError):
            TokenizerConfig(dropout=-0.1)
        
        with pytest.raises(ValueError):
            TokenizerConfig(dropout=1.1)
    
    def test_conflicting_configurations(self):
        """Test handling of conflicting configuration options."""
        # Some configurations might not be compatible
        config = TokenizerConfig(
            byte_level=True,
            normalize_unicode=True,  # Might conflict with byte-level
            vocab_size=500
        )
        
        # Should either work or raise a clear error
        try:
            tokenizer = OmniToken(method="sentencepiece", config=config)
            tokenizer.fit(["test text"])
            assert tokenizer._tokenizer.is_trained
        except ValueError:
            # Acceptable to reject conflicting configurations
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])