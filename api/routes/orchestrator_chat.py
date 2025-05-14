"""
Orchestrator Chat API: Central endpoint for multi-agent chat system

This API route implements the orchestrator pattern described in the multi-agent
architecture document, using the Agent Registry and Handoff Protocol to manage
agent selection and transitions.
"""

import os
import json
import time
import logging
import uuid
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, Field

from backend.agent_registry import get_registry
from backend.agent_handoff import get_handoff_manager, Session
from backend.protocol.ui_instruction import UIInstruction, validate_ui_instruction

# Set up router
router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

# Set up logging
logger = logging.getLogger(__name__)

# Session storage (in-memory for now)
# In a production system, this would use a persistent database
sessions: Dict[str, Session] = {}

# Models
class ChatRequest(BaseModel):
    """Request model for chat messages"""
    session_id: Optional[str] = Field(None, description="Session ID, or null for new session")
    user_message: str = Field(..., description="User message text")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChatResponse(BaseModel):
    """Response model for chat messages"""
    session_id: str = Field(..., description="Session ID for this conversation")
    assistant_message: str = Field(..., description="Response message from the assistant")
    done: bool = Field(False, description="Whether the conversation is complete")
    progress: Optional[Dict[str, Any]] = Field(None, description="Progress information (e.g., form completion)")
    agent_type: Optional[str] = Field(None, description="Type of agent that handled the message")
    handoff: Optional[Dict[str, Any]] = Field(None, description="Handoff information if a handoff occurred")
    ui_instruction: Optional[Dict[str, Any]] = Field(None, description="UI instruction for the frontend")


# Utility functions
def get_or_create_session(session_id: Optional[str] = None) -> Session:
    """
    Get an existing session or create a new one.
    
    Args:
        session_id: Optional existing session ID
        
    Returns:
        Session object
    """
    if session_id and session_id in sessions:
        return sessions[session_id]
    
    # Create new session
    new_id = session_id or f"session_{uuid.uuid4()}"
    
    # Get the default agent from registry config
    registry = get_registry()
    default_agent_id = getattr(registry._config, 'default_agent_id', None)
    
    # Create session with default agent
    sessions[new_id] = Session(
        session_id=new_id,
        registry=registry,
        handoff_manager=get_handoff_manager(),
        initial_agent_id=default_agent_id
    )
    
    logger.info(f"Created new session {new_id} with agent {default_agent_id}")
    return sessions[new_id]


def cleanup_old_sessions():
    """Remove sessions that have been inactive for more than an hour"""
    now = time.time()
    to_remove = []
    
    for session_id, session in sessions.items():
        # Check if any agent instance exists
        if session.active_agent_instance_id:
            try:
                agent = session.registry.get_agent_instance(session.active_agent_instance_id)
                if agent.is_idle(3600):  # 1 hour
                    to_remove.append(session_id)
            except ValueError:
                # Agent instance doesn't exist
                to_remove.append(session_id)
        else:
            # Session has no active agent
            to_remove.append(session_id)
    
    # Remove inactive sessions
    for session_id in to_remove:
        logger.info(f"Removing inactive session {session_id}")
        sessions.pop(session_id, None)


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    background_tasks: BackgroundTasks
):
    """
    Send a message to the chat system.
    
    This endpoint:
    1. Gets or creates a session
    2. Passes the message to the appropriate agent based on session state
    3. Handles agent handoffs automatically
    4. Returns the response with any UI instructions
    
    A new session starts with the default agent, which handles general inquiries
    and can hand off to specialized agents as needed.
    """
    # Schedule cleanup of old sessions
    background_tasks.add_task(cleanup_old_sessions)
    
    # Get or create session
    session = get_or_create_session(request.session_id)
    session_id = session.session_id
    
    try:
        # Process the message with the current agent
        response = session.handle_message(
            request.user_message,
            additional_context=request.meta
        )
        
        # Get agent type
        agent_type = session.active_agent_id
        
        # Prepare the response
        chat_response = ChatResponse(
            session_id=session_id,
            assistant_message=response.get("message", "I'm not sure how to respond to that."),
            done=response.get("done", False),
            progress=response.get("progress"),
            agent_type=agent_type,
            handoff=response.get("handoff")
        )
        
        # Add UI instruction if present
        ui_instruction = response.get("ui_instruction")
        if ui_instruction:
            # In a real implementation, this would validate and format the UI instruction
            # Here we just pass it through as a dictionary
            chat_response.ui_instruction = {
                "instruction_type": ui_instruction,
                "parameters": response.get("ui_instruction_params", {}),
                "metadata": {
                    "priority": "normal",
                    "version": "1.0.0",
                    "agent_id": agent_type
                }
            }
            
            # Validate the UI instruction if we're using the real protocol
            try:
                # This will raise an exception if invalid
                if hasattr(UIInstruction, '__annotations__'):
                    validate_ui_instruction(chat_response.ui_instruction)
            except Exception as e:
                logger.warning(f"Invalid UI instruction: {str(e)}")
                chat_response.ui_instruction = None
        
        return chat_response
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """
    Get information about a session.
    
    This endpoint returns:
    - Current active agent
    - Session data
    - Handoff history
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    # Get handoff history
    handoff_history = get_handoff_manager().get_handoff_history(session_id)
    
    return {
        "session_id": session_id,
        "active_agent": session.active_agent_id,
        "data": session.data,
        "handoff_history": [h.dict() for h in handoff_history],
        "message_count": len(session.message_history)
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sessions.pop(session_id)
    
    # Clear handoff history
    get_handoff_manager().clear_history(session_id)
    
    return {"status": "success", "message": f"Session {session_id} deleted"}


@router.get("/agents")
async def list_agents():
    """
    List all registered agent types.
    
    This endpoint returns information about all available agent types,
    their capabilities, and their UI instruction types.
    """
    registry = get_registry()
    agent_types = registry.get_agent_types()
    
    # Convert to a more API-friendly format
    result = []
    for agent_id, metadata in agent_types.items():
        # Collect UI instruction types from capabilities
        ui_instructions = set()
        for capability in metadata.capabilities.values():
            if capability.ui_instructions:
                ui_instructions.update(capability.ui_instructions)
        
        result.append({
            "id": agent_id,
            "name": metadata.name,
            "description": metadata.description,
            "version": metadata.version,
            "capabilities": list(metadata.capabilities.keys()),
            "ui_instructions": list(ui_instructions),
            "priority": metadata.priority
        })
    
    return result