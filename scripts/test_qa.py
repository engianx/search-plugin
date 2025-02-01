"""Test script for Q&A generation."""
import sys
import os
import logging
from ..utils.llm_chat import ChatCompletionGenerator
from ..processor.qa import generate_qa_pairs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    if len(sys.argv) != 2:
        print("Usage: python -m search.scripts.test_qa <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    # Read input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        sys.exit(1)

    # Initialize chat
    chat = ChatCompletionGenerator()

    # Generate Q&A pairs
    qa_pairs = generate_qa_pairs(chat, content)

    # Print results
    print("\nGenerated Q&A Pairs:")
    print("===================")
    for i, qa in enumerate(qa_pairs, 1):
        print(f"\nPair #{i}:")
        print(f"Q: {qa['question']}")
        print(f"A: {qa['answer']}")
        print("-" * 80)

if __name__ == "__main__":
    main()