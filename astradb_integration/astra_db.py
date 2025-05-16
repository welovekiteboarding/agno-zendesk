"""
AstraDB vector database implementation for Agno RAG

This implementation adapts Agno's Cassandra vector database to work with DataStax AstraDB.
"""

import asyncio
from typing import Any, Dict, List, Optional, Union

from agno.document import Document
from agno.embedder import Embedder
from agno.utils.log import log_debug, log_info
from agno.vectordb.base import VectorDb

# Import for astrapy 0.7.7
from astrapy.db import AstraDB, AstraDBCollection

class AstraDb(VectorDb):
    """
    AstraDB vector database implementation for Agno.
    
    This implementation uses DataStax's AstraDB for vector storage and retrieval.
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
    ) -> None:
        """
        Initialize AstraDB vector database.
        
        Args:
            collection_name: Name of the collection to use
            api_endpoint: The AstraDB API endpoint
            token: The AstraDB API token
            namespace: The namespace to use (default: "default")
            embedder: Embedder to use for generating embeddings
            dimensions: Dimensions of the embedding vectors
            similarity_metric: Similarity metric to use (default: "cosine")
        """
        if not collection_name:
            raise ValueError("Collection name must be provided.")
            
        if not api_endpoint:
            raise ValueError("API endpoint must be provided.")
            
        if not token:
            raise ValueError("Token must be provided.")
            
        if embedder is None:
            from agno.embedder.openai import OpenAIEmbedder
            embedder = OpenAIEmbedder()
            log_info("Embedder not provided, using OpenAIEmbedder as default.")
            
        self.collection_name = collection_name
        self.api_endpoint = api_endpoint
        self.token = token
        self.namespace = namespace
        self.embedder = embedder
        self.dimensions = dimensions
        self.similarity_metric = similarity_metric
        
        # Initialize the connection
        self.astra_db = AstraPyDB(api_endpoint=api_endpoint, token=token)
        
        # Create namespace if it doesn't exist
        try:
            self.astra_db.create_namespace(namespace)
            log_info(f"Created namespace: {namespace}")
        except CreateNamespaceError:
            log_info(f"Namespace {namespace} already exists.")
            
        # Initialize or get the collection
        self.initialize_collection()
        
    def initialize_collection(self) -> None:
        """Initialize or get the AstraDB collection."""
        log_debug(f"Initializing or getting collection: {self.collection_name}")
        
        collection_info = self.astra_db.get_collection(
            collection_name=self.collection_name,
            namespace=self.namespace
        )
        
        if collection_info:
            self.collection = collection_info
            log_debug(f"Found existing collection: {self.collection_name}")
        else:
            log_debug(f"Creating new collection: {self.collection_name}")
            self.collection = self.astra_db.create_collection(
                collection_name=self.collection_name,
                namespace=self.namespace,
                dimension=self.dimensions,
                metric=self.similarity_metric
            )
            
    def _document_to_astra_doc(self, document: Document) -> Dict[str, Any]:
        """Convert an Agno Document to AstraDB document format."""
        return {
            "_id": document.id,
            "content": document.content,
            "metadata": document.meta_data,
            "name": document.name or document.id,
            "vector": document.embedding
        }
        
    def _astra_doc_to_document(self, astra_doc: Dict[str, Any]) -> Document:
        """Convert an AstraDB document to Agno Document format."""
        return Document(
            id=astra_doc.get("_id"),
            content=astra_doc.get("content", ""),
            meta_data=astra_doc.get("metadata", {}),
            embedding=astra_doc.get("vector", []),
            name=astra_doc.get("name", "")
        )
        
    def create(self) -> None:
        """Create the collection in AstraDB for storing vectors and metadata."""
        # Collection is automatically created in __init__
        pass
        
    async def async_create(self) -> None:
        """Create the collection asynchronously."""
        await asyncio.to_thread(self.create)
        
    def doc_exists(self, document: Document) -> bool:
        """Check if a document exists by ID."""
        result = self.collection.find_one({"_id": document.id})
        return result is not None
        
    async def async_doc_exists(self, document: Document) -> bool:
        """Check if a document exists asynchronously."""
        return await asyncio.to_thread(self.doc_exists, document)
        
    def name_exists(self, name: str) -> bool:
        """Check if a document exists by name."""
        result = self.collection.find_one({"name": name})
        return result is not None
        
    async def async_name_exists(self, name: str) -> bool:
        """Check if a document with given name exists asynchronously."""
        return await asyncio.to_thread(self.name_exists, name)
        
    def id_exists(self, id: str) -> bool:
        """Check if a document exists by ID."""
        result = self.collection.find_one({"_id": id})
        return result is not None
        
    def insert(self, documents: List[Document], filters: Optional[Dict[str, Any]] = None) -> None:
        """Insert documents into AstraDB."""
        log_debug(f"AstraDB: Inserting {len(documents)} Documents to the collection {self.collection_name}")
        
        for doc in documents:
            # Ensure document has an embedding
            doc.embed(embedder=self.embedder)
            
            # Convert to AstraDB format
            astra_doc = self._document_to_astra_doc(doc)
            
            # Insert document
            self.collection.insert_one(astra_doc)
            
    async def async_insert(self, documents: List[Document], filters: Optional[Dict[str, Any]] = None) -> None:
        """Insert documents asynchronously."""
        await asyncio.to_thread(self.insert, documents, filters)
        
    def upsert(self, documents: List[Document], filters: Optional[Dict[str, Any]] = None) -> None:
        """Insert or update documents."""
        log_debug(f"AstraDB: Upserting {len(documents)} Documents to the collection {self.collection_name}")
        
        for doc in documents:
            # Ensure document has an embedding
            doc.embed(embedder=self.embedder)
            
            # Convert to AstraDB format
            astra_doc = self._document_to_astra_doc(doc)
            
            # Upsert document
            self.collection.upsert_one(astra_doc)
            
    async def async_upsert(self, documents: List[Document], filters: Optional[Dict[str, Any]] = None) -> None:
        """Upsert documents asynchronously."""
        await asyncio.to_thread(self.upsert, documents, filters)
        
    def search(self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Semantic search on document content."""
        log_debug(f"AstraDB: Performing Vector Search on {self.collection_name} with query {query}")
        return self.vector_search(query=query, limit=limit, filters=filters)
        
    async def async_search(
        self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search asynchronously."""
        return await asyncio.to_thread(self.search, query, limit, filters)
        
    def vector_search(
        self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Vector similarity search implementation."""
        # Generate embedding for the query
        query_embedding = self.embedder.get_embedding(query)
        
        # Prepare filter if provided
        filter_object = filters or {}
        
        # Perform vector search
        results = self.collection.vector_find(
            vector=query_embedding,
            limit=limit,
            filter=filter_object if filter_object else None
        )
        
        # Convert results to Documents
        documents = []
        for result in results:
            documents.append(self._astra_doc_to_document(result))
            
        return documents
        
    def drop(self) -> None:
        """Drop the collection in AstraDB."""
        log_debug(f"AstraDB: Dropping Collection {self.collection_name}")
        self.astra_db.delete_collection(
            collection_name=self.collection_name,
            namespace=self.namespace
        )
        
    async def async_drop(self) -> None:
        """Drop the collection asynchronously."""
        await asyncio.to_thread(self.drop)
        
    def exists(self) -> bool:
        """Check if the collection exists in AstraDB."""
        collection_info = self.astra_db.get_collection(
            collection_name=self.collection_name,
            namespace=self.namespace
        )
        return collection_info is not None
        
    async def async_exists(self) -> bool:
        """Check if collection exists asynchronously."""
        return await asyncio.to_thread(self.exists)
        
    def delete(self) -> bool:
        """Delete all documents in the collection."""
        log_debug(f"AstraDB: Clearing the collection {self.collection_name}")
        # AstraDB doesn't have a clear method, so we drop and recreate
        self.drop()
        self.initialize_collection()
        return True
        
    def count(self) -> int:
        """Get the number of documents in the collection."""
        # AstraDB doesn't provide a direct count method, so we have to estimate
        # This is not accurate, but provides a rough count
        results = self.collection.find({}, limit=1)
        if not results:
            return 0
        return 1  # If we get here, at least one document exists