"""
FastAPI Server for Multi-Agent Widget Backend

This module implements a FastAPI server specifically designed to serve
as the backend for the Vercel-hosted widget frontend.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..integration.widget_integration import get_widget_integration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("widget_api")

# Create FastAPI app
app = FastAPI(
    title="Agno Multi-Agent Widget API",
    description="API for the Agno Multi-Agent RAG widget frontend",
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
class WidgetQueryRequest(BaseModel):
    query: str = Field(..., description="The user query")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID")
    workflow_id: Optional[str] = Field(None, description="Optional workflow ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class WidgetQueryResponse(BaseModel):
    query: str = Field(..., description="The original query")
    response: str = Field(..., description="The generated response")
    conversation_id: str = Field(..., description="Conversation ID")
    citations: List[Dict[str, Any]] = Field(..., description="Citations used in the response")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: str = Field(..., description="Response timestamp")


class FeedbackRequest(BaseModel):
    conversation_id: str = Field(..., description="Conversation ID")
    helpful: bool = Field(..., description="Whether the response was helpful")
    comments: Optional[str] = Field(None, description="Optional feedback comments")
    rating: Optional[int] = Field(None, description="Optional rating (1-5)")


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    logger.info("Starting Widget API server")
    
    # Check environment variables
    required_env_vars = ["ASTRA_ENDPOINT", "ASTRA_TOKEN", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Server will start but API calls may fail")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/widget/config")
async def get_widget_config():
    """Get widget configuration."""
    try:
        integration = get_widget_integration()
        config = await integration.initialize_widget()
        return config
    except Exception as e:
        logger.error(f"Error getting widget config: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting widget configuration: {str(e)}"
        )


@app.post("/widget/query", response_model=WidgetQueryResponse)
async def process_widget_query(request: WidgetQueryRequest):
    """
    Process a query from the widget.
    
    Args:
        request: The widget query request
        
    Returns:
        The widget query response
    """
    logger.info(f"Received widget query: {request.query}")
    
    try:
        # Get the widget integration
        integration = get_widget_integration()
        
        # Process the query
        result = await integration.process_widget_query(
            query=request.query,
            conversation_id=request.conversation_id,
            workflow_id=request.workflow_id,
            metadata=request.metadata
        )
        
        logger.info(f"Widget query processed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error processing widget query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.get("/widget/citation/{citation_id}")
async def get_citation(citation_id: str):
    """
    Get detailed information about a citation.
    
    Args:
        citation_id: ID of the citation
        
    Returns:
        Citation details
    """
    try:
        integration = get_widget_integration()
        citation_details = await integration.get_citation_details(citation_id)
        return citation_details
    except Exception as e:
        logger.error(f"Error getting citation details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting citation details: {str(e)}"
        )


@app.post("/widget/feedback")
async def provide_feedback(feedback: FeedbackRequest):
    """
    Process user feedback on a response.
    
    Args:
        feedback: The feedback request
        
    Returns:
        Acknowledgement
    """
    try:
        integration = get_widget_integration()
        result = await integration.provide_feedback(
            conversation_id=feedback.conversation_id,
            feedback={
                "helpful": feedback.helpful,
                "comments": feedback.comments,
                "rating": feedback.rating,
                "timestamp": datetime.now().isoformat()
            }
        )
        return result
    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing feedback: {str(e)}"
        )
