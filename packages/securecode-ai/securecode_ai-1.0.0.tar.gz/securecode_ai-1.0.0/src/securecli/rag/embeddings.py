"""
RAG (Retrieval Augmented Generation) system for SecureCLI
Handles document embedding, vector storage, and semantic retrieval for cross-file analysis
"""

import os
import asyncio
import hashlib
import json
import warnings
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Suppress all warnings for clean output
os.environ['PYTHONWARNINGS'] = 'ignore'
warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")

import tiktoken
try:
    from langchain_community.embeddings import OpenAIEmbeddings
    OPENAI_EMBEDDINGS_AVAILABLE = True
except ImportError:
    OPENAI_EMBEDDINGS_AVAILABLE = False

try:
    from langchain_community.embeddings import OllamaEmbeddings, HuggingFaceEmbeddings
    LOCAL_EMBEDDINGS_AVAILABLE = True
except ImportError:
    LOCAL_EMBEDDINGS_AVAILABLE = False

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import FAISS, Chroma
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

from ..schemas.findings import FileInfo


@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata"""
    content: str
    file_path: str
    start_line: int
    end_line: int
    chunk_id: str
    language: Optional[str]
    symbols: List[str]  # Functions, classes, variables
    imports: List[str]
    hash: str


class CodeEmbeddings:
    """Handles code-aware embeddings and chunking"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.chunk_size = config.get('rag.chunk_size', 1000)
        self.chunk_overlap = config.get('rag.chunk_overlap', 200)
        self.max_tokens = config.get('rag.max_tokens', 8000)
        
        # Initialize embeddings based on provider configuration
        self.embeddings = self._create_embeddings(config)
        
        # Initialize text splitter with code awareness
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=[
                # Code-specific separators
                '\nclass ', '\ndef ', '\nfunction ', '\ncontract ',
                '\n\n', '\n', ' ', ''
            ],
            keep_separator=True
        )
    
    def _create_embeddings(self, config: Dict[str, Any]):
        """Create embeddings based on provider configuration"""
        llm_provider = config.get('llm', {}).get('provider', 'auto')
        local_model_enabled = config.get('local_model', {}).get('enabled', False)
        
        # Use local embeddings if local provider is configured
        if llm_provider == 'local' or local_model_enabled:
            if LOCAL_EMBEDDINGS_AVAILABLE:
                local_config = config.get('local_model', {})
                engine = local_config.get('engine', 'ollama')
                
                if engine == 'ollama':
                    try:
                        # Use Ollama embeddings with a smaller model for embeddings
                        return OllamaEmbeddings(
                            base_url=local_config.get('base_url', 'http://localhost:11434'),
                            model='nomic-embed-text'  # Use a lightweight embedding model
                        )
                    except Exception as e:
                        print(f"Warning: Ollama embeddings not available, using HuggingFace: {e}")
                        
                # Fallback to HuggingFace embeddings for local processing
                try:
                    return HuggingFaceEmbeddings(
                        model_name='sentence-transformers/all-MiniLM-L6-v2'
                    )
                except Exception as e:
                    print(f"Warning: HuggingFace embeddings not available, using simple embeddings: {e}")
                    # Return a simple mock embeddings for local-only operation
                    return SimpleLocalEmbeddings()
            else:
                print("Info: Using simplified embeddings for local-only operation")
                return SimpleLocalEmbeddings()
        
        # Default to OpenAI embeddings
        if OPENAI_EMBEDDINGS_AVAILABLE:
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                return OpenAIEmbeddings(
                    model=config.get('rag.embedding_model', 'text-embedding-ada-002')
                )
            else:
                print("Warning: OpenAI API key not found, using simple embeddings")
                return SimpleLocalEmbeddings()
        else:
            print("Info: Using simplified embeddings for local operation")
            return SimpleLocalEmbeddings()


class SimpleLocalEmbeddings:
    """Simple local embeddings for when other options are not available"""
    
    def embed_documents(self, texts):
        """Simple hash-based embeddings for local operation"""
        import hashlib
        import numpy as np
        
        embeddings = []
        for text in texts:
            # Create a simple hash-based embedding
            hash_obj = hashlib.md5(text.encode())
            hash_bytes = hash_obj.digest()
            # Convert to a simple vector (not as good as real embeddings but works)
            embedding = [float(b) / 255.0 for b in hash_bytes[:16]]  # 16-dimensional
            # Pad to 384 dimensions (common size)
            embedding.extend([0.0] * (384 - len(embedding)))
            embeddings.append(embedding)
        return embeddings
    
    def embed_query(self, text):
        """Embed a single query"""
        return self.embed_documents([text])[0]
        
        # Token encoder for accurate counting
        self.encoder = tiktoken.get_encoding("cl100k_base")
    
    async def chunk_files(self, files: List[FileInfo]) -> List[CodeChunk]:
        """Chunk code files into semantically meaningful pieces"""
        chunks = []
        
        for file_info in files:
            if file_info.file_type == 'code' and file_info.content:
                file_chunks = await self._chunk_single_file(file_info)
                chunks.extend(file_chunks)
        
        return chunks
    
    async def _chunk_single_file(self, file_info: FileInfo) -> List[CodeChunk]:
        """Chunk a single file with language-aware splitting"""
        chunks = []
        
        # Use language-specific chunking if available
        if file_info.language == 'python':
            chunks = self._chunk_python_file(file_info)
        elif file_info.language == 'javascript':
            chunks = self._chunk_javascript_file(file_info)
        elif file_info.language == 'solidity':
            chunks = self._chunk_solidity_file(file_info)
        else:
            # Generic chunking
            chunks = self._chunk_generic_file(file_info)
        
        return chunks
    
    def _chunk_python_file(self, file_info: FileInfo) -> List[CodeChunk]:
        """Python-aware chunking"""
        chunks = []
        lines = file_info.content.split('\n')
        
        current_chunk = []
        current_start_line = 1
        current_symbols = []
        current_imports = []
        
        in_class = False
        in_function = False
        indent_level = 0
        
        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()
            
            # Track imports
            if stripped.startswith(('import ', 'from ')):
                current_imports.append(stripped)
            
            # Track symbols
            if stripped.startswith('class '):
                current_symbols.append(self._extract_python_class_name(stripped))
                in_class = True
                indent_level = len(line) - len(line.lstrip())
            elif stripped.startswith('def '):
                current_symbols.append(self._extract_python_function_name(stripped))
                in_function = True
                indent_level = len(line) - len(line.lstrip())
            
            current_chunk.append(line)
            
            # Check if we should create a chunk
            chunk_content = '\n'.join(current_chunk)
            if self._should_split_chunk(chunk_content):
                chunk = self._create_code_chunk(
                    content=chunk_content,
                    file_info=file_info,
                    start_line=current_start_line,
                    end_line=line_num,
                    symbols=current_symbols.copy(),
                    imports=current_imports.copy()
                )
                chunks.append(chunk)
                
                # Reset for next chunk
                current_chunk = []
                current_start_line = line_num + 1
                current_symbols = []
                # Keep imports for context
        
        # Add final chunk if any content remains
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            chunk = self._create_code_chunk(
                content=chunk_content,
                file_info=file_info,
                start_line=current_start_line,
                end_line=len(lines),
                symbols=current_symbols,
                imports=current_imports
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_javascript_file(self, file_info: FileInfo) -> List[CodeChunk]:
        """JavaScript-aware chunking"""
        # Similar implementation to Python but with JS-specific patterns
        return self._chunk_generic_file(file_info)
    
    def _chunk_solidity_file(self, file_info: FileInfo) -> List[CodeChunk]:
        """Solidity-aware chunking"""
        chunks = []
        lines = file_info.content.split('\n')
        
        current_chunk = []
        current_start_line = 1
        current_symbols = []
        current_imports = []
        
        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()
            
            # Track imports
            if stripped.startswith('import '):
                current_imports.append(stripped)
            
            # Track contracts and functions
            if stripped.startswith('contract '):
                current_symbols.append(self._extract_solidity_contract_name(stripped))
            elif 'function ' in stripped:
                current_symbols.append(self._extract_solidity_function_name(stripped))
            
            current_chunk.append(line)
            
            # Split on contract boundaries or when chunk gets too large
            if (stripped.startswith('contract ') and current_chunk) or \
               self._should_split_chunk('\n'.join(current_chunk)):
                
                if len(current_chunk) > 1:  # Don't create empty chunks
                    chunk = self._create_code_chunk(
                        content='\n'.join(current_chunk[:-1]),
                        file_info=file_info,
                        start_line=current_start_line,
                        end_line=line_num - 1,
                        symbols=current_symbols.copy(),
                        imports=current_imports.copy()
                    )
                    chunks.append(chunk)
                
                # Start new chunk
                current_chunk = [line]
                current_start_line = line_num
                current_symbols = []
        
        # Add final chunk
        if current_chunk:
            chunk = self._create_code_chunk(
                content='\n'.join(current_chunk),
                file_info=file_info,
                start_line=current_start_line,
                end_line=len(lines),
                symbols=current_symbols,
                imports=current_imports
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_generic_file(self, file_info: FileInfo) -> List[CodeChunk]:
        """Generic file chunking using RecursiveCharacterTextSplitter"""
        chunks = []
        
        # Split text into chunks
        text_chunks = self.text_splitter.split_text(file_info.content)
        
        lines = file_info.content.split('\n')
        current_line = 1
        
        for i, chunk_content in enumerate(text_chunks):
            # Calculate line numbers for this chunk
            chunk_lines = chunk_content.count('\n') + 1
            start_line = current_line
            end_line = current_line + chunk_lines - 1
            
            chunk = self._create_code_chunk(
                content=chunk_content,
                file_info=file_info,
                start_line=start_line,
                end_line=end_line,
                symbols=[],
                imports=[]
            )
            chunks.append(chunk)
            
            current_line = end_line + 1
        
        return chunks
    
    def _should_split_chunk(self, content: str) -> bool:
        """Determine if chunk should be split based on size"""
        token_count = len(self.encoder.encode(content))
        return token_count > self.chunk_size
    
    def _create_code_chunk(
        self,
        content: str,
        file_info: FileInfo,
        start_line: int,
        end_line: int,
        symbols: List[str],
        imports: List[str]
    ) -> CodeChunk:
        """Create a CodeChunk object"""
        
        # Generate chunk ID
        chunk_id = hashlib.md5(
            f"{file_info.path}:{start_line}:{end_line}:{content}".encode()
        ).hexdigest()[:12]
        
        # Generate content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        return CodeChunk(
            content=content,
            file_path=file_info.path,
            start_line=start_line,
            end_line=end_line,
            chunk_id=chunk_id,
            language=file_info.language,
            symbols=symbols,
            imports=imports,
            hash=content_hash
        )
    
    def _extract_python_class_name(self, line: str) -> str:
        """Extract class name from Python class definition"""
        parts = line.strip().split()
        if len(parts) >= 2:
            class_part = parts[1]
            return class_part.split('(')[0].rstrip(':')
        return 'UnknownClass'
    
    def _extract_python_function_name(self, line: str) -> str:
        """Extract function name from Python function definition"""
        parts = line.strip().split()
        if len(parts) >= 2:
            func_part = parts[1]
            return func_part.split('(')[0]
        return 'unknown_function'
    
    def _extract_solidity_contract_name(self, line: str) -> str:
        """Extract contract name from Solidity contract definition"""
        parts = line.strip().split()
        if len(parts) >= 2:
            return parts[1].split()[0]
        return 'UnknownContract'
    
    def _extract_solidity_function_name(self, line: str) -> str:
        """Extract function name from Solidity function definition"""
        if 'function ' in line:
            start = line.find('function ') + 9
            end = line.find('(', start)
            if end > start:
                return line[start:end].strip()
        return 'unknown_function'
    
    async def embed_chunks(self, chunks: List[CodeChunk]) -> List[Tuple[CodeChunk, List[float]]]:
        """Generate embeddings for code chunks"""
        embedded_chunks = []
        
        # Prepare texts for embedding
        texts = []
        for chunk in chunks:
            # Create enriched text for embedding
            enriched_text = self._create_embedding_text(chunk)
            texts.append(enriched_text)
        
        # Generate embeddings in batches
        batch_size = 100
        embeddings_list = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = await self.embeddings.aembed_documents(batch_texts)
            embeddings_list.extend(batch_embeddings)
        
        # Combine chunks with embeddings
        for chunk, embedding in zip(chunks, embeddings_list):
            embedded_chunks.append((chunk, embedding))
        
        return embedded_chunks
    
    def _create_embedding_text(self, chunk: CodeChunk) -> str:
        """Create enriched text for embedding"""
        text_parts = []
        
        # Add file path context
        text_parts.append(f"File: {chunk.file_path}")
        
        # Add language context
        if chunk.language:
            text_parts.append(f"Language: {chunk.language}")
        
        # Add symbol context
        if chunk.symbols:
            text_parts.append(f"Symbols: {', '.join(chunk.symbols)}")
        
        # Add import context
        if chunk.imports:
            text_parts.append(f"Imports: {', '.join(chunk.imports[:5])}")  # Limit imports
        
        # Add line range
        text_parts.append(f"Lines: {chunk.start_line}-{chunk.end_line}")
        
        # Add the actual content
        text_parts.append("Content:")
        text_parts.append(chunk.content)
        
        return '\n'.join(text_parts)


# Create alias for backwards compatibility
CodeEmbedder = CodeEmbeddings