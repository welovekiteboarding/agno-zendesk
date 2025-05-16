"""
AstraDB RAG Integration for the Agno API Server

This module provides the integration between the existing Agno API server 
and AstraDB for Retrieval Augmented Generation (RAG).
"""

print("[DEBUG] Loading astradb_rag.py...")
import os
import logging
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

# For AstraDB connection
from astrapy.db import AstraDB

# For OpenAI embeddings
import openai

# Import the Agno agent registry to modify existing agents
from api.routes.agno_agent_chat import get_session

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("astradb_rag")

# Configuration from environment
ASTRA_ENDPOINT = os.getenv("ASTRA_ENDPOINT")
ASTRA_TOKEN = os.getenv("ASTRA_TOKEN")
ASTRA_COLLECTION = os.getenv("ASTRA_COLLECTION", "ss_guide")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configure OpenAI
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


async def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding for the given text using OpenAI.
    
    Args:
        text: The text to generate an embedding for
        
    Returns:
        The embedding as a list of floats
    """
    try:
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        response = await client.embeddings.create(
            input=text, 
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        return []


async def search_astradb(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search AstraDB for relevant documents based on the query.
    This is a READ-ONLY operation that doesn't modify the database.
    
    Args:
        query: The search query
        limit: Number of results to return
        
    Returns:
        List of matching documents with similarity scores
    """
    # Get AstraDB configuration
    if not all([ASTRA_ENDPOINT, ASTRA_TOKEN, ASTRA_COLLECTION, OPENAI_API_KEY]):
        logger.error("Missing required environment variables for AstraDB RAG")
        return []
    
    try:
        # Generate embedding for the query
        logger.info(f"Generating embedding for query: '{query}'")
        query_embedding = await generate_embedding(query)
        
        if not query_embedding:
            logger.error("Failed to generate embedding")
            return []
        
        # Connect to AstraDB
        logger.info("Connecting to AstraDB...")
        db = AstraDB(
            token=ASTRA_TOKEN,
            api_endpoint=ASTRA_ENDPOINT
        )
        
        # Get the collection
        collection = db.collection(ASTRA_COLLECTION)
        
        # Perform vector search (READ-ONLY)
        logger.info("Performing vector search...")
        results = collection.vector_find(
            vector=query_embedding,
            limit=limit
        )
        
        results_list = list(results)
        logger.info(f"Found {len(results_list)} matching documents")
        return results_list
        
    except Exception as e:
        logger.error(f"Error during AstraDB search: {str(e)}")
        return []


def format_results(results: List[Dict[str, Any]]) -> str:
    """
    Format search results into a readable string.
    
    Args:
        results: List of document results from AstraDB
        
    Returns:
        Formatted results as a string
    """
    if not results:
        return "No relevant information found in the knowledge base."
    
    formatted_text = "### Relevant Information from Knowledge Base\n\n"
    
    for i, doc in enumerate(results, 1):
        # Extract content and metadata
        content = doc.get('text', '')
        doc_id = doc.get('_id', f"Document {i}")
        similarity = doc.get('$similarity', 0.0)
        
        formatted_text += f"**Source #{i}** (Relevance: {similarity:.4f})\n"
        formatted_text += f"{content}\n\n"
    
    return formatted_text


async def enhance_response_with_rag(session_id: str, user_message: str) -> Optional[str]:
    """
    Enhance the agent's response with RAG before generating a response.
    
    Args:
        session_id: The session ID
        user_message: The user's message
        
    Returns:
        The context from RAG to prepend to the agent's prompt
    """
    try:
        # Check if AstraDB RAG is configured
        if not all([ASTRA_ENDPOINT, ASTRA_TOKEN, ASTRA_COLLECTION, OPENAI_API_KEY]):
            logger.warning("AstraDB RAG is not configured, skipping")
            return None
        
        # Get session
        session = get_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return None
        
        # Search AstraDB for relevant documents
        results = await search_astradb(user_message)
        
        # Format results if any
        if results:
            context = format_results(results)
            logger.info(f"Enhanced response with RAG context for session {session_id}")
            
            # Check if we need to add the context to the session for the agent
            if 'context' not in session:
                session['context'] = []
            
            # Update session context with the new RAG context
            session['context'].append({
                "type": "rag",
                "content": context
            })
            
            return context
        
        return None
    
    except Exception as e:
        logger.error(f"Error enhancing response with RAG: {str(e)}")
        return None


# Patch the Agno agent's chat route to include RAG
from fastapi import Request
from api.routes.agno_agent_chat import router, chat

# Store the original chat function
original_chat = chat

# Override the chat function to include RAG
async def rag_enhanced_chat(request: Request):
    """
    Enhanced chat function that includes RAG before generating a response.
    """
    # Get the request body
    body = await request.json()
    
    # Extract session_id and user_message
    session_id = body.get("session_id")
    user_message = body.get("user_message")
    
    # Enhance with RAG
    await enhance_response_with_rag(session_id, user_message)
    
    # Call the original chat function
    return await original_chat(request)

# Replace the original chat function with the enhanced one
chat = rag_enhanced_chat

print("[DEBUG] AstraDB RAG integration initialized and registered with API routes")
