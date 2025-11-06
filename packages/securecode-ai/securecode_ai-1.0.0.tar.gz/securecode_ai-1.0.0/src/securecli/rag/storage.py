"""
SecureCLI RAG Storage System
Vector storage and retrieval for knowledge base and embeddings
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import uuid

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from .embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)

@dataclass
class Document:
    """Document for storage in vector database"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class SearchResult:
    """Search result from vector database"""
    document: Document
    score: float
    distance: float

class VectorStore:
    """
    Abstract base class for vector storage backends
    """
    
    async def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store"""
        raise NotImplementedError
    
    async def search(self, query: str, limit: int = 10, filter_metadata: Optional[Dict] = None) -> List[SearchResult]:
        """Search for similar documents"""
        raise NotImplementedError
    
    async def search_by_embedding(self, embedding: List[float], limit: int = 10, filter_metadata: Optional[Dict] = None) -> List[SearchResult]:
        """Search by embedding vector"""
        raise NotImplementedError
    
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """Get document by ID"""
        raise NotImplementedError
    
    async def update_document(self, doc_id: str, content: Optional[str] = None, metadata: Optional[Dict] = None) -> bool:
        """Update document content or metadata"""
        raise NotImplementedError
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete document by ID"""
        raise NotImplementedError
    
    async def list_collections(self) -> List[str]:
        """List available collections"""
        raise NotImplementedError
    
    async def clear_collection(self, collection_name: str) -> None:
        """Clear all documents from collection"""
        raise NotImplementedError

class ChromaVectorStore(VectorStore):
    """
    ChromaDB vector store implementation
    """
    
    def __init__(self, 
                 collection_name: str = "securecli",
                 persist_directory: Optional[str] = None,
                 host: Optional[str] = None,
                 port: Optional[int] = None):
        if not CHROMA_AVAILABLE:
            raise ImportError("ChromaDB not available. Install with: pip install chromadb")
        
        self.collection_name = collection_name
        self.embedding_generator = EmbeddingGenerator()
        
        # Initialize ChromaDB client
        if host and port:
            # Remote ChromaDB instance
            self.client = chromadb.HttpClient(host=host, port=port)
        else:
            # Local ChromaDB instance
            settings = Settings()
            if persist_directory:
                settings.persist_directory = persist_directory
                settings.anonymized_telemetry = False
            
            self.client = chromadb.Client(settings)
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
            logger.info(f"Using existing ChromaDB collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "SecureCLI knowledge base"}
            )
            logger.info(f"Created new ChromaDB collection: {collection_name}")
    
    async def add_documents(self, documents: List[Document]) -> None:
        """Add documents to ChromaDB"""
        if not documents:
            return
        
        # Generate embeddings if not present
        for doc in documents:
            if doc.embedding is None:
                doc.embedding = await self.embedding_generator.generate_embedding(doc.content)
        
        # Prepare data for ChromaDB
        ids = [doc.id for doc in documents]
        embeddings = [doc.embedding for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        documents_content = [doc.content for doc in documents]
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents_content
        )
        
        logger.info(f"Added {len(documents)} documents to ChromaDB")
    
    async def search(self, query: str, limit: int = 10, filter_metadata: Optional[Dict] = None) -> List[SearchResult]:
        """Search ChromaDB by query text"""
        # Generate query embedding
        query_embedding = await self.embedding_generator.generate_embedding(query)
        
        return await self.search_by_embedding(query_embedding, limit, filter_metadata)
    
    async def search_by_embedding(self, embedding: List[float], limit: int = 10, filter_metadata: Optional[Dict] = None) -> List[SearchResult]:
        """Search ChromaDB by embedding vector"""
        # Build where clause for filtering
        where_clause = filter_metadata if filter_metadata else None
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=limit,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
        
        # Convert to SearchResult objects
        search_results = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                document = Document(
                    id=doc_id,
                    content=results['documents'][0][i],
                    metadata=results['metadatas'][0][i] or {},
                    embedding=None  # Don't return embeddings in search results
                )
                
                distance = results['distances'][0][i]
                score = 1.0 - distance  # Convert distance to similarity score
                
                search_results.append(SearchResult(
                    document=document,
                    score=score,
                    distance=distance
                ))
        
        return search_results
    
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """Get document by ID from ChromaDB"""
        try:
            results = self.collection.get(
                ids=[doc_id],
                include=["documents", "metadatas", "embeddings"]
            )
            
            if results['ids'] and results['ids'][0]:
                return Document(
                    id=doc_id,
                    content=results['documents'][0],
                    metadata=results['metadatas'][0] or {},
                    embedding=results['embeddings'][0] if results['embeddings'] else None
                )
        except Exception as e:
            logger.error(f"Error getting document {doc_id}: {str(e)}")
        
        return None
    
    async def update_document(self, doc_id: str, content: Optional[str] = None, metadata: Optional[Dict] = None) -> bool:
        """Update document in ChromaDB"""
        try:
            # Get existing document
            existing_doc = await self.get_document(doc_id)
            if not existing_doc:
                return False
            
            # Update content and/or metadata
            updated_content = content if content is not None else existing_doc.content
            updated_metadata = {**existing_doc.metadata, **(metadata or {})}
            
            # Generate new embedding if content changed
            updated_embedding = existing_doc.embedding
            if content is not None and content != existing_doc.content:
                updated_embedding = await self.embedding_generator.generate_embedding(updated_content)
            
            # Update in ChromaDB (delete and re-add)
            self.collection.delete(ids=[doc_id])
            
            updated_doc = Document(
                id=doc_id,
                content=updated_content,
                metadata=updated_metadata,
                embedding=updated_embedding,
                updated_at=datetime.now()
            )
            
            await self.add_documents([updated_doc])
            return True
            
        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {str(e)}")
            return False
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete document from ChromaDB"""
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {str(e)}")
            return False
    
    async def list_collections(self) -> List[str]:
        """List available ChromaDB collections"""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Error listing collections: {str(e)}")
            return []
    
    async def clear_collection(self, collection_name: str) -> None:
        """Clear all documents from ChromaDB collection"""
        try:
            if collection_name == self.collection_name:
                # Clear current collection
                self.client.delete_collection(collection_name)
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": "SecureCLI knowledge base"}
                )
            else:
                # Clear other collection
                self.client.delete_collection(collection_name)
                
            logger.info(f"Cleared collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error clearing collection {collection_name}: {str(e)}")

class FileVectorStore(VectorStore):
    """
    File-based vector store implementation (fallback when ChromaDB not available)
    """
    
    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.documents_file = self.storage_path / "documents.json"
        self.embeddings_file = self.storage_path / "embeddings.pkl"
        self.metadata_file = self.storage_path / "metadata.json"
        
        self.embedding_generator = EmbeddingGenerator()
        
        # Load existing data
        self.documents: Dict[str, Document] = self._load_documents()
        self.embeddings: Dict[str, List[float]] = self._load_embeddings()
        
        logger.info(f"Initialized file-based vector store at {storage_path}")
    
    def _load_documents(self) -> Dict[str, Document]:
        """Load documents from file"""
        if not self.documents_file.exists():
            return {}
        
        try:
            with open(self.documents_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            documents = {}
            for doc_id, doc_data in data.items():
                documents[doc_id] = Document(
                    id=doc_data['id'],
                    content=doc_data['content'],
                    metadata=doc_data.get('metadata', {}),
                    created_at=datetime.fromisoformat(doc_data.get('created_at', datetime.now().isoformat())),
                    updated_at=datetime.fromisoformat(doc_data.get('updated_at', datetime.now().isoformat()))
                )
            
            return documents
        except Exception as e:
            logger.error(f"Error loading documents: {str(e)}")
            return {}
    
    def _load_embeddings(self) -> Dict[str, List[float]]:
        """Load embeddings from file"""
        if not self.embeddings_file.exists():
            return {}
        
        try:
            with open(self.embeddings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading embeddings: {str(e)}")
            return {}
    
    def _save_documents(self) -> None:
        """Save documents to file"""
        try:
            data = {}
            for doc_id, doc in self.documents.items():
                data[doc_id] = {
                    'id': doc.id,
                    'content': doc.content,
                    'metadata': doc.metadata,
                    'created_at': doc.created_at.isoformat(),
                    'updated_at': doc.updated_at.isoformat()
                }
            
            with open(self.documents_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving documents: {str(e)}")
    
    def _save_embeddings(self) -> None:
        """Save embeddings to file using safe JSON serialization"""
        try:
            # Convert embeddings to JSON-serializable format
            serializable_embeddings = self._convert_embeddings_to_json(self.embeddings)
            with open(self.embeddings_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_embeddings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving embeddings: {str(e)}")
    
    def _convert_embeddings_to_json(self, embeddings: Dict[str, Any]) -> Dict[str, Any]:
        """Convert embeddings to JSON-serializable format"""
        result = {}
        for key, value in embeddings.items():
            if isinstance(value, (list, tuple)) and all(isinstance(x, (int, float)) for x in value):
                result[key] = list(value)  # Convert embedding vectors to lists
            elif isinstance(value, (str, int, float, bool, type(None))):
                result[key] = value
            else:
                # Skip non-serializable objects
                continue
        return result
    
    async def add_documents(self, documents: List[Document]) -> None:
        """Add documents to file store"""
        for doc in documents:
            # Generate embedding if not present
            if doc.embedding is None:
                doc.embedding = await self.embedding_generator.generate_embedding(doc.content)
            
            # Store document and embedding
            self.documents[doc.id] = doc
            self.embeddings[doc.id] = doc.embedding
        
        # Save to files
        self._save_documents()
        self._save_embeddings()
        
        logger.info(f"Added {len(documents)} documents to file store")
    
    async def search(self, query: str, limit: int = 10, filter_metadata: Optional[Dict] = None) -> List[SearchResult]:
        """Search file store by query text"""
        query_embedding = await self.embedding_generator.generate_embedding(query)
        return await self.search_by_embedding(query_embedding, limit, filter_metadata)
    
    async def search_by_embedding(self, embedding: List[float], limit: int = 10, filter_metadata: Optional[Dict] = None) -> List[SearchResult]:
        """Search file store by embedding vector"""
        if not NUMPY_AVAILABLE:
            logger.warning("NumPy not available, using simple similarity")
            return await self._simple_similarity_search(embedding, limit, filter_metadata)
        
        import numpy as np
        
        query_vector = np.array(embedding)
        results = []
        
        for doc_id, doc in self.documents.items():
            # Apply metadata filter
            if filter_metadata:
                if not all(doc.metadata.get(k) == v for k, v in filter_metadata.items()):
                    continue
            
            # Calculate similarity
            if doc_id in self.embeddings:
                doc_vector = np.array(self.embeddings[doc_id])
                
                # Cosine similarity
                cosine_similarity = np.dot(query_vector, doc_vector) / (
                    np.linalg.norm(query_vector) * np.linalg.norm(doc_vector)
                )
                
                # Euclidean distance
                distance = np.linalg.norm(query_vector - doc_vector)
                
                results.append(SearchResult(
                    document=doc,
                    score=float(cosine_similarity),
                    distance=float(distance)
                ))
        
        # Sort by similarity score (descending)
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:limit]
    
    async def _simple_similarity_search(self, embedding: List[float], limit: int = 10, filter_metadata: Optional[Dict] = None) -> List[SearchResult]:
        """Simple similarity search without NumPy"""
        results = []
        
        for doc_id, doc in self.documents.items():
            # Apply metadata filter
            if filter_metadata:
                if not all(doc.metadata.get(k) == v for k, v in filter_metadata.items()):
                    continue
            
            # Simple dot product similarity
            if doc_id in self.embeddings:
                doc_embedding = self.embeddings[doc_id]
                
                if len(embedding) == len(doc_embedding):
                    similarity = sum(a * b for a, b in zip(embedding, doc_embedding))
                    distance = sum((a - b) ** 2 for a, b in zip(embedding, doc_embedding)) ** 0.5
                    
                    results.append(SearchResult(
                        document=doc,
                        score=similarity,
                        distance=distance
                    ))
        
        # Sort by similarity score (descending)
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:limit]
    
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """Get document by ID from file store"""
        return self.documents.get(doc_id)
    
    async def update_document(self, doc_id: str, content: Optional[str] = None, metadata: Optional[Dict] = None) -> bool:
        """Update document in file store"""
        if doc_id not in self.documents:
            return False
        
        doc = self.documents[doc_id]
        
        # Update content
        if content is not None:
            doc.content = content
            doc.embedding = await self.embedding_generator.generate_embedding(content)
            self.embeddings[doc_id] = doc.embedding
        
        # Update metadata
        if metadata is not None:
            doc.metadata.update(metadata)
        
        doc.updated_at = datetime.now()
        
        # Save changes
        self._save_documents()
        if content is not None:
            self._save_embeddings()
        
        return True
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete document from file store"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            if doc_id in self.embeddings:
                del self.embeddings[doc_id]
            
            self._save_documents()
            self._save_embeddings()
            return True
        
        return False
    
    async def list_collections(self) -> List[str]:
        """List available collections (always return single collection for file store)"""
        return ["default"]
    
    async def clear_collection(self, collection_name: str) -> None:
        """Clear all documents from file store"""
        self.documents.clear()
        self.embeddings.clear()
        self._save_documents()
        self._save_embeddings()

class KnowledgeBase:
    """
    High-level knowledge base interface
    """
    
    def __init__(self, storage_backend: Optional[VectorStore] = None, storage_path: Optional[Path] = None):
        if storage_backend:
            self.store = storage_backend
        elif CHROMA_AVAILABLE:
            self.store = ChromaVectorStore(persist_directory=str(storage_path) if storage_path else None)
        else:
            if not storage_path:
                storage_path = Path.cwd() / "data" / "vectorstore"
            self.store = FileVectorStore(storage_path)
        
        logger.info(f"Initialized knowledge base with {type(self.store).__name__}")
    
    async def add_security_rules(self, rules: List[Dict[str, Any]]) -> None:
        """Add security rules to knowledge base"""
        documents = []
        for rule in rules:
            doc_id = f"rule_{uuid.uuid4().hex[:8]}"
            content = f"{rule.get('title', '')}\n{rule.get('description', '')}\n{rule.get('solution', '')}"
            metadata = {
                'type': 'security_rule',
                'category': rule.get('category', 'unknown'),
                'severity': rule.get('severity', 'medium'),
                'cwe_id': rule.get('cwe_id'),
                'owasp_category': rule.get('owasp_category')
            }
            
            documents.append(Document(
                id=doc_id,
                content=content,
                metadata=metadata
            ))
        
        await self.store.add_documents(documents)
        logger.info(f"Added {len(rules)} security rules to knowledge base")
    
    async def search_remediation(self, finding_description: str, limit: int = 5) -> List[SearchResult]:
        """Search for remediation advice for a security finding"""
        return await self.store.search(
            query=finding_description,
            limit=limit,
            filter_metadata={'type': 'security_rule'}
        )
    
    async def add_vulnerability_data(self, vulnerabilities: List[Dict[str, Any]]) -> None:
        """Add vulnerability data to knowledge base"""
        documents = []
        for vuln in vulnerabilities:
            doc_id = f"vuln_{uuid.uuid4().hex[:8]}"
            content = f"{vuln.get('name', '')}\n{vuln.get('description', '')}\n{vuln.get('remediation', '')}"
            metadata = {
                'type': 'vulnerability',
                'cve_id': vuln.get('cve_id'),
                'cvss_score': vuln.get('cvss_score'),
                'affected_products': vuln.get('affected_products', [])
            }
            
            documents.append(Document(
                id=doc_id,
                content=content,
                metadata=metadata
            ))
        
        await self.store.add_documents(documents)
        logger.info(f"Added {len(vulnerabilities)} vulnerabilities to knowledge base")

# Export main components
__all__ = [
    'VectorStore',
    'ChromaVectorStore', 
    'FileVectorStore',
    'KnowledgeBase',
    'Document',
    'SearchResult',
]