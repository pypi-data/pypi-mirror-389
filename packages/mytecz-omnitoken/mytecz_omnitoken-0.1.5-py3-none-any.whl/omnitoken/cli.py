"""
Command-line interface for MyTecZ OmniToken.

This module provides a CLI for the universal tokenizer, supporting
text tokenization from stdin, files, or command arguments.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Union

from . import OmniToken, __version__
from .utils import TokenVisualizer


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="omnitoken",
        description="Universal tokenizer with modular architecture",
        epilog="Example: echo 'Hello world 👋' | omnitoken --method hybrid"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "text",
        nargs="?",
        help="Text to tokenize (if not provided, reads from stdin)"
    )
    input_group.add_argument(
        "--file", "-f",
        type=Path,
        help="File to tokenize"
    )
    input_group.add_argument(
        "--files",
        nargs="+",
        type=Path,
        help="Multiple files to tokenize"
    )
    
    # Tokenizer configuration
    parser.add_argument(
        "--method", "-m",
        choices=["bpe", "wordpiece", "sentencepiece", "hybrid"],
        default="hybrid",
        help="Tokenization method (default: hybrid)"
    )
    
    parser.add_argument(
        "--vocab-size", "-v",
        type=int,
        default=10000,
        help="Vocabulary size (default: 10000)"
    )
    
    parser.add_argument(
        "--min-frequency",
        type=int,
        default=2,
        help="Minimum token frequency (default: 2)"
    )
    
    # Training data options
    parser.add_argument(
        "--train-file",
        type=Path,
        help="Training data file"
    )
    
    parser.add_argument(
        "--train-files",
        nargs="+",
        type=Path,
        help="Multiple training data files"
    )
    
    parser.add_argument(
        "--train-text",
        nargs="+",
        help="Training text strings"
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        choices=["tokens", "ids", "both", "json", "visualize"],
        default="tokens",
        help="Output format (default: tokens)"
    )
    
    parser.add_argument(
        "--decode",
        action="store_true",
        help="Decode token IDs instead of encoding text"
    )
    
    parser.add_argument(
        "--round-trip",
        action="store_true",
        help="Test round-trip encoding/decoding"
    )
    
    # Model persistence
    parser.add_argument(
        "--save-model",
        type=Path,
        help="Save trained model to file"
    )
    
    parser.add_argument(
        "--load-model",
        type=Path,
        help="Load pre-trained model from file"
    )
    
    # Utility options
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress informational output"
    )
    
    parser.add_argument(
        "--verbose", "-V",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser


def get_training_data(args: argparse.Namespace) -> Optional[List[Union[str, Path]]]:
    """Get training data from command-line arguments."""
    training_data = []
    
    if args.train_file:
        training_data.append(args.train_file)
    
    if args.train_files:
        training_data.extend(args.train_files)
    
    if args.train_text:
        training_data.extend(args.train_text)
    
    return training_data if training_data else None


def get_input_text(args: argparse.Namespace) -> str:
    """Get input text from various sources."""
    if args.text:
        return args.text
    elif args.file:
        return args.file.read_text(encoding='utf-8')
    elif args.files:
        texts = []
        for file_path in args.files:
            texts.append(file_path.read_text(encoding='utf-8'))
        return "\n".join(texts)
    else:
        # Read from stdin
        if sys.stdin.isatty():
            print("Enter text to tokenize (Ctrl+D/Ctrl+Z to end):", file=sys.stderr)
        return sys.stdin.read().strip()


def create_tokenizer(args: argparse.Namespace) -> OmniToken:
    """Create and configure the tokenizer."""
    if args.load_model:
        # Load pre-trained model
        tokenizer = OmniToken(method=args.method)
        tokenizer._tokenizer.load_model(str(args.load_model))
        if not args.quiet:
            print(f"Loaded model from {args.load_model}", file=sys.stderr)
        return tokenizer
    
    # Create new tokenizer
    tokenizer = OmniToken(
        method=args.method,
        vocab_size=args.vocab_size,
        min_frequency=args.min_frequency
    )
    
    # Get training data
    training_data = get_training_data(args)
    
    if training_data:
        if not args.quiet:
            print(f"Training {args.method} tokenizer with {len(training_data)} sources...", file=sys.stderr)
        tokenizer.fit(training_data)
        if not args.quiet:
            vocab_size = tokenizer._tokenizer.get_vocab_size()
            print(f"Training completed! Vocabulary size: {vocab_size}", file=sys.stderr)
    else:
        # Use default training data if none provided
        default_training = [
            "Hello world! This is sample text.",
            "The quick brown fox jumps over the lazy dog.",
            "Python programming language with Unicode support.",
            "Natural language processing and machine learning.",
            "Emojis and international text: 🚀 café 北京 العربية"
        ]
        if not args.quiet:
            print("No training data provided, using default samples...", file=sys.stderr)
        tokenizer.fit(default_training)
    
    # Save model if requested
    if args.save_model:
        tokenizer._tokenizer.save_model(str(args.save_model))
        if not args.quiet:
            print(f"Model saved to {args.save_model}", file=sys.stderr)
    
    return tokenizer


def process_text(tokenizer: OmniToken, text: str, args: argparse.Namespace) -> None:
    """Process input text and produce output."""
    if args.decode:
        # Decode token IDs
        try:
            token_ids = json.loads(text)
            if not isinstance(token_ids, list):
                raise ValueError("Input must be a list of token IDs for decoding")
            
            decoded_text = tokenizer.decode(token_ids)
            print(decoded_text)
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    else:
        # Encode text
        if args.round_trip:
            # Test round-trip encoding/decoding
            tokens = tokenizer.encode(text)
            decoded = tokenizer.decode(tokens)
            
            print("=== ROUND-TRIP TEST ===")
            print(f"Original:  {text}")
            print(f"Tokens:    {tokens}")
            print(f"Decoded:   {decoded}")
            print(f"Success:   {'✅' if text.strip() == decoded.strip() else '❌'}")
            
        elif args.output == "tokens":
            tokens = tokenizer._tokenizer.tokenize(text)
            for token in tokens:
                print(token)
        
        elif args.output == "ids":
            token_ids = tokenizer.encode(text)
            for token_id in token_ids:
                print(token_id)
        
        elif args.output == "both":
            tokens = tokenizer._tokenizer.tokenize(text)
            token_ids = tokenizer.encode(text)
            
            for token, token_id in zip(tokens, token_ids):
                print(f"{token_id}\t{token}")
        
        elif args.output == "json":
            tokens = tokenizer._tokenizer.tokenize(text)
            token_ids = tokenizer.encode(text)
            
            result = {
                "text": text,
                "tokens": tokens,
                "token_ids": token_ids,
                "method": args.method,
                "vocab_size": tokenizer._tokenizer.get_vocab_size()
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        elif args.output == "visualize":
            tokens = tokenizer._tokenizer.tokenize(text)
            token_ids = tokenizer.encode(text)
            
            visualization = TokenVisualizer.visualize_tokens(text, tokens, token_ids)
            print(visualization)


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Create tokenizer
        tokenizer = create_tokenizer(args)
        
        # Get input text
        input_text = get_input_text(args)
        
        if not input_text:
            print("Error: No input text provided", file=sys.stderr)
            return 1
        
        # Process the text
        process_text(tokenizer, input_text, args)
        
        return 0
        
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())