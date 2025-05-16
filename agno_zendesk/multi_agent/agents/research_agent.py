"""
Research Agent Implementation

This agent specializes in retrieving information from AstraDB collections
and preparing it for use by other agents in the system.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
import json
from datetime import datetime

from ..core.agent_interface import Agent, AgentContext
from ..core.astradb_connector import get_astradb_connector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("research_agent")


class ResearchAgent(Agent):
    """
    Agent specializing in research and information retrieval from AstraDB.
    Performs vector searches across collections and formats results for other agents.
    """
    
    def __init__(self, 
                 agent_id: str,
                 name: str,
                 description: str,
                 collections: List[str] = None,
                 model: Optional[str] = None,
                 similarity_threshold: float = 0.4,
                 max_results_per_collection: int = 3,
                 use_hybrid_search: bool = True):
        """
        Initialize the research agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            description: Detailed description of the agent's purpose
            collections: List of AstraDB collections to search
            model: Optional LLM model name
            similarity_threshold: Minimum similarity score (0-1) for results
            max_results_per_collection: Maximum results to return per collection
            use_hybrid_search: Whether to use hybrid search (vector + keyword)
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            role="research",
            model=model
        )
        
        # Set default collections if none provided
        if collections is None:
            self.collections = ["skysafari", "celestron_pdfs"]
        else:
            self.collections = collections
        self.similarity_threshold = similarity_threshold
        self.max_results_per_collection = max_results_per_collection
        self.use_hybrid_search = use_hybrid_search
        
    async def can_handle(self, context: AgentContext) -> bool:
        """
        Check if this agent can handle the given context.
        Research agent can handle any context with a query.
        
        Args:
            context: The agent context
            
        Returns:
            True if the agent can handle the context, False otherwise
        """
        return bool(context.query.strip())
    
    async def process(self, context: AgentContext) -> AgentContext:
        """
        Process the given context by searching AstraDB collections.
        
        Args:
            context: The agent context
            
        Returns:
            Updated context with search results
        """
        query = context.query
        logger.info(f"Research agent processing query: {query}")
        
        try:
            # Get the AstraDB connector
            connector = await get_astradb_connector()
            
            # Determine which collections to search
            collections_to_search = self.collections
            
            # If specific collections are requested in the context, use those instead
            if context.metadata.get("target_collections"):
                requested_collections = context.metadata.get("target_collections", [])
                # Use all collections specified by the leader agent - don't filter
                collections_to_search = requested_collections
                logger.info(f"Using requested collections: {collections_to_search}")
            
            # If no collections are available, report error
            if not collections_to_search:
                logger.error("No collections available to search")
                context.add_error(
                    self.agent_id,
                    "No collections available to search"
                )
                return context
            
            # Search across all specified collections
            search_results = await connector.multi_collection_search(
                collection_names=collections_to_search,
                query=query,
                limit_per_collection=self.max_results_per_collection,
                similarity_threshold=self.similarity_threshold
            )
            
            # Format results with citations
            formatted_context, citations = connector.format_results_with_citations(
                search_results, include_metadata=True
            )
            
            # Add context and citations to the result
            context.set_result("formatted_context", formatted_context)
            context.set_result("raw_search_results", search_results)
            
            # Add citations to the context
            for citation in citations:
                try:
                    # Get the collection and citation ID
                    collection = citation["collection"]
                    # Note: citation IDs are 1-indexed but collection results are 0-indexed
                    citation_index = citation["id"] - 1
                    
                    # Safely access the search results
                    if collection in search_results and citation_index < len(search_results[collection]):
                        doc = search_results[collection][citation_index]
                        content = doc.get("text", "") or doc.get("content", "")
                        
                        # Add the citation to the context
                        context.add_citation(
                            source=collection,
                            content=content,
                            metadata=citation
                        )
                    else:
                        logger.warning(f"Cannot find citation {citation['id']} in collection {collection}")
                except Exception as e:
                    logger.error(f"Error adding citation {citation}: {str(e)}")
                    # Continue processing other citations even if one fails
                    continue
            
            # Add memory entry for this operation
            context.update_memory({
                "agent": self.name,
                "action": "research",
                "collections_searched": collections_to_search,
                "citations_found": len(citations),
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Research completed successfully. Found {len(citations)} citations.")
            return context
            
        except Exception as e:
            logger.error(f"Error in research agent: {str(e)}")
            context.add_error(
                self.agent_id,
                f"Research failed: {str(e)}"
            )
            return context
