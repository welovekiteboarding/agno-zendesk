"""
FastAPI Server for Multi-Agent RAG System

This module implements a minimal FastAPI server that exposes the multi-agent RAG system
through a RESTful API for use by the frontend widget.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..core.system import get_multi_agent_system
from ..core.astradb_connector import get_astradb_connector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("multi_agent_api")

# Create FastAPI app
app = FastAPI(
    title="Agno Multi-Agent RAG API",
    description="API for the Agno Multi-Agent RAG widget",
    version="0.1.0"
)

# Add CORS middleware for Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set to specific Vercel domain
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Models for request and response
class QueryRequest(BaseModel):
    query: str = Field(..., description="The user query")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for continuing threads")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class QueryResponse(BaseModel):
    query: str = Field(..., description="The original query")
    response: str = Field(..., description="The generated response")
    conversation_id: str = Field(..., description="Conversation ID")
    citations: Optional[List[Dict[str, Any]]] = Field(None, description="Citations used in the response")
    processing_time: float = Field(..., description="Processing time in seconds")


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a query through the multi-agent system.
    This is the main endpoint for the widget to interact with.
    """
    logger.info(f"Received query: {request.query}")
    
    try:
        # Get the multi-agent system
        system = get_multi_agent_system()
        
        # Process the query
        start_time = datetime.now()
        result = await system.process_query(
            query=request.query,
            conversation_id=request.conversation_id,
            metadata=request.metadata
        )
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Format response for the widget
        response = {
            "query": request.query,
            "response": result.get("response", "I couldn't find an answer to your question."),
            "conversation_id": result.get("conversation_id"),
            "citations": result.get("citations", []),
            "processing_time": processing_time
        }
        
        logger.info(f"Query processed in {processing_time:.2f}s")
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )
