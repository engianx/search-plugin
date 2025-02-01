"""Text chunking utilities."""
import tiktoken
from typing import List

class TextChunker:
    """Handles text chunking logic."""

    def __init__(self, sentence_splitters: List[str], max_tokens: int):
        """Initialize text chunker.

        Args:
            sentence_splitters: List of strings to split sentences on
            max_tokens: Maximum number of tokens per chunk
        """
        self.sentence_splitters = sentence_splitters
        self.max_tokens = max_tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences.

        Args:
            text: Text to split into sentences

        Returns:
            List of sentences
        """
        sentences = [text]
        for splitter in self.sentence_splitters:
            new_sentences = []
            for sentence in sentences:
                new_sentences.extend(sentence.split(splitter))
            sentences = new_sentences
        return [s.strip() for s in sentences if s.strip()]

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks respecting sentence boundaries.

        Args:
            text: Text to split into chunks

        Returns:
            List of text chunks
        """
        sentences = self._split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = len(self.tokenizer.encode(sentence))

            if sentence_tokens > self.max_tokens:
                # Split long sentence by tokens
                tokens = self.tokenizer.encode(sentence)
                for i in range(0, len(tokens), self.max_tokens):
                    chunk_tokens = tokens[i:i + self.max_tokens]
                    chunks.append(self.tokenizer.decode(chunk_tokens))
                continue

            if current_tokens + sentence_tokens > self.max_tokens:
                # Start new chunk
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks