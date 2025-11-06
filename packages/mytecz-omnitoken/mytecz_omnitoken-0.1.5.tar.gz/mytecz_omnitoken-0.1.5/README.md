# MyTecZ OmniToken 🚀

**Universal Tokenizer Framework with Multi-Backend Support**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/mytecz-omnitoken.svg)](https://pypi.org/project/mytecz-omnitoken/)
[![Downloads](https://img.shields.io/pypi/dm/mytecz-omnitoken.svg)](https://pypi.org/project/mytecz-omnitoken/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-98%20passing-brightgreen.svg)](#testing)

## 🎯 Overview

MyTecZ OmniToken is a production-ready universal tokenizer framework that provides a unified interface for multiple tokenization backends. Designed for modern NLP workflows, it offers seamless switching between BPE, WordPiece, SentencePiece, and experimental Hybrid tokenization strategies.

**Perfect for:**
- 🤖 Machine Learning practitioners building NLP models  
- 🔬 Researchers comparing tokenization strategies
- 🏗️ Production systems requiring robust text processing
- 📚 Educational projects exploring tokenization algorithms

### ✨ Key Features

- **🔧 Multi-Backend Support**: BPE, WordPiece, SentencePiece, and Hybrid tokenizers
- **🎯 Unified API**: Single interface across all tokenization methods  
- **🌍 Unicode Ready**: Full support for international text, emojis, and complex scripts
- **🧪 98 Tests Passing**: Comprehensive test suite ensuring reliability
- **📊 Frequency Analysis**: Built-in token and character frequency tracking
- **⚙️ Highly Configurable**: Extensive customization options
- **⚡ Production Optimized**: Efficient training and inference with robust error handling

### 🛠️ Supported Tokenization Methods

| Method | Description | Best For |
|--------|-------------|----------|
| **BPE** | Byte Pair Encoding with merge operations | General-purpose, handling OOV words |
| **WordPiece** | BERT-style with `##` continuation prefixes | Transformer models, subword tokenization |
| **SentencePiece** | Language-independent raw character processing | Multilingual applications, robust Unicode |
| **Hybrid** | Adaptive strategy combining multiple approaches | Mixed content types, experimental research |

## 🚀 Quick Start

### Installation

```bash
pip install mytecz-omnitoken
```

### Basic Usage

```python
from omnitoken import OmniToken

# Create tokenizer with your preferred method
tokenizer = OmniToken(method="wordpiece", vocab_size=1000)

# Train on text data
training_texts = [
    "Hello world! This is sample text.",
    "More training data here.",
    "Tokenization is important for NLP."
]

tokenizer.fit(training_texts)

# Encode text to token IDs
text = "Hello world! 👋 Unicode works perfectly."
token_ids = tokenizer.encode(text)
print(f"Token IDs: {token_ids}")

# Decode back to text  
decoded = tokenizer.decode(token_ids)
print(f"Decoded: {decoded}")

# Get vocabulary and frequencies
vocab = tokenizer.get_vocab()
frequencies = tokenizer.get_token_frequencies()
print(f"Vocabulary size: {len(vocab)}")
```

### Advanced Example

```python
from omnitoken import OmniToken

# Configure tokenizer with custom settings
tokenizer = OmniToken(
    method="bpe",
    vocab_size=2000,
    min_frequency=1,  # Include rare tokens
    special_tokens=["[CUSTOM]", "[SPECIAL]"]
)

# Train with text data
training_texts = [
    "The quick brown fox jumps over the lazy dog.",
    "Artificial intelligence and machine learning.",
    "Natural language processing with tokenization."
]

tokenizer.fit(training_texts)

# Analyze tokenization results
test_text = "Machine learning tokenization example!"
token_ids = tokenizer.encode(test_text)
decoded = tokenizer.decode(token_ids)

print(f"Original: {test_text}")
print(f"Token IDs: {token_ids}")
print(f"Decoded: {decoded}")
print(f"Vocabulary size: {len(tokenizer.get_vocab())}")
```

### Method Comparison

```python
# Compare different tokenization methods on the same text
text = "Hello world! Tokenization comparison."

methods = ["bpe", "wordpiece", "sentencepiece", "hybrid"]
training_data = ["Sample training text", "More training data", "Hello world"]

for method in methods:
    tokenizer = OmniToken(method=method, vocab_size=500, min_frequency=1)
    tokenizer.fit(training_data)
    
    token_ids = tokenizer.encode(text)
    decoded = tokenizer.decode(text)
    vocab_size = len(tokenizer.get_vocab())
    
    print(f"{method}: {len(token_ids)} tokens, vocab={vocab_size}")
```

## 📚 API Reference

### Tokenization Methods

#### BPE (Byte Pair Encoding)
```python
tokenizer = OmniToken(method="bpe", vocab_size=10000)
```
- Learns merge operations for frequent character pairs
- Good for handling out-of-vocabulary words
- Deterministic and efficient

#### WordPiece
```python
tokenizer = OmniToken(method="wordpiece", vocab_size=10000)
```
- BERT-style tokenization with ## continuation prefixes
- Greedy longest-match-first algorithm
- Excellent for transformer models

#### SentencePiece
```python
tokenizer = OmniToken(method="sentencepiece", vocab_size=10000)
```
- Language-independent tokenization
- Treats text as raw character sequence
- Robust Unicode handling

#### Hybrid (Experimental)
```python
tokenizer = OmniToken(method="hybrid", vocab_size=10000)
```
- Combines multiple strategies adaptively
- Analyzes text characteristics to choose optimal approach
- Best for diverse content types

### Input Format Support

#### String Input
```python
tokenizer.fit("Simple string input for training")
```

#### File Input
```python
tokenizer.fit("path/to/textfile.txt")
tokenizer.fit(["file1.txt", "file2.txt", "file3.txt"])
```

#### JSON Input
```python
data = {
    "texts": ["Text 1", "Text 2"],
    "metadata": "Additional content"
}
tokenizer.fit(data)
```

#### Mixed Input
```python
mixed = [
    "Direct string",
    "data/file.txt",
    {"json": "object"},
    ["list", "of", "items"]
]
tokenizer.fit(mixed)
```

## 🧪 Testing

MyTecZ OmniToken includes a comprehensive test suite with 98 passing tests covering all functionality.

### Running Tests

```bash
# Install the package
pip install mytecz-omnitoken

# Clone repository for tests (if contributing)
git clone https://github.com/kalyanakkondapalli/mytecz_omnitoken.git
cd mytecz_omnitoken

# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_basic.py -v          # Basic functionality
python -m pytest tests/test_roundtrip.py -v     # Encode/decode consistency
python -m pytest tests/test_unicode.py -v       # Unicode and multilingual
```

### Test Coverage

Our test suite covers:
- ✅ Round-trip encode/decode accuracy
- ✅ Unicode and emoji handling
- ✅ All input format types
- ✅ Edge cases and error conditions
- ✅ Performance benchmarks
- ✅ Deterministic behavior
- ✅ Cross-method consistency

## ⚙️ Configuration Options

### TokenizerConfig Parameters

```python
from omnitoken import OmniToken
from omnitoken.tokenizer_base import TokenizerConfig

config = TokenizerConfig(
    vocab_size=10000,           # Maximum vocabulary size
    min_frequency=2,            # Minimum token frequency
    special_tokens=["[MASK]"],  # Custom special tokens
    unk_token="[UNK]",         # Unknown token
    pad_token="[PAD]",         # Padding token
    case_sensitive=True,        # Case sensitivity
    max_token_length=100       # Maximum token length
)

tokenizer = OmniToken(method="bpe", config=config)
```

### Method-Specific Options

#### BPE Options
```python
tokenizer = OmniToken(
    method="bpe",
    vocab_size=10000,
    dropout=0.1,                # BPE dropout for regularization
    end_of_word_suffix="</w>"   # End-of-word marker
)
```

#### WordPiece Options
```python
tokenizer = OmniToken(
    method="wordpiece",
    vocab_size=10000,
    continuation_prefix="##",    # Subword continuation prefix
    do_lower_case=True,         # Lowercase normalization
    max_input_chars_per_word=100 # Max characters per word
)
```

#### Hybrid Options
```python
tokenizer = OmniToken(
    method="hybrid",
    vocab_size=10000,
    char_ratio=0.3,             # Character vocab ratio
    word_ratio=0.4,             # Word vocab ratio  
    subword_ratio=0.3,          # Subword vocab ratio
    adaptive_mode=True          # Enable adaptive strategy selection
)
```

## 🔍 Visualization and Analysis

### Token Visualization

```python
from omnitoken.utils import TokenVisualizer

# Visualize tokenization
text = "Example text with emojis 🎯"
tokens = tokenizer._tokenizer.tokenize(text)
token_ids = tokenizer.encode(text)

viz = TokenVisualizer.visualize_tokens(text, tokens, token_ids)
print(viz)
```

### Method Comparison

```python
# Compare different tokenization methods
tokenizations = {
    "BPE": bpe_tokenizer.tokenize(text),
    "WordPiece": wp_tokenizer.tokenize(text),
    "Hybrid": hybrid_tokenizer.tokenize(text)
}

comparison = TokenVisualizer.compare_tokenizations(text, tokenizations)
print(comparison)
```

### Vocabulary Statistics

```python
vocab = tokenizer._tokenizer.get_vocab()
stats = TokenVisualizer.show_vocabulary_stats(vocab)
print(stats)
```

## 🎯 Use Cases

**Natural Language Processing**
- Text preprocessing for transformer models
- Multi-language document processing  
- Social media content analysis

**Code Analysis**
- Programming language tokenization
- Code documentation processing
- Technical text analysis

**Content Processing**
- Web scraping and text extraction
- Document indexing and search
- Content recommendation systems

**Research and Development**
- Tokenization algorithm research
- Comparative analysis studies
- Custom tokenization strategies

## 🏗️ Package Structure

```text
mytecz_omnitoken/
├── omnitoken/
│   ├── __init__.py              # Main OmniToken interface
│   ├── tokenizer_base.py        # Abstract base class
│   ├── tokenizer_bpe.py         # BPE implementation
│   ├── tokenizer_wordpiece.py   # WordPiece implementation  
│   ├── tokenizer_sentencepiece.py # SentencePiece implementation
│   ├── tokenizer_hybrid.py      # Hybrid tokenizer
│   ├── trainer.py               # Training algorithms
│   ├── utils.py                 # Utilities and helpers
│   └── data/                    # Training corpora and test samples
└── tests/                       # Comprehensive test suite
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

- **🐛 Report Issues**: [Open an issue](https://github.com/kalyanakkondapalli/mytecz_omnitoken/issues) for bugs or feature requests
- **📝 Improve Documentation**: Help enhance examples and documentation
- **🧪 Add Tests**: Contribute test cases for edge cases
- **🔧 Submit Code**: Submit pull requests with improvements or fixes

### Development Setup

```bash
# Clone the repository
git clone https://github.com/kalyanakkondapalli/mytecz_omnitoken.git
cd mytecz_omnitoken

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/ -v
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **PyPI Package**: [https://pypi.org/project/mytecz-omnitoken/](https://pypi.org/project/mytecz-omnitoken/)
- **Source Code**: [https://github.com/kalyanakkondapalli/mytecz_omnitoken](https://github.com/kalyanakkondapalli/mytecz_omnitoken)
- **Issues & Support**: [https://github.com/kalyanakkondapalli/mytecz_omnitoken/issues](https://github.com/kalyanakkondapalli/mytecz_omnitoken/issues)

---

**Universal Tokenization Made Simple** 🚀
