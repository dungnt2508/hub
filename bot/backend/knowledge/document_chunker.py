"""
Document Chunker - Split documents into chunks for embedding
Supports semantic chunking with overlap
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import re

from ..shared.logger import logger


@dataclass
class DocumentChunk:
    """Represents a chunk of a document"""
    id: str
    content: str
    source: str
    page: Optional[int] = None
    chunk_index: int = 0
    metadata: Optional[Dict[str, Any]] = None


class DocumentChunker:
    """
    Split documents into chunks for RAG pipeline.
    
    Supports:
    - Fixed-size chunking with overlap
    - Semantic chunking (split on sentences/paragraphs)
    - Metadata preservation
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        split_on_newlines: bool = True,
    ):
        """
        Initialize document chunker.
        
        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
            split_on_newlines: Whether to prefer splitting on newlines
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.split_on_newlines = split_on_newlines
        
        logger.info(
            f"DocumentChunker initialized: "
            f"chunk_size={chunk_size}, overlap={chunk_overlap}"
        )
    
    def chunk_text(
        self,
        text: str,
        source: str,
        page: Optional[int] = None,
        base_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        Split text into chunks.
        
        Args:
            text: Text to chunk
            source: Source document identifier
            page: Page number (if applicable)
            base_id: Base ID for chunk identifiers
            metadata: Additional metadata to attach to chunks
        
        Returns:
            List of document chunks
        """
        if not text or not text.strip():
            logger.warning(f"Empty text to chunk from source: {source}")
            return []
        
        # Clean text
        text = self._clean_text(text)
        
        # Split into chunks
        if self.split_on_newlines:
            chunks_text = self._semantic_split(text)
        else:
            chunks_text = self._fixed_split(text)
        
        # Convert to DocumentChunk objects
        chunks = []
        for i, chunk_text in enumerate(chunks_text):
            chunk = DocumentChunk(
                id=f"{base_id or source}#{i}" if base_id else f"{source}#{i}",
                content=chunk_text,
                source=source,
                page=page,
                chunk_index=i,
                metadata=metadata or {},
            )
            chunks.append(chunk)
        
        logger.info(
            f"Split {len(text)} characters into {len(chunks)} chunks",
            extra={
                "source": source,
                "chunks_count": len(chunks),
                "avg_chunk_size": len(text) // len(chunks) if chunks else 0,
            }
        )
        
        return chunks
    
    def chunk_documents(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[DocumentChunk]:
        """
        Chunk multiple documents.
        
        Each document dict should contain:
        - content (str): Document text
        - source (str): Document source identifier
        - page (int, optional): Page number
        - metadata (dict, optional): Additional metadata
        
        Args:
            documents: List of document dicts
        
        Returns:
            List of all chunks from all documents
        """
        all_chunks = []
        
        for doc in documents:
            content = doc.get("content", "")
            source = doc.get("source", "unknown")
            page = doc.get("page")
            metadata = doc.get("metadata", {})
            
            chunks = self.chunk_text(
                text=content,
                source=source,
                page=page,
                metadata=metadata,
            )
            
            all_chunks.extend(chunks)
        
        logger.info(
            f"Chunked {len(documents)} documents into {len(all_chunks)} chunks"
        )
        
        return all_chunks
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text: remove extra whitespace, normalize unicode.
        
        Args:
            text: Text to clean
        
        Returns:
            Cleaned text
        """
        # Remove multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove trailing whitespace
        text = text.strip()
        
        return text
    
    def _semantic_split(self, text: str) -> List[str]:
        """
        Split text semantically on paragraphs/sentences with overlap.
        
        Prefers splitting on paragraph boundaries (double newlines),
        then sentences, then fixed-size chunks.
        
        Args:
            text: Text to split
        
        Returns:
            List of chunks
        """
        chunks = []
        
        # Split on paragraph boundaries first
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            
            if not paragraph:
                continue
            
            # If adding this paragraph exceeds chunk size
            if len(current_chunk) + len(paragraph) + 2 > self.chunk_size:
                # Finalize current chunk if not empty
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Check if paragraph itself is too large
                if len(paragraph) > self.chunk_size:
                    # Split paragraph into sentences
                    para_chunks = self._split_long_paragraph(paragraph)
                    chunks.extend(para_chunks)
                    # Keep last part for overlap
                    current_chunk = para_chunks[-1][-self.chunk_overlap:] if para_chunks else ""
                else:
                    # Start new chunk with this paragraph
                    current_chunk = paragraph
            else:
                # Add to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """
        Split a long paragraph into sentences.
        
        Args:
            paragraph: Long paragraph text
        
        Returns:
            List of sentence chunks
        """
        # Simple sentence splitting on . ! ?
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) + 1 > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _fixed_split(self, text: str) -> List[str]:
        """
        Split text into fixed-size chunks with overlap.
        
        Args:
            text: Text to split
        
        Returns:
            List of chunks
        """
        chunks = []
        
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk = text[i:i + self.chunk_size]
            
            if chunk.strip():  # Only add non-empty chunks
                chunks.append(chunk.strip())
        
        return chunks

