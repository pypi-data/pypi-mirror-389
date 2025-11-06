"""
Vector store management for SecureCLI RAG system
Handles storage, indexing, and retrieval of code embeddings
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from langchain_community.vectorstores import FAISS, Chroma
from langchain.schema import Document
from langchain.embeddings.base import Embeddings

from .embeddings import CodeChunk, CodeEmbeddings


class CodeVectorStore:
    """Manages vector storage for code chunks with metadata"""
    
    def __init__(self, 
                 embeddings: Embeddings,
                 storage_path: str,
                 store_type: str = 'faiss'):
        self.embeddings = embeddings
        self.storage_path = Path(storage_path)
        self.store_type = store_type.lower()
        self.vectorstore = None
        self.chunk_metadata = {}  # chunk_id -> CodeChunk mapping
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    async def create_index(self, embedded_chunks: List[Tuple[CodeChunk, List[float]]]) -> None:
        """Create vector index from embedded chunks"""
        if not embedded_chunks:
            raise ValueError("No embedded chunks provided")
        
        # Prepare documents for vector store
        documents = []
        chunk_metadata = {}
        
        for chunk, embedding in embedded_chunks:
            # Create document with metadata
            doc = Document(
                page_content=chunk.content,
                metadata={
                    'chunk_id': chunk.chunk_id,
                    'file_path': chunk.file_path,
                    'start_line': chunk.start_line,
                    'end_line': chunk.end_line,
                    'language': chunk.language,
                    'symbols': chunk.symbols,
                    'imports': chunk.imports,
                    'hash': chunk.hash
                }
            )
            documents.append(doc)
            chunk_metadata[chunk.chunk_id] = chunk
        
        # Create vector store
        if self.store_type == 'faiss':
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
        elif self.store_type == 'chroma':
            self.vectorstore = Chroma.from_documents(
                documents, 
                self.embeddings,
                persist_directory=str(self.storage_path / "chroma_db")
            )
        else:
            raise ValueError(f"Unsupported store type: {self.store_type}")
        
        # Store metadata
        self.chunk_metadata = chunk_metadata
        
        # Persist to disk
        await self.save_index()
    
    async def load_index(self) -> bool:
        """Load existing vector index from disk"""
        try:
            if self.store_type == 'faiss':
                index_path = self.storage_path / "faiss_index"
                if index_path.exists():
                    self.vectorstore = FAISS.load_local(str(index_path), self.embeddings)
                else:
                    return False
            
            elif self.store_type == 'chroma':
                chroma_path = self.storage_path / "chroma_db"
                if chroma_path.exists():
                    self.vectorstore = Chroma(
                        persist_directory=str(chroma_path),
                        embedding_function=self.embeddings
                    )
                else:
                    return False
            
            # Load metadata using safer JSON serialization
            metadata_path = self.storage_path / "chunk_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata_dict = json.load(f)
                    # Reconstruct CodeChunk objects from JSON data
                    self.chunk_metadata = self._reconstruct_chunks_from_dict(metadata_dict)
            
            return True
            
        except Exception as e:
            print(f"Error loading index: {e}")
            return False
    
    async def save_index(self) -> None:
        """Save vector index to disk"""
        if not self.vectorstore:
            raise ValueError("No vector store to save")
        
        if self.store_type == 'faiss':
            index_path = self.storage_path / "faiss_index"
            self.vectorstore.save_local(str(index_path))
        
        elif self.store_type == 'chroma':
            # Chroma persists automatically with persist_directory
            pass
        
        # Save metadata using safer JSON serialization
        metadata_path = self.storage_path / "chunk_metadata.json" 
        metadata_dict = self._convert_chunks_to_dict(self.chunk_metadata)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=2)
    
    async def similarity_search(self, 
                              query: str, 
                              k: int = 5,
                              filter_metadata: Dict[str, Any] = None) -> List[Tuple[CodeChunk, float]]:
        """Perform similarity search and return chunks with scores"""
        if not self.vectorstore:
            raise ValueError("Vector store not initialized")
        
        # Perform search
        if filter_metadata:
            # Use metadata filtering if supported
            docs_and_scores = self.vectorstore.similarity_search_with_score(
                query, k=k, filter=filter_metadata
            )
        else:
            docs_and_scores = self.vectorstore.similarity_search_with_score(query, k=k)
        
        # Convert to CodeChunk objects
        results = []
        for doc, score in docs_and_scores:
            chunk_id = doc.metadata.get('chunk_id')
            if chunk_id in self.chunk_metadata:
                chunk = self.chunk_metadata[chunk_id]
                results.append((chunk, score))
        
        return results
    
    async def similarity_search_by_file(self, 
                                      query: str,
                                      file_path: str,
                                      k: int = 3) -> List[Tuple[CodeChunk, float]]:
        """Search for similar chunks within a specific file"""
        filter_metadata = {'file_path': file_path}
        return await self.similarity_search(query, k=k, filter_metadata=filter_metadata)
    
    async def similarity_search_by_language(self,
                                          query: str,
                                          language: str,
                                          k: int = 5) -> List[Tuple[CodeChunk, float]]:
        """Search for similar chunks in a specific language"""
        filter_metadata = {'language': language}
        return await self.similarity_search(query, k=k, filter_metadata=filter_metadata)
    
    async def get_chunks_by_symbol(self, symbol_name: str) -> List[CodeChunk]:
        """Get all chunks that contain a specific symbol"""
        matching_chunks = []
        
        for chunk in self.chunk_metadata.values():
            if symbol_name in chunk.symbols:
                matching_chunks.append(chunk)
        
        return matching_chunks
    
    async def get_chunks_by_file(self, file_path: str) -> List[CodeChunk]:
        """Get all chunks from a specific file"""
        matching_chunks = []
        
        for chunk in self.chunk_metadata.values():
            if chunk.file_path == file_path:
                matching_chunks.append(chunk)
        
        # Sort by line number
        matching_chunks.sort(key=lambda c: c.start_line)
        return matching_chunks
    
    async def update_chunk(self, chunk: CodeChunk) -> None:
        """Update a single chunk in the index"""
        # For now, this requires rebuilding the index
        # In production, implement incremental updates
        pass
    
    async def remove_chunk(self, chunk_id: str) -> None:
        """Remove a chunk from the index"""
        # For now, this requires rebuilding the index
        # In production, implement chunk removal
        pass
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector index"""
        stats = {
            'total_chunks': len(self.chunk_metadata),
            'files_indexed': len(set(chunk.file_path for chunk in self.chunk_metadata.values())),
            'languages': {},
            'storage_size': 0
        }
        
        # Count by language
        for chunk in self.chunk_metadata.values():
            if chunk.language:
                stats['languages'][chunk.language] = \
                    stats['languages'].get(chunk.language, 0) + 1
        
        # Calculate storage size
        if self.storage_path.exists():
            for file_path in self.storage_path.rglob('*'):
                if file_path.is_file():
                    stats['storage_size'] += file_path.stat().st_size
        
        return stats
    
    async def search_cross_file_references(self, 
                                         symbol_name: str,
                                         origin_file: str) -> List[Tuple[CodeChunk, str]]:
        """Find cross-file references to a symbol"""
        references = []
        
        for chunk in self.chunk_metadata.values():
            # Skip the origin file
            if chunk.file_path == origin_file:
                continue
            
            # Check if symbol is referenced in content
            if symbol_name in chunk.content:
                # Determine reference type
                ref_type = self._classify_reference(chunk.content, symbol_name)
                references.append((chunk, ref_type))
        
        return references
    
    def _classify_reference(self, content: str, symbol_name: str) -> str:
        """Classify how a symbol is referenced in content"""
        lines = content.split('\n')
        
        for line in lines:
            if symbol_name in line:
                line = line.strip()
                
                if line.startswith('import ') or 'from ' in line:
                    return 'import'
                elif f'{symbol_name}(' in line:
                    return 'function_call'
                elif f'{symbol_name}.' in line:
                    return 'method_call'
                elif f'= {symbol_name}' in line or f'({symbol_name})' in line:
                    return 'variable_usage'
                elif f'class {symbol_name}' in line:
                    return 'inheritance'
                else:
                    return 'reference'
        
        return 'unknown'
    
    def _convert_chunks_to_dict(self, chunk_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Safely convert CodeChunk objects to dictionary for JSON serialization"""
        result = {}
        for chunk_id, chunk in chunk_metadata.items():
            result[chunk_id] = {
                'chunk_id': chunk.chunk_id,
                'file_path': chunk.file_path,
                'start_line': chunk.start_line,
                'end_line': chunk.end_line,
                'content': chunk.content,
                'language': chunk.language,
                'symbols': chunk.symbols,
                'imports': chunk.imports,
                'hash': chunk.hash
            }
        return result
    
    def _reconstruct_chunks_from_dict(self, metadata_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Safely reconstruct CodeChunk objects from dictionary"""
        from .embeddings import CodeChunk  # Import here to avoid circular import
        
        result = {}
        for chunk_id, chunk_data in metadata_dict.items():
            # Validate required fields
            required_fields = ['chunk_id', 'file_path', 'start_line', 'end_line', 'content']
            if not all(field in chunk_data for field in required_fields):
                continue  # Skip invalid chunks
            
            chunk = CodeChunk(
                chunk_id=chunk_data['chunk_id'],
                file_path=chunk_data['file_path'],
                start_line=chunk_data['start_line'],
                end_line=chunk_data['end_line'],
                content=chunk_data['content'],
                language=chunk_data.get('language', 'unknown'),
                symbols=chunk_data.get('symbols', []),
                imports=chunk_data.get('imports', []),
                hash=chunk_data.get('hash', '')
            )
            result[chunk_id] = chunk
        return result


class MemoryManager:
    """Manages different types of memory for the RAG system"""
    
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Different memory types
        self.conversation_memory = {}  # session_id -> conversation history
        self.finding_memory = {}       # file_path -> previous findings
        self.cross_file_memory = {}    # symbol -> cross-file relationships
        self.summary_memory = {}       # directory -> summary
    
    async def store_conversation(self, session_id: str, message: str, response: str) -> None:
        """Store conversation turn"""
        if session_id not in self.conversation_memory:
            self.conversation_memory[session_id] = []
        
        self.conversation_memory[session_id].append({
            'message': message,
            'response': response,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Keep only last N turns
        max_turns = 50
        if len(self.conversation_memory[session_id]) > max_turns:
            self.conversation_memory[session_id] = \
                self.conversation_memory[session_id][-max_turns:]
    
    async def get_conversation_context(self, session_id: str, last_n: int = 5) -> str:
        """Get recent conversation context"""
        if session_id not in self.conversation_memory:
            return ""
        
        recent_turns = self.conversation_memory[session_id][-last_n:]
        context_parts = []
        
        for turn in recent_turns:
            context_parts.append(f"Human: {turn['message']}")
            context_parts.append(f"Assistant: {turn['response']}")
        
        return '\n'.join(context_parts)
    
    async def store_finding_context(self, file_path: str, finding_context: Dict[str, Any]) -> None:
        """Store context about findings in a file"""
        self.finding_memory[file_path] = finding_context
    
    async def get_finding_context(self, file_path: str) -> Dict[str, Any]:
        """Get previous finding context for a file"""
        return self.finding_memory.get(file_path, {})
    
    async def store_cross_file_relationship(self, 
                                          symbol: str,
                                          relationships: List[Dict[str, Any]]) -> None:
        """Store cross-file relationships for a symbol"""
        self.cross_file_memory[symbol] = relationships
    
    async def get_cross_file_relationships(self, symbol: str) -> List[Dict[str, Any]]:
        """Get cross-file relationships for a symbol"""
        return self.cross_file_memory.get(symbol, [])
    
    async def store_directory_summary(self, directory: str, summary: str) -> None:
        """Store summary for a directory"""
        self.summary_memory[directory] = {
            'summary': summary,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def get_directory_summary(self, directory: str) -> Optional[str]:
        """Get summary for a directory"""
        summary_data = self.summary_memory.get(directory)
        return summary_data['summary'] if summary_data else None
    
    async def save_memory(self) -> None:
        """Persist memory to disk"""
        memory_data = {
            'conversation_memory': self.conversation_memory,
            'finding_memory': self.finding_memory,
            'cross_file_memory': self.cross_file_memory,
            'summary_memory': self.summary_memory
        }
        
        memory_file = self.storage_path / "memory.json"
        with open(memory_file, 'w') as f:
            json.dump(memory_data, f, indent=2)
    
    async def load_memory(self) -> None:
        """Load memory from disk"""
        memory_file = self.storage_path / "memory.json"
        
        if memory_file.exists():
            try:
                with open(memory_file, 'r') as f:
                    memory_data = json.load(f)
                
                self.conversation_memory = memory_data.get('conversation_memory', {})
                self.finding_memory = memory_data.get('finding_memory', {})
                self.cross_file_memory = memory_data.get('cross_file_memory', {})
                self.summary_memory = memory_data.get('summary_memory', {})
                
            except Exception as e:
                print(f"Error loading memory: {e}")
    
    async def clear_memory(self, memory_type: str = 'all') -> None:
        """Clear specific or all memory"""
        if memory_type == 'all' or memory_type == 'conversation':
            self.conversation_memory = {}
        if memory_type == 'all' or memory_type == 'finding':
            self.finding_memory = {}
        if memory_type == 'all' or memory_type == 'cross_file':
            self.cross_file_memory = {}
        if memory_type == 'all' or memory_type == 'summary':
            self.summary_memory = {}