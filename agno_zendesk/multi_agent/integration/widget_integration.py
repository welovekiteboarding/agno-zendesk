"""
Widget Integration Layer for Multi-Agent System

This module provides the integration layer between the multi-agent system and
the frontend widget, ensuring proper data formatting and API compatibility.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
import json
from datetime import datetime

from ..core.system import get_multi_agent_system
from ..orchestration.workflow_designer import get_workflow_designer
from ..core.agent_interface import AgentContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("widget_integration")


class WidgetIntegration:
    """
    Integration layer between the multi-agent system and frontend widget.
    Handles request processing, response formatting, and widget-specific features.
    """
    
    def __init__(self):
        """Initialize the widget integration layer."""
        self.multi_agent_system = get_multi_agent_system()
        self.workflow_designer = get_workflow_designer()
        
    async def process_widget_query(self, 
                                 query: str,
                                 conversation_id: Optional[str] = None,
                                 workflow_id: Optional[str] = None,
                                 metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a query from the widget.
        
        Args:
            query: The user query
            conversation_id: Optional conversation ID for continuing threads
            workflow_id: Optional explicit workflow ID to use
            metadata: Additional metadata for processing
            
        Returns:
            Widget-compatible response
        """
        logger.info(f"Processing widget query: {query}")
        
        # Initialize metadata if not provided
        metadata = metadata or {}
        
        # Add widget integration metadata
        metadata["source"] = "widget"
        metadata["timestamp"] = datetime.now().isoformat()
        
        # Design workflow if not specified
        custom_workflow_id = None
        if not workflow_id:
            designed_workflow = await self.workflow_designer.design_workflow(query)
            custom_workflow_id = designed_workflow["id"]
            
        # Process the query
        start_time = datetime.now()
        result = await self.multi_agent_system.process_query(
            query=query,
            conversation_id=conversation_id,
            workflow_id=workflow_id or custom_workflow_id,
            metadata=metadata
        )
        
        # Format the result for the widget
        widget_response = await self._format_widget_response(result)
        
        logger.info(f"Widget query processed in {(datetime.now() - start_time).total_seconds():.2f}s")
        return widget_response
    
    async def _format_widget_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a system result for the widget.
        
        Args:
            result: Raw result from the multi-agent system
            
        Returns:
            Widget-compatible response
        """
        # Extract response with fallback to ensure we never have a null response
        response_text = result.get("response", "") 
        
        # Ensure we have a valid string response (required by API model)
        if response_text is None or not isinstance(response_text, str):
            logger.warning(f"Invalid response text: {response_text}. Using fallback response.")
            response_text = "(Based on provided context)\n\nSorry, I could not generate a valid response for your query. Please try rephrasing your question with more specific details."
        
        # Format citations for the widget
        citations = []
        for citation in result.get("citations", []):
            formatted_citation = {
                "id": citation.get("id"),
                "source": citation.get("collection", "unknown"),
                "relevance": citation.get("relevance", "Medium"),
                "content": citation.get("content", ""),
                "metadata": citation.get("metadata", {})
            }
            citations.append(formatted_citation)
        
        # Create a widget-compatible response
        widget_response = {
            "query": result.get("query", ""),
            "response": response_text,
            "conversation_id": result.get("conversation_id", ""),
            "citations": citations,
            "processing_time": result.get("processing_time", 0),
            "timestamp": datetime.now().isoformat()
        }
        
        return widget_response
    
    async def initialize_widget(self) -> Dict[str, Any]:
        """
        Initialize the widget with necessary configuration.
        
        Returns:
            Widget configuration
        """
        # Get system info
        system_info = self.multi_agent_system.get_system_info()
        
        # Create widget configuration
        widget_config = {
            "widget_id": f"agno_rag_widget_{datetime.now().strftime('%Y%m%d')}",
            "available_workflows": [
                {"id": w["id"], "name": w["name"]}
                for w in system_info.get("registry", {}).get("workflows", [])
            ],
            "available_collections": system_info.get("collections", []),
            "widget_version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
        return widget_config
    
    async def get_citation_details(self, citation_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a citation.
        Used by the widget to display citation details.
        
        Args:
            citation_id: ID of the citation
            
        Returns:
            Citation details
        """
        # In a real implementation, this would look up the citation in a database
        # For now, we'll return a placeholder
        return {
            "id": citation_id,
            "title": "Citation Details",
            "source": "AstraDB Collection",
            "last_updated": datetime.now().isoformat(),
            "full_content": "Full content of the citation would be retrieved here.",
            "metadata": {}
        }
    
    async def provide_feedback(self, 
                             conversation_id: str,
                             feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user feedback on a response.
        
        Args:
            conversation_id: ID of the conversation
            feedback: Feedback data
            
        Returns:
            Acknowledgement
        """
        logger.info(f"Received feedback for conversation {conversation_id}")
        
        # In a real implementation, this would store the feedback for learning
        return {
            "status": "success",
            "message": "Feedback received and processed",
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat()
        }


# Singleton instance of the widget integration
_integration_instance = None

def get_widget_integration() -> WidgetIntegration:
    """
    Get the singleton instance of the widget integration.
    
    Returns:
        WidgetIntegration instance
    """
    global _integration_instance
    
    if _integration_instance is None:
        _integration_instance = WidgetIntegration()
        
    return _integration_instance
