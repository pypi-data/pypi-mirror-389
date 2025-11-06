"""
Unicode and internationalization tests for MyTecZ OmniToken.

This module tests Unicode handling, emoji support, normalization,
and internationalization features of the tokenizer.
"""

import pytest
from typing import List

from omnitoken import OmniToken
from omnitoken.utils import TextProcessor


@pytest.fixture
def unicode_texts() -> List[str]:
    """Sample texts with Unicode content."""
    return [
        "Hello world! Bonjour le monde!",
        "Café naïve résumé façade",
        "北京 東京 서울 москва",
        "العربية हिन्दी বাংলা தமிழ்",
        "Ελληνικά Български Română",
        "🚀 🌟 💡 🎯 🎨 🔥",
        "😀 😃 😄 😁 😆 😅",
        "Python 🐍 programming with emojis 👨‍💻"
    ]


class TestUnicodeSupport:
    """Test Unicode and emoji support."""
    
    def test_unicode_training(self, unicode_texts: List[str]):
        """Test training with Unicode content."""
        tokenizer = OmniToken(method="bpe", vocab_size=1000)
        
        # Should not raise exceptions
        tokenizer.fit(unicode_texts)
        assert tokenizer._tokenizer.is_trained
    
    def test_emoji_tokenization(self, unicode_texts: List[str]):
        """Test emoji tokenization."""
        tokenizer = OmniToken(method="sentencepiece", vocab_size=1000)
        tokenizer.fit(unicode_texts)
        
        emoji_text = "Hello 👋 world 🌍!"
        tokens = tokenizer._tokenizer.tokenize(emoji_text)
        
        assert isinstance(tokens, list)
        assert len(tokens) > 0
    
    def test_mixed_unicode_content(self, unicode_texts: List[str]):
        """Test mixed Unicode content."""
        tokenizer = OmniToken(method="hybrid", vocab_size=1500)
        tokenizer.fit(unicode_texts)
        
        mixed_text = "Café 🇫🇷 Coffee ☕ 咖啡 कॉफी"
        token_ids = tokenizer.encode(mixed_text)
        decoded = tokenizer.decode(token_ids)
        
        assert isinstance(token_ids, list)
        assert isinstance(decoded, str)
        assert len(token_ids) > 0
        assert len(decoded) > 0
    
    def test_unicode_normalization(self):
        """Test Unicode normalization."""
        # Test different Unicode representations
        text1 = "café"  # Composed form
        text2 = "cafe\u0301"  # Decomposed form (e + combining acute)
        
        normalized1 = TextProcessor.normalize_unicode(text1)
        normalized2 = TextProcessor.normalize_unicode(text2)
        
        # Both should normalize to the same form
        assert normalized1 == normalized2
    
    @pytest.mark.parametrize("text,expected_chars", [
        ("🚀", ["🚀"]),
        ("👨‍💻", ["👨‍💻"]),  # Compound emoji
        ("🇺🇸", ["🇺🇸"]),    # Flag emoji
        ("café", ["c", "a", "f", "é"]),
        ("北京", ["北", "京"]),
    ])
    def test_character_extraction(self, text: str, expected_chars: List[str]):
        """Test character extraction from Unicode text."""
        chars = TextProcessor.extract_characters(text)
        assert len(chars) == len(expected_chars)
        assert chars == expected_chars


class TestInternationalization:
    """Test internationalization features."""
    
    @pytest.fixture
    def multilingual_texts(self) -> List[str]:
        """Multilingual training texts."""
        return [
            # English
            "The quick brown fox jumps over the lazy dog.",
            # French
            "Le renard brun et rapide saute par-dessus le chien paresseux.",
            # German
            "Der schnelle braune Fuchs springt über den faulen Hund.",
            # Spanish
            "El rápido zorro marrón salta sobre el perro perezoso.",
            # Chinese
            "敏捷的棕色狐狸跳过懒狗。",
            # Japanese
            "素早い茶色のキツネが怠け者の犬を飛び越えます。",
            # Arabic
            "الثعلب البني السريع يقفز فوق الكلب الكسول.",
            # Russian
            "Быстрая коричневая лиса прыгает через ленивую собаку.",
        ]
    
    def test_multilingual_training(self, multilingual_texts: List[str]):
        """Test training with multilingual content."""
        tokenizer = OmniToken(method="sentencepiece", vocab_size=2000)
        tokenizer.fit(multilingual_texts)
        
        assert tokenizer._tokenizer.is_trained
        assert tokenizer._tokenizer.get_vocab_size() > 0
    
    @pytest.mark.parametrize("method", ["bpe", "wordpiece", "sentencepiece", "hybrid"])
    def test_multilingual_tokenization(self, method: str, multilingual_texts: List[str]):
        """Test tokenization of multilingual content."""
        tokenizer = OmniToken(method=method, vocab_size=1500, min_frequency=1)
        tokenizer.fit(multilingual_texts)
        
        test_texts = [
            "Hello world",      # English
            "Bonjour monde",    # French
            "Hola mundo",       # Spanish
            "你好世界",          # Chinese
            "こんにちは世界",    # Japanese
        ]
        
        for text in test_texts:
            token_ids = tokenizer.encode(text)
            decoded = tokenizer.decode(token_ids)
            
            assert isinstance(token_ids, list)
            assert len(token_ids) > 0
            assert isinstance(decoded, str)
            assert len(decoded) > 0
    
    def test_rtl_language_support(self):
        """Test right-to-left language support."""
        rtl_texts = [
            "السلام عليكم",  # Arabic greeting
            "שלום עליכם",    # Hebrew greeting
            "مرحبا بالعالم",  # Arabic "Hello world"
            "שלום עולם",     # Hebrew "Hello world"
        ]
        
        tokenizer = OmniToken(method="sentencepiece", vocab_size=1000)
        tokenizer.fit(rtl_texts)
        
        for text in rtl_texts:
            token_ids = tokenizer.encode(text)
            decoded = tokenizer.decode(token_ids)
            
            assert isinstance(token_ids, list)
            assert len(token_ids) > 0
            assert isinstance(decoded, str)


class TestSpecialCharacters:
    """Test handling of special characters and symbols."""
    
    @pytest.fixture
    def special_char_texts(self) -> List[str]:
        """Texts with special characters."""
        return [
            "Price: $29.99 (USD)",
            "Email: test@example.com",
            "URL: https://www.example.org/path?param=value",
            "Math: x² + y² = z²",
            "Code: print('Hello, world!')",
            "Punctuation: !@#$%^&*()_+-={}[]|\\:;\"'<>?,./'",
            "Symbols: ™ © ® ± ∞ ≈ ≠ ≤ ≥ π α β γ δ",
        ]
    
    def test_special_character_training(self, special_char_texts: List[str]):
        """Test training with special characters."""
        tokenizer = OmniToken(method="bpe", vocab_size=1000)
        tokenizer.fit(special_char_texts)
        
        assert tokenizer._tokenizer.is_trained
    
    def test_url_tokenization(self, special_char_texts: List[str]):
        """Test URL tokenization."""
        tokenizer = OmniToken(method="sentencepiece", vocab_size=1000)
        tokenizer.fit(special_char_texts)
        
        url = "https://www.example.com/path/to/resource?param=value&other=123"
        token_ids = tokenizer.encode(url)
        decoded = tokenizer.decode(token_ids)
        
        assert isinstance(token_ids, list)
        assert len(token_ids) > 0
        assert isinstance(decoded, str)
        # URL structure should be preserved in some form
        assert "http" in decoded or "www" in decoded or "example" in decoded
    
    def test_code_tokenization(self, special_char_texts: List[str]):
        """Test code snippet tokenization."""
        tokenizer = OmniToken(method="hybrid", vocab_size=1500)
        tokenizer.fit(special_char_texts)
        
        code = "def hello_world():\n    print('Hello, world!')\n    return True"
        token_ids = tokenizer.encode(code)
        decoded = tokenizer.decode(token_ids)
        
        assert isinstance(token_ids, list)
        assert len(token_ids) > 0
        assert isinstance(decoded, str)
        # Some programming keywords should be preserved
        assert any(keyword in decoded for keyword in ["def", "print", "return"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])