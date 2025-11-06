import pytest
from omnitoken import OmniToken


def test_bpe_frequency_api_basic():
    data = [
        "Hello world!",
        "Hello tokenization world.",
        "Tokenization counts tokens in the world"
    ]
    tok = OmniToken(method="bpe", vocab_size=200)
    tok.fit(data)
    vocab = tok.get_vocab()
    freqs = tok.get_token_frequencies()
    assert isinstance(vocab, dict) and vocab, "Vocabulary should be non-empty dict"
    assert isinstance(freqs, dict), "Frequencies should be dict"
    # Frequencies should refer only to tokens in vocab
    assert set(freqs.keys()).issubset(vocab.keys())
    # Some token frequency counts should be > 1
    assert any(v > 1 for v in freqs.values())


def test_mode_alias_wordpiece():
    data = ["Alias mode param works correctly"]
    tok = OmniToken(mode="wordpiece", vocab_size=150)
    tok.fit(data)
    # Ensure encode works
    ids = tok.encode("mode alias test")
    assert isinstance(ids, list) and ids, "Encoded IDs should be non-empty"
    # Frequencies present after training
    assert tok.get_token_frequencies(), "Frequencies should be populated"


def test_frequency_api_access_before_training():
    tok = OmniToken(method="hybrid")
    # Access before training should be safe and empty
    assert tok.get_token_frequencies() == {}
    tok.fit(["Hybrid tokenizer frequency tracking test"])
    assert tok.get_token_frequencies(), "Frequencies should populate after fit"
