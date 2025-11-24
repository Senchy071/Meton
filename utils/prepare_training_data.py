#!/usr/bin/env python3
"""Prepare training data for fine-tuning from Meton conversations.

This utility extracts conversations from Meton's saved sessions and formats
them for llama.cpp fine-tuning with LoRA.

Usage:
    python prepare_training_data.py \
        --conversations-dir ./conversations \
        --output training_data.txt \
        --format llama

Example with filters:
    python prepare_training_data.py \
        --conversations-dir ./conversations \
        --output training_data.txt \
        --min-length 50 \
        --filter-keyword "Python" \
        --exclude-system
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Set
from datetime import datetime


class TrainingDataPreparator:
    """Prepare training data from Meton conversations."""

    def __init__(self, args):
        """Initialize with command-line arguments."""
        self.conversations_dir = Path(args.conversations_dir)
        self.output_file = Path(args.output)
        self.format = args.format
        self.min_length = args.min_length
        self.max_length = args.max_length
        self.filter_keyword = args.filter_keyword
        self.exclude_system = args.exclude_system
        self.deduplicate = args.deduplicate
        self.quality_threshold = args.quality_threshold

        self.seen_exchanges: Set[str] = set()
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'total_exchanges': 0,
            'filtered_exchanges': 0,
            'duplicates_removed': 0,
        }

    def load_conversations(self) -> List[Dict[str, Any]]:
        """Load all conversation files."""
        conversations = []
        json_files = list(self.conversations_dir.glob('*.json'))
        self.stats['total_files'] = len(json_files)

        for file_path in json_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    conversations.append(data)
                    self.stats['processed_files'] += 1
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")

        return conversations

    def extract_exchanges(self, conversations: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract user-assistant exchanges from conversations."""
        exchanges = []

        for conv in conversations:
            messages = conv.get('messages', [])

            # Pair up user and assistant messages
            i = 0
            while i < len(messages):
                msg = messages[i]

                # Skip system messages if requested
                if self.exclude_system and msg.get('role') == 'system':
                    i += 1
                    continue

                # Look for user message followed by assistant message
                if msg.get('role') == 'user' and i + 1 < len(messages):
                    next_msg = messages[i + 1]
                    if next_msg.get('role') == 'assistant':
                        user_content = msg.get('content', '').strip()
                        assistant_content = next_msg.get('content', '').strip()

                        if user_content and assistant_content:
                            exchanges.append({
                                'user': user_content,
                                'assistant': assistant_content,
                                'timestamp': msg.get('timestamp', '')
                            })
                            self.stats['total_exchanges'] += 1

                        i += 2
                        continue

                i += 1

        return exchanges

    def filter_exchanges(self, exchanges: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Filter exchanges based on criteria."""
        filtered = []

        for exchange in exchanges:
            user_text = exchange['user']
            assistant_text = exchange['assistant']

            # Length filtering
            combined_length = len(user_text) + len(assistant_text)
            if combined_length < self.min_length:
                continue
            if self.max_length > 0 and combined_length > self.max_length:
                continue

            # Keyword filtering
            if self.filter_keyword:
                combined_text = user_text + ' ' + assistant_text
                if self.filter_keyword.lower() not in combined_text.lower():
                    continue

            # Deduplication
            if self.deduplicate:
                # Create hash of exchange
                exchange_hash = f"{user_text[:100]}:{assistant_text[:100]}"
                if exchange_hash in self.seen_exchanges:
                    self.stats['duplicates_removed'] += 1
                    continue
                self.seen_exchanges.add(exchange_hash)

            # Quality filtering (basic heuristics)
            if self.quality_threshold > 0:
                quality_score = self.estimate_quality(user_text, assistant_text)
                if quality_score < self.quality_threshold:
                    continue

            filtered.append(exchange)
            self.stats['filtered_exchanges'] += 1

        return filtered

    def estimate_quality(self, user_text: str, assistant_text: str) -> float:
        """Estimate quality of exchange (0.0-1.0).

        Basic heuristics:
        - Longer responses generally better
        - Code blocks indicate technical content
        - Well-formatted responses score higher
        """
        score = 0.5  # Base score

        # Length bonus (up to +0.2)
        length_score = min(len(assistant_text) / 1000, 0.2)
        score += length_score

        # Code block bonus (+0.15)
        if '```' in assistant_text:
            score += 0.15

        # Formatting bonus (+0.1)
        if any(marker in assistant_text for marker in ['**', '##', '- ', '1. ']):
            score += 0.1

        # Penalty for very short responses (-0.3)
        if len(assistant_text) < 50:
            score -= 0.3

        # Penalty for error messages (-0.2)
        error_indicators = ['error', 'failed', 'cannot', "can't"]
        if any(ind in assistant_text.lower()[:200] for ind in error_indicators):
            score -= 0.2

        return max(0.0, min(1.0, score))

    def format_llama(self, exchanges: List[Dict[str, str]]) -> str:
        """Format exchanges for llama.cpp (Llama format)."""
        formatted = []

        for exchange in exchanges:
            user = exchange['user'].replace('\n', ' ')
            assistant = exchange['assistant']

            # Llama-2 format
            entry = f"<s>[INST] {user} [/INST] {assistant} </s>\n\n"
            formatted.append(entry)

        return ''.join(formatted)

    def format_alpaca(self, exchanges: List[Dict[str, str]]) -> str:
        """Format exchanges for Alpaca-style training."""
        formatted = []

        for exchange in exchanges:
            entry = {
                "instruction": exchange['user'],
                "input": "",
                "output": exchange['assistant']
            }
            formatted.append(json.dumps(entry))

        return '\n'.join(formatted)

    def format_chat(self, exchanges: List[Dict[str, str]]) -> str:
        """Format exchanges for ChatML format."""
        formatted = []

        for exchange in exchanges:
            entry = f"""<|im_start|>user
{exchange['user']}<|im_end|>
<|im_start|>assistant
{exchange['assistant']}<|im_end|>

"""
            formatted.append(entry)

        return ''.join(formatted)

    def prepare(self):
        """Main preparation workflow."""
        print("=" * 60)
        print("Meton Training Data Preparation Utility")
        print("=" * 60)
        print()

        # Load conversations
        print(f"Loading conversations from: {self.conversations_dir}")
        conversations = self.load_conversations()
        print(f"✓ Loaded {self.stats['processed_files']}/{self.stats['total_files']} conversation files")
        print()

        # Extract exchanges
        print("Extracting user-assistant exchanges...")
        exchanges = self.extract_exchanges(conversations)
        print(f"✓ Extracted {self.stats['total_exchanges']} exchanges")
        print()

        # Filter exchanges
        print("Applying filters...")
        if self.min_length > 0:
            print(f"  - Minimum length: {self.min_length} characters")
        if self.max_length > 0:
            print(f"  - Maximum length: {self.max_length} characters")
        if self.filter_keyword:
            print(f"  - Keyword filter: '{self.filter_keyword}'")
        if self.exclude_system:
            print(f"  - Excluding system messages")
        if self.deduplicate:
            print(f"  - Deduplicating exchanges")
        if self.quality_threshold > 0:
            print(f"  - Quality threshold: {self.quality_threshold}")

        filtered_exchanges = self.filter_exchanges(exchanges)
        print(f"✓ Filtered to {self.stats['filtered_exchanges']} high-quality exchanges")
        if self.deduplicate:
            print(f"  (Removed {self.stats['duplicates_removed']} duplicates)")
        print()

        # Format output
        print(f"Formatting for {self.format} training...")
        if self.format == 'llama':
            output_text = self.format_llama(filtered_exchanges)
        elif self.format == 'alpaca':
            output_text = self.format_alpaca(filtered_exchanges)
        elif self.format == 'chat':
            output_text = self.format_chat(filtered_exchanges)
        else:
            raise ValueError(f"Unknown format: {self.format}")

        # Write output
        print(f"Writing to: {self.output_file}")
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, 'w') as f:
            f.write(output_text)

        file_size = self.output_file.stat().st_size
        print(f"✓ Wrote {file_size:,} bytes")
        print()

        # Summary
        print("=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"Conversation files processed: {self.stats['processed_files']}")
        print(f"Total exchanges extracted:    {self.stats['total_exchanges']}")
        print(f"High-quality exchanges:       {self.stats['filtered_exchanges']}")
        print(f"Output file:                  {self.output_file}")
        print(f"Output format:                {self.format}")
        print()
        print("✓ Training data preparation complete!")
        print()
        print("Next steps:")
        print("1. Review the output file to ensure quality")
        print("2. Use with llama.cpp finetune:")
        print(f"   ./finetune --model-base base.gguf --train-data {self.output_file}")
        print()


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Prepare training data from Meton conversations for fine-tuning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python prepare_training_data.py \\
      --conversations-dir ./conversations \\
      --output training_data.txt

  # With keyword filter
  python prepare_training_data.py \\
      --conversations-dir ./conversations \\
      --output python_training.txt \\
      --filter-keyword "Python"

  # High-quality only
  python prepare_training_data.py \\
      --conversations-dir ./conversations \\
      --output quality_training.txt \\
      --min-length 100 \\
      --quality-threshold 0.7 \\
      --deduplicate
        """
    )

    parser.add_argument(
        '--conversations-dir',
        type=str,
        default='./conversations',
        help='Directory containing conversation JSON files (default: ./conversations)'
    )

    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output training data file'
    )

    parser.add_argument(
        '--format',
        type=str,
        choices=['llama', 'alpaca', 'chat'],
        default='llama',
        help='Output format (default: llama)'
    )

    parser.add_argument(
        '--min-length',
        type=int,
        default=0,
        help='Minimum combined length of exchange (default: 0)'
    )

    parser.add_argument(
        '--max-length',
        type=int,
        default=0,
        help='Maximum combined length of exchange (default: unlimited)'
    )

    parser.add_argument(
        '--filter-keyword',
        type=str,
        default='',
        help='Only include exchanges mentioning this keyword'
    )

    parser.add_argument(
        '--exclude-system',
        action='store_true',
        help='Exclude system messages from output'
    )

    parser.add_argument(
        '--deduplicate',
        action='store_true',
        help='Remove duplicate exchanges'
    )

    parser.add_argument(
        '--quality-threshold',
        type=float,
        default=0.0,
        help='Minimum quality score (0.0-1.0, default: 0.0 = no filtering)'
    )

    args = parser.parse_args()

    # Validate arguments
    if not Path(args.conversations_dir).exists():
        print(f"Error: Conversations directory not found: {args.conversations_dir}")
        return 1

    if args.quality_threshold < 0.0 or args.quality_threshold > 1.0:
        print("Error: Quality threshold must be between 0.0 and 1.0")
        return 1

    # Run preparation
    try:
        preparator = TrainingDataPreparator(args)
        preparator.prepare()
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
