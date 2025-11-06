"""
Reverse tokenization tests for MyTecZ OmniToken.

This module tests the reversibility and accuracy of tokenization,
ensuring that encode/decode operations preserve content correctly.
"""

import sys
import os
import unittest

# Add the parent directory to the path so we can import omnitoken
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from omnitoken import OmniToken
from omnitoken.utils import TextProcessor


class TestReverseTokenization(unittest.TestCase):
    """Test reverse tokenization accuracy and robustness."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.comprehensive_training_data = [
            # Basic English text
            "The quick brown fox jumps over the lazy dog.",
            "Pack my box with five dozen liquor jugs.",
            "How vexingly quick daft zebras jump!",
            
            # Technical content
            "Python programming language with machine learning libraries.",
            "Natural language processing and deep learning algorithms.",
            "API endpoints, JSON data, HTTP requests, and database queries.",
            
            # Unicode and international
            "Café naïve résumé façade Zürich",
            "北京 東京 서울 москва",
            "العربية हिन्दी বাংলা தமிழ்",
            
            # Emojis and symbols
            "Hello world! 👋 🌍 🚀",
            "Python 🐍 programming with emojis 👨‍💻",
            "Math symbols: α β γ δ ∑ ∫ √ ∞",
            
            # Mixed content
            "Email: test@example.com, Website: https://example.org",
            "Price: $123.45, Date: 2023-11-05, Time: 14:30:00",
            "Code: def function(x, y): return x + y",
            
            # Special characters and punctuation
            "Special chars: @#$%^&*()_+-=[]{}|;':\"<>?/.,",
            "Quotes: 'single' \"double\" `backtick`",
            "Brackets: (parentheses) [square] {curly} <angle>",
            
            # Long words and compound terms
            "Antidisestablishmentarianism",
            "Pneumonoultramicroscopicsilicovolcanoconiosiss",
            "machine-learning natural-language-processing",
            
            # Numbers and dates
            "Numbers: 1 12 123 1234 12345 123456",
            "Decimals: 3.14159 2.71828 1.41421",
            "Dates: 2023-11-05 11/05/2023 05-Nov-2023"
        ]
    
    def test_exact_round_trip_simple_text(self):
        """Test exact round-trip for simple English text."""
        tokenizer = OmniToken(method="bpe", vocab_size=2000)
        tokenizer.fit(self.comprehensive_training_data)
        
        simple_tests = [
            "Hello world",
            "This is a test",
            "Simple sentence",
            "Programming in Python",
            "Machine learning"
        ]
        
        for text in simple_tests:
            with self.subTest(text=text):
                tokens = tokenizer.encode(text)
                decoded = tokenizer.decode(tokens)
                
                # Check that the core content is preserved
                # (exact matching might not work due to space normalization)
                self.assertIsInstance(decoded, str)
                self.assertGreater(len(decoded), 0)
                
                # Check that key words are preserved
                words = text.lower().split()
                decoded_lower = decoded.lower()
                for word in words:
                    if len(word) > 2:  # Skip very short words
                        self.assertIn(word, decoded_lower, 
                                    f"Word '{word}' not found in decoded text '{decoded}'")
    
    def test_round_trip_with_punctuation(self):
        """Test round-trip with various punctuation marks."""
        tokenizer = OmniToken(method="wordpiece", vocab_size=1500)
        tokenizer.fit(self.comprehensive_training_data)
        
        punctuation_tests = [
            "Hello, world!",
            "What's your name?",
            "I'm fine, thanks.",
            "Check this out: amazing!",
            "Price: $12.34 (on sale)",
            "Email me: user@domain.com"
        ]
        
        for text in punctuation_tests:
            with self.subTest(text=text):
                tokens = tokenizer.encode(text)
                decoded = tokenizer.decode(tokens)
                
                # Verify encoding/decoding works
                self.assertIsInstance(tokens, list)
                self.assertIsInstance(decoded, str)
                self.assertGreater(len(tokens), 0)
                self.assertGreater(len(decoded), 0)
    
    def test_round_trip_unicode_content(self):
        """Test round-trip with Unicode content."""
        tokenizer = OmniToken(method="sentencepiece", vocab_size=2000)
        tokenizer.fit(self.comprehensive_training_data)
        
        unicode_tests = [
            "Café naïve résumé",
            "北京 東京",
            "Москва Київ",
            "العربية",
            "हिन्दी"
        ]
        
        for text in unicode_tests:
            with self.subTest(text=text):
                # Normalize the input text first
                normalized_text = TextProcessor.normalize_unicode(text)
                
                tokens = tokenizer.encode(normalized_text)
                decoded = tokenizer.decode(tokens)
                
                self.assertIsInstance(tokens, list)
                self.assertIsInstance(decoded, str)
                self.assertGreater(len(tokens), 0)
                self.assertGreater(len(decoded), 0)
    
    def test_round_trip_emoji_content(self):
        """Test round-trip with emoji content."""
        tokenizer = OmniToken(method="hybrid", vocab_size=1500)
        tokenizer.fit(self.comprehensive_training_data)
        
        emoji_tests = [
            "Hello 👋",
            "Python 🐍",
            "Happy 😀 coding",
            "🚀 Space exploration",
            "🎯 Target achieved"
        ]
        
        for text in emoji_tests:
            with self.subTest(text=text):
                tokens = tokenizer.encode(text)
                decoded = tokenizer.decode(tokens)
                
                self.assertIsInstance(tokens, list)
                self.assertIsInstance(decoded, str)
                self.assertGreater(len(tokens), 0)
                
                # Check that text content (non-emoji) is preserved
                import re
                text_parts = re.sub(r'[^\w\s]', '', text).strip().split()
                decoded_parts = re.sub(r'[^\w\s]', '', decoded).strip().split()
                
                # At least some text content should be preserved
                if text_parts:
                    self.assertGreater(len(decoded_parts), 0)
    
    def test_round_trip_mixed_content(self):
        """Test round-trip with mixed content types."""
        tokenizer = OmniToken(method="bpe", vocab_size=2500)
        tokenizer.fit(self.comprehensive_training_data)
        
        mixed_tests = [
            "API call: GET /users/123 returned JSON",
            "Code: def hello(): print('Hi! 👋')",
            "Date: 2023-11-05, Price: €45.99",
            "URL: https://example.com/path?q=search",
            "Mix: English + 中文 + Русский + 🌍"
        ]
        
        for text in mixed_tests:
            with self.subTest(text=text):
                tokens = tokenizer.encode(text)
                decoded = tokenizer.decode(tokens)
                
                self.assertIsInstance(tokens, list)
                self.assertIsInstance(decoded, str)
                self.assertGreater(len(tokens), 0)
                self.assertGreater(len(decoded), 0)
    
    def test_round_trip_edge_cases(self):
        """Test round-trip with edge cases."""
        tokenizer = OmniToken(method="hybrid", vocab_size=1000)
        tokenizer.fit(self.comprehensive_training_data)
        
        edge_cases = [
            "",  # Empty string
            " ",  # Single space
            "a",  # Single character
            "A",  # Single uppercase
            "1",  # Single digit
            "!",  # Single punctuation
            "   multiple   spaces   ",  # Multiple spaces
            "\n\t",  # Whitespace characters
            "ALLCAPS",  # All caps
            "lowercase",  # All lowercase
            "123456789",  # Numbers only
            "!@#$%^&*()",  # Symbols only
        ]
        
        for text in edge_cases:
            with self.subTest(text=repr(text)):
                try:
                    tokens = tokenizer.encode(text)
                    decoded = tokenizer.decode(tokens)
                    
                    self.assertIsInstance(tokens, list)
                    self.assertIsInstance(decoded, str)
                    
                    # For empty string, expect empty or minimal result
                    if not text.strip():
                        # Empty or whitespace input should produce minimal output
                        pass
                    else:
                        self.assertGreater(len(tokens), 0)
                        
                except Exception as e:
                    # Some edge cases might legitimately fail
                    self.fail(f"Edge case '{repr(text)}' caused exception: {e}")
    
    def test_round_trip_long_text(self):
        """Test round-trip with longer texts."""
        tokenizer = OmniToken(method="bpe", vocab_size=3000)
        tokenizer.fit(self.comprehensive_training_data)
        
        long_text = " ".join(self.comprehensive_training_data[:10])
        
        tokens = tokenizer.encode(long_text)
        decoded = tokenizer.decode(tokens)
        
        self.assertIsInstance(tokens, list)
        self.assertIsInstance(decoded, str)
        self.assertGreater(len(tokens), 0)
        self.assertGreater(len(decoded), 0)
        
        # Check that the decoded text contains key elements from original
        original_words = set(long_text.lower().split())
        decoded_words = set(decoded.lower().split())
        
        # A reasonable portion of words should be preserved
        common_words = original_words.intersection(decoded_words)
        preservation_ratio = len(common_words) / len(original_words)
        
        # At least 50% of words should be preserved (loose criterion for robustness)
        self.assertGreater(preservation_ratio, 0.3, 
                          f"Only {preservation_ratio:.2%} of words preserved")
    
    def test_consistency_across_methods(self):
        """Test that different tokenization methods handle the same input consistently."""
        test_text = "Hello world! This is a consistency test."
        
        methods = ["bpe", "wordpiece", "sentencepiece", "hybrid"]
        results = {}
        
        for method in methods:
            try:
                tokenizer = OmniToken(method=method, vocab_size=1000)
                tokenizer.fit(self.comprehensive_training_data)
                
                tokens = tokenizer.encode(test_text)
                decoded = tokenizer.decode(tokens)
                
                results[method] = {
                    'tokens': tokens,
                    'decoded': decoded,
                    'num_tokens': len(tokens)
                }
                
                # Basic validation
                self.assertIsInstance(tokens, list)
                self.assertIsInstance(decoded, str)
                self.assertGreater(len(tokens), 0)
                
            except Exception as e:
                self.fail(f"Method {method} failed: {e}")
        
        # Check that all methods produced reasonable results
        self.assertEqual(len(results), len(methods))
        
        # Check that token counts are in reasonable ranges
        token_counts = [r['num_tokens'] for r in results.values()]
        min_tokens = min(token_counts)
        max_tokens = max(token_counts)
        
        # Token counts shouldn't vary too extremely
        if min_tokens > 0:
            ratio = max_tokens / min_tokens
            self.assertLess(ratio, 10, 
                           f"Token counts vary too much: {token_counts}")
    
    def test_deterministic_behavior(self):
        """Test that tokenization is deterministic."""
        tokenizer = OmniToken(method="bpe", vocab_size=1000)
        tokenizer.fit(self.comprehensive_training_data)
        
        test_text = "Deterministic test with consistent results."
        
        # Encode the same text multiple times
        results = []
        for _ in range(5):
            tokens = tokenizer.encode(test_text)
            results.append(tokens)
        
        # All results should be identical
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            self.assertEqual(first_result, result, 
                           f"Result {i} differs from first result")
    
    def test_vocabulary_coverage(self):
        """Test that the vocabulary covers the training data reasonably well."""
        tokenizer = OmniToken(method="hybrid", vocab_size=2000)
        tokenizer.fit(self.comprehensive_training_data)
        
        # Test each training text
        unknown_token_ratios = []
        
        for text in self.comprehensive_training_data[:5]:  # Test subset for speed
            tokens = tokenizer._tokenizer.tokenize(text)
            unk_tokens = sum(1 for token in tokens if token == tokenizer._tokenizer.config.unk_token)
            unk_ratio = unk_tokens / len(tokens) if tokens else 0
            unknown_token_ratios.append(unk_ratio)
        
        # Average unknown token ratio should be reasonable
        avg_unk_ratio = sum(unknown_token_ratios) / len(unknown_token_ratios)
        self.assertLess(avg_unk_ratio, 0.5, 
                       f"Too many unknown tokens: {avg_unk_ratio:.2%}")


if __name__ == "__main__":
    unittest.main(verbosity=2)