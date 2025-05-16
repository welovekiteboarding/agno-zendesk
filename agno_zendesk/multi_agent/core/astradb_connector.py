"""
AstraDB Connector for Multi-Agent RAG System

This module provides the integration with AstraDB for the multi-agent RAG system,
focusing on vector search capabilities across collections.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import asyncio
import json
from datetime import datetime

# For AstraDB connection
from astrapy.db import AstraDB

# For OpenAI embedding generation
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("astradb_connector")


class AstraDBConnector:
    """
    Connector for AstraDB vector database integration.
    Handles connection management, vector search, and result formatting.
    """
    
    def __init__(self, 
                 endpoint: Optional[str] = None, 
                 token: Optional[str] = None,
                 namespace: str = "default"):
        """
        Initialize the AstraDB connector.
        
        Args:
            endpoint: AstraDB API endpoint (defaults to env var ASTRA_ENDPOINT)
            token: AstraDB API token (defaults to env var ASTRA_TOKEN)
            namespace: Namespace for collections (defaults to "default")
        """
        self.endpoint = endpoint or os.getenv("ASTRA_ENDPOINT")
        self.token = token or os.getenv("ASTRA_TOKEN")
        self.namespace = namespace
        
        if not self.endpoint or not self.token:
            raise ValueError("AstraDB endpoint and token must be provided")
        
        self.db = None
        self.collections_cache = {}
        
    async def connect(self) -> bool:
        """
        Connect to AstraDB.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to AstraDB at {self.endpoint}")
            self.db = AstraDB(
                token=self.token,
                api_endpoint=self.endpoint
            )
            # Test connection
            collections = self.db.get_collections()
            logger.info(f"Successfully connected to AstraDB. Available collections: {collections}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to AstraDB: {str(e)}")
            return False
    
    async def get_collection(self, collection_name: str):
        """
        Get an AstraDB collection, using cache if available.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            AstraDB collection object
        """
        if not self.db:
            await self.connect()
            
        if collection_name in self.collections_cache:
            return self.collections_cache[collection_name]
        
        try:
            # Fix: The AstraDB.collection() method only takes one argument (collection_name)
            # The namespace is already specified in the AstraDB client configuration
            collection = self.db.collection(collection_name)
            self.collections_cache[collection_name] = collection
            return collection
        except Exception as e:
            logger.error(f"Failed to get collection {collection_name}: {str(e)}")
            raise
    
    @staticmethod
    async def generate_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
        """
        Generate an embedding vector for the given text using OpenAI.
        
        Args:
            text: Text to generate embedding for
            model: OpenAI embedding model to use
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text:
            raise ValueError("Cannot generate embedding for empty text")
        
        try:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
                
            client = openai.AsyncOpenAI(api_key=openai_api_key)
            response = await client.embeddings.create(
                input=text,
                model=model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    @staticmethod
    def calculate_keyword_score(text: str, query: str) -> float:
        """
        Calculate a keyword-based relevance score.
        Matching the approach from the other widget implementation.
        
        Args:
            text: Document text to score
            query: Query to match against
            
        Returns:
            Keyword match score between 0 and 1
        """
        if not text or not query:
            return 0.0
            
        normalized_text = text.lower()
        keywords = query.lower().split()
        
        # Match the approach from the other implementation
        # Each keyword match adds 0.25 to the score
        score = 0.0
        for keyword in keywords:
            if keyword in normalized_text:
                score += 0.25
        
        # Cap the score at 1.0
        return min(score, 1.0)
    
    async def vector_search(self, collection_name: str, query: str, limit: int = 3, similarity_threshold: float = 0.5, use_hybrid_search: bool = True) -> List[Dict[str, Any]]:
        """
        Perform vector search in the specified collection using hybrid search approach.
        
        Args:
            collection_name: Name of the collection to search
            query: Query string
            query: Query string to search for
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0-1) to include in results
            use_hybrid_search: Whether to use hybrid search (vector + keyword)
            
        Returns:
            List of matching documents with similarity scores
        """
        try:
            # Generate embedding for the query
            logger.info(f"Generating embedding for query: {query}")
            embedding = await self.generate_embedding(query)
            
            # Get the collection
            collection = await self.get_collection(collection_name)
            
            # Perform vector search
            logger.info(f"Performing vector search in collection {collection_name}")
            results = collection.vector_find(
                vector=embedding,
                limit=limit * 4  # Get more results for hybrid re-ranking and better coverage
            )
            
            # Log the query that was used
            logger.info(f"Query: '{query}' searching in collection: {collection_name}")
            
            # Convert to list and add metadata
            result_list = list(results)
            logger.info(f"Found {len(result_list)} vector matches")
            
            if not result_list:
                return []
                
            # Apply hybrid search if enabled
            if use_hybrid_search:
                hybrid_results = []
                for doc in result_list:
                    # Get vector similarity score
                    vector_score = doc.get('$similarity', 0)
                    
                    # Calculate keyword score
                    content = doc.get('text', '') or doc.get('content', '')
                    keyword_score = self.calculate_keyword_score(content, query)
                    
                    # Combine scores for hybrid ranking - match the other implementation
                    # Add full keyword score to vector score instead of weighted approach
                    hybrid_score = vector_score + keyword_score
                    
                    # Add hybrid score to document
                    doc_copy = doc.copy()
                    doc_copy['$similarity'] = hybrid_score
                    doc_copy['$vector_score'] = vector_score
                    doc_copy['$keyword_score'] = keyword_score
                    
                    hybrid_results.append(doc_copy)
                
                # Sort by hybrid score
                result_list = sorted(hybrid_results, key=lambda x: x.get('$similarity', 0), reverse=True)
            
            # Filter by similarity threshold and limit results
            filtered_results = [
                doc for doc in result_list 
                if doc.get('$similarity', 0) >= similarity_threshold
            ][:limit]
            
            logger.info(f"Returning {len(filtered_results)} results after filtering")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
            raise
    
    async def multi_collection_search(self,
                                     collection_names: List[str],
                                     query: str,
                                     limit_per_collection: int = 3,
                                     similarity_threshold: float = 0.5,
                                     max_results: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform vector search across multiple collections.
        
        Args:
            collection_names: List of collection names to search
            query: Query string to search for
            limit_per_collection: Maximum number of results per collection
            similarity_threshold: Minimum similarity score to include in results
            
        Returns:
            Dictionary mapping collection names to search results
        """
        results = {}
        tasks = []
        
        # Create async tasks for each collection search
        for collection_name in collection_names:
            task = asyncio.create_task(
                self.vector_search(
                    collection_name=collection_name,
                    query=query,
                    limit=limit_per_collection,
                    similarity_threshold=similarity_threshold,
                    use_hybrid_search=True
                )
            )
            tasks.append((collection_name, task))
        
        # Wait for all searches to complete
        for collection_name, task in tasks:
            try:
                collection_results = await task
                # Log the first result's content for debugging
                if collection_results and len(collection_results) > 0:
                    content = collection_results[0].get('text', '') or collection_results[0].get('content', '')
                    similarity = collection_results[0].get('$similarity', 0)
                    logger.info(f"Collection {collection_name} top result: Similarity={similarity:.4f}, Content preview: {content[:200]}...")
                    
                if collection_results:
                    results[collection_name] = collection_results
                    # Log the number of results and their similarity scores
                    similarities = [doc.get('$similarity', 0) for doc in collection_results]
                    logger.info(f"Collection {collection_name}: Found {len(collection_results)} results with similarities: {similarities}")
            except Exception as e:
                logger.error(f"Error searching collection {collection_name}: {str(e)}")
                results[collection_name] = []
        
        return results
    
    def format_results_with_citations(self, 
                                     results: Dict[str, List[Dict[str, Any]]],
                                     include_metadata: bool = True) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Format search results with citations for use in agent context.
        
        Args:
            results: Results from multi_collection_search
            include_metadata: Whether to include metadata in the formatted results
            
        Returns:
            Tuple of (formatted_text, citation_list)
        """
        if not results:
            return "", []
            
        formatted_texts = []
        citation_list = []
        citation_id = 1
        
        for collection_name, collection_results in results.items():
            for doc in collection_results:
                # Extract content and metadata
                content = doc.get('text', '') or doc.get('content', '')
                similarity = doc.get('$similarity', 0)
                
                # Determine relevance tier
                relevance = "High" if similarity > 0.85 else "Medium" if similarity > 0.75 else "Low"
                
                # Create citation ID
                citation = f"[{citation_id}]"
                
                # Format citation text
                citation_text = f"{citation} (Collection: {collection_name}, Relevance: {relevance})\n{content}\n"
                formatted_texts.append(citation_text)
                
                # Build citation metadata
                citation_metadata = {
                    "id": citation_id,
                    "collection": collection_name,
                    "similarity": similarity,
                    "relevance": relevance,
                    "document_id": doc.get('_id', ''),
                }
                
                # Add additional metadata if requested
                if include_metadata:
                    # Copy all metadata except the content and embedding
                    metadata = {k: v for k, v in doc.items() 
                               if k not in ('text', 'content', 'embedding', '$vector')}
                    citation_metadata["metadata"] = metadata
                
                citation_list.append(citation_metadata)
                citation_id += 1
        
        # Join all formatted texts with separators
        formatted_text = "\n---\n".join(formatted_texts)
        
        # Add citation policy
        citation_ids = [f"[{i}]" for i in range(1, citation_id)]
        citation_policy = (
            f"\n\nCitation Policy:\n"
            f"- Every statement must reference at least one citation\n"
            f"- Only use citations {', '.join(citation_ids)}\n"
            f"- If information is not found in citations, clearly indicate this\n"
        )
        
        return formatted_text + citation_policy, citation_list


# Singleton instance of the AstraDB connector
_connector_instance = None

async def get_astradb_connector() -> AstraDBConnector:
    """
    Get the singleton instance of the AstraDB connector.
    
    Returns:
        AstraDBConnector instance
    """
    global _connector_instance
    
    if _connector_instance is None:
        _connector_instance = AstraDBConnector()
        await _connector_instance.connect()
        
    return _connector_instance
