"""
Document loader utility for AstraDB RAG implementation
"""

import os
import json
from typing import Dict, List, Optional, Union, Any

from agno.document import Document
from agno.embedder import Embedder
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.text import TextKnowledgeBase
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.knowledge.csv import CSVKnowledgeBase
from agno.knowledge.website import WebsiteKnowledgeBase

from astradb_integration import AstraDb

class DocumentLoader:
    """
    Utility class for loading documents into AstraDB for RAG
    """
    
    def __init__(
        self,
        collection_name: str,
        api_endpoint: str,
        token: str,
        namespace: str = "default",
        embedder: Optional[Embedder] = None,
        dimensions: int = 1536,
        similarity_metric: str = "cosine",
    ):
        """
        Initialize the document loader
        
        Args:
            collection_name: Name of the collection to use
            api_endpoint: The AstraDB API endpoint
            token: The AstraDB API token
            namespace: The namespace to use (default: "default")
            embedder: Embedder to use for generating embeddings
            dimensions: Dimensions of the embedding vectors
            similarity_metric: Similarity metric to use (default: "cosine")
        """
        if embedder is None:
            embedder = OpenAIEmbedder(id="text-embedding-3-small")
            
        self.embedder = embedder
        self.vector_db = AstraDb(
            collection_name=collection_name,
            api_endpoint=api_endpoint,
            token=token,
            namespace=namespace,
            embedder=embedder,
            dimensions=dimensions,
            similarity_metric=similarity_metric
        )
        
    def load_text_files(self, directory: str, recursive: bool = True, extension: str = ".txt") -> None:
        """
        Load text files from a directory
        
        Args:
            directory: Directory containing text files
            recursive: Whether to search recursively
            extension: File extension to filter by
        """
        texts = []
        file_paths = []
        
        # Walk through directory
        for root, _, files in os.walk(directory):
            if not recursive and root != directory:
                continue
                
            for file in files:
                if file.endswith(extension):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            text = f.read()
                            texts.append(text)
                            file_paths.append(file_path)
                    except Exception as e:
                        print(f"Error reading file {file_path}: {e}")
        
        # Create knowledge base and load documents
        knowledge_base = TextKnowledgeBase(
            texts=texts,
            vector_db=self.vector_db,
            metadata=[{"source": path} for path in file_paths]
        )
        
        knowledge_base.load()
        print(f"Loaded {len(texts)} text files into AstraDB")
        
    def load_pdf_files(self, directory: str, recursive: bool = True) -> None:
        """
        Load PDF files from a directory
        
        Args:
            directory: Directory containing PDF files
            recursive: Whether to search recursively
        """
        pdf_paths = []
        
        # Walk through directory
        for root, _, files in os.walk(directory):
            if not recursive and root != directory:
                continue
                
            for file in files:
                if file.endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    pdf_paths.append(file_path)
        
        # Create knowledge base and load documents
        knowledge_base = PDFKnowledgeBase(
            file_paths=pdf_paths,
            vector_db=self.vector_db
        )
        
        knowledge_base.load()
        print(f"Loaded {len(pdf_paths)} PDF files into AstraDB")
        
    def load_csv_files(self, directory: str, recursive: bool = True) -> None:
        """
        Load CSV files from a directory
        
        Args:
            directory: Directory containing CSV files
            recursive: Whether to search recursively
        """
        csv_paths = []
        
        # Walk through directory
        for root, _, files in os.walk(directory):
            if not recursive and root != directory:
                continue
                
            for file in files:
                if file.endswith('.csv'):
                    file_path = os.path.join(root, file)
                    csv_paths.append(file_path)
        
        # Create knowledge base and load documents
        knowledge_base = CSVKnowledgeBase(
            file_paths=csv_paths,
            vector_db=self.vector_db
        )
        
        knowledge_base.load()
        print(f"Loaded {len(csv_paths)} CSV files into AstraDB")
        
    def load_websites(self, urls: List[str]) -> None:
        """
        Load content from websites
        
        Args:
            urls: List of website URLs to crawl
        """
        # Create knowledge base and load documents
        knowledge_base = WebsiteKnowledgeBase(
            urls=urls,
            vector_db=self.vector_db
        )
        
        knowledge_base.load()
        print(f"Loaded content from {len(urls)} websites into AstraDB")
        
    def load_json(self, json_file: str, text_field: str = "text", metadata_fields: Optional[List[str]] = None) -> None:
        """
        Load documents from a JSON file
        
        Args:
            json_file: Path to JSON file
            text_field: Name of the field containing the text
            metadata_fields: Names of fields to include as metadata
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            texts = []
            metadata_list = []
            
            # Handle both array of objects and object with nested arrays
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict) and any(isinstance(v, list) for v in data.values()):
                # Find the first list in the dictionary
                for key, value in data.items():
                    if isinstance(value, list):
                        items = value
                        break
                else:
                    items = [data]
            else:
                items = [data]
                
            # Extract text and metadata
            for item in items:
                if text_field in item:
                    text = item[text_field]
                    texts.append(text)
                    
                    # Extract metadata
                    metadata = {}
                    if metadata_fields:
                        for field in metadata_fields:
                            if field in item and field != text_field:
                                metadata[field] = item[field]
                    
                    metadata_list.append(metadata)
            
            # Create knowledge base and load documents
            knowledge_base = TextKnowledgeBase(
                texts=texts,
                vector_db=self.vector_db,
                metadata=metadata_list
            )
            
            knowledge_base.load()
            print(f"Loaded {len(texts)} documents from JSON file into AstraDB")
            
        except Exception as e:
            print(f"Error loading JSON file {json_file}: {e}")
            
    def load_custom_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Load custom documents into AstraDB
        
        Args:
            documents: List of document dictionaries with 'content' and optional 'metadata'
        """
        doc_objects = []
        
        for doc in documents:
            if 'content' not in doc:
                print(f"Skipping document without 'content' field: {doc}")
                continue
                
            # Create Document object
            doc_object = Document(
                content=doc['content'],
                meta_data=doc.get('metadata', {}),
                name=doc.get('name', None)
            )
            
            doc_objects.append(doc_object)
            
        # Insert documents directly
        self.vector_db.insert(doc_objects)
        print(f"Loaded {len(doc_objects)} custom documents into AstraDB")