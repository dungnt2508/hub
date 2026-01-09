"""
Knowledge Ingester - Load documents into vector store for RAG
Handles document processing, embedding, and storage
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from ..infrastructure.ai_provider import AIProvider
from ..infrastructure.vector_store import QdrantVectorStore
from ..infrastructure.qdrant_client import VectorPoint
from ..shared.logger import logger
from ..shared.exceptions import ExternalServiceError
from .document_chunker import DocumentChunker, DocumentChunk


class KnowledgeIngester:
    """
    Ingest documents into knowledge base.
    
    Pipeline:
    1. Split document into chunks
    2. Generate embeddings for each chunk
    3. Store in vector store with metadata
    4. Track ingestion history
    """
    
    def __init__(
        self,
        vector_store: Optional[QdrantVectorStore] = None,
        ai_provider: Optional[AIProvider] = None,
        chunker: Optional[DocumentChunker] = None,
    ):
        """
        Initialize knowledge ingester.
        
        Args:
            vector_store: Vector store instance
            ai_provider: AI provider for embeddings
            chunker: Document chunker instance
        """
        self.vector_store = vector_store or QdrantVectorStore()
        self.ai_provider = ai_provider or AIProvider()
        self.chunker = chunker or DocumentChunker()
        
        logger.info("KnowledgeIngester initialized")
    
    async def ingest_documents(
        self,
        documents: List[Dict[str, Any]],
        tenant_id: str,
        domain: str,
        batch_size: int = 10,
    ) -> Dict[str, Any]:
        """
        Ingest multiple documents into knowledge base.
        
        Args:
            documents: List of document dicts with:
                - content: Document text
                - source: Document identifier
                - page: Page number (optional)
                - metadata: Additional metadata (optional)
            tenant_id: Tenant UUID
            domain: Domain name (hr, catalog, etc.)
            batch_size: Batch size for embedding generation
        
        Returns:
            Ingestion result with statistics
        
        Raises:
            ExternalServiceError: If ingestion fails
        """
        try:
            logger.info(
                f"Starting ingestion of {len(documents)} documents",
                extra={
                    "tenant_id": tenant_id,
                    "domain": domain,
                    "count": len(documents),
                }
            )
            
            # Ensure collection exists
            collection_exists = await self.vector_store.collection_exists(tenant_id)
            if not collection_exists:
                await self.vector_store.create_collection(tenant_id)
                logger.info(f"Created collection for tenant {tenant_id}")
            
            # Step 1: Chunk documents
            all_chunks = self.chunker.chunk_documents(documents)
            
            if not all_chunks:
                logger.warning("No chunks generated from documents")
                return {
                    "status": "success",
                    "ingested_count": 0,
                    "chunk_count": 0,
                    "failed_count": 0,
                    "ingestion_time": 0,
                }
            
            logger.info(f"Generated {len(all_chunks)} chunks from documents")
            
            # Step 2: Generate embeddings and prepare vectors
            vectors = []
            failed_chunks = 0
            
            for i, chunk in enumerate(all_chunks):
                try:
                    # Generate embedding
                    embedding = await self.ai_provider.embed(chunk.content)
                    
                    # Prepare metadata
                    metadata = {
                        "domain": domain,
                        "source": chunk.source,
                        "page": chunk.page,
                        "chunk_index": chunk.chunk_index,
                        "ingested_at": datetime.utcnow().isoformat(),
                    }
                    
                    # Merge with additional metadata
                    if chunk.metadata:
                        metadata.update(chunk.metadata)
                    
                    # Create vector point
                    vector = VectorPoint(
                        id=chunk.id,
                        vector=embedding,
                        metadata=metadata,
                    )
                    vectors.append(vector)
                    
                    # Log progress
                    if (i + 1) % max(10, len(all_chunks) // 10) == 0:
                        logger.info(
                            f"Processed {i + 1}/{len(all_chunks)} chunks",
                            extra={"tenant_id": tenant_id, "progress": f"{(i+1)*100//len(all_chunks)}%"}
                        )
                
                except Exception as e:
                    logger.warning(
                        f"Failed to embed chunk {chunk.id}: {e}",
                        extra={"chunk_id": chunk.id},
                        exc_info=True
                    )
                    failed_chunks += 1
            
            if not vectors:
                raise ExternalServiceError("No vectors generated from chunks")
            
            logger.info(
                f"Generated {len(vectors)} vectors (failed: {failed_chunks})",
                extra={"tenant_id": tenant_id, "success": len(vectors), "failed": failed_chunks}
            )
            
            # Step 3: Upsert vectors in batches
            ingested_count = 0
            
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                
                try:
                    await self.vector_store.upsert_vectors(tenant_id, batch)
                    ingested_count += len(batch)
                    
                    logger.info(
                        f"Upserted batch {i // batch_size + 1}",
                        extra={
                            "tenant_id": tenant_id,
                            "batch_size": len(batch),
                            "total_ingested": ingested_count,
                        }
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to upsert batch: {e}",
                        extra={"batch_index": i // batch_size},
                        exc_info=True
                    )
                    raise
            
            result = {
                "status": "success",
                "ingested_count": ingested_count,
                "chunk_count": len(all_chunks),
                "failed_count": failed_chunks,
                "ingestion_time": datetime.utcnow().isoformat(),
            }
            
            logger.info(
                f"Ingestion complete: {ingested_count} vectors stored",
                extra=result
            )
            
            return result
        
        except Exception as e:
            logger.error(
                f"Knowledge ingestion failed: {e}",
                extra={"tenant_id": tenant_id, "domain": domain},
                exc_info=True
            )
            raise ExternalServiceError(f"Ingestion failed: {e}") from e
    
    async def ingest_from_file(
        self,
        file_path: str,
        tenant_id: str,
        domain: str,
        file_type: str = "txt",
    ) -> Dict[str, Any]:
        """
        Ingest document from file.
        
        Args:
            file_path: Path to file
            tenant_id: Tenant UUID
            domain: Domain name
            file_type: File type (txt, pdf, markdown)
        
        Returns:
            Ingestion result
        
        Raises:
            ExternalServiceError: If file reading fails
        """
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Prepare document
            document = {
                "content": content,
                "source": file_path,
                "metadata": {
                    "file_type": file_type,
                    "original_path": file_path,
                }
            }
            
            # Ingest
            return await self.ingest_documents(
                documents=[document],
                tenant_id=tenant_id,
                domain=domain,
            )
        
        except FileNotFoundError as e:
            logger.error(f"File not found: {file_path}", exc_info=True)
            raise ExternalServiceError(f"File not found: {file_path}") from e
        except Exception as e:
            logger.error(f"Failed to ingest file: {e}", exc_info=True)
            raise ExternalServiceError(f"File ingestion failed: {e}") from e
    
    async def delete_domain_knowledge(
        self,
        tenant_id: str,
        domain: str,
    ) -> bool:
        """
        Delete all knowledge for a domain.
        
        Args:
            tenant_id: Tenant UUID
            domain: Domain name
        
        Returns:
            True if successful
        """
        try:
            # Search for all documents in domain
            # This is a simplified version - in production, you might need a more
            # sophisticated approach to delete by metadata filter
            
            logger.info(
                f"Deleting domain knowledge",
                extra={"tenant_id": tenant_id, "domain": domain}
            )
            
            # TODO: Implement filtered deletion based on domain metadata
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete domain knowledge: {e}", exc_info=True)
            return False
    
    async def update_document(
        self,
        document: Dict[str, Any],
        tenant_id: str,
        domain: str,
    ) -> Dict[str, Any]:
        """
        Update a single document (delete old + ingest new).
        
        Args:
            document: Document dict
            tenant_id: Tenant UUID
            domain: Domain name
        
        Returns:
            Update result
        """
        source = document.get("source", "")
        
        try:
            logger.info(
                f"Updating document",
                extra={"tenant_id": tenant_id, "source": source}
            )
            
            # TODO: Delete old chunks of this source
            
            # Ingest new version
            return await self.ingest_documents(
                documents=[document],
                tenant_id=tenant_id,
                domain=domain,
            )
        
        except Exception as e:
            logger.error(
                f"Failed to update document: {e}",
                extra={"source": source},
                exc_info=True
            )
            raise ExternalServiceError(f"Document update failed: {e}") from e

