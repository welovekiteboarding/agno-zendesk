"""
Agent Handoff Protocol: Standardized mechanism for transferring control and context between agents

This module provides utilities for handling the transfer of control and context
between different agents in the system, ensuring a smooth transition with proper
state preservation.
"""

import time
import logging
import json
from typing import Dict, Any, Optional, List, Set, Union, Tuple
from pydantic import BaseModel, Field

from .agent_registry import get_registry, AgentRegistry

# Set up logging
logger = logging.getLogger(__name__)

class HandoffContext(BaseModel):
    """Context information transferred during a handoff between agents"""
    source_agent_id: str = Field(..., description="ID of the agent initiating the handoff")
    target_agent_id: str = Field(..., description="ID of the agent receiving the handoff")
    session_id: str = Field(..., description="ID of the user session")
    reason: str = Field(..., description="Reason for the handoff")
    timestamp: float = Field(default_factory=time.time, description="Time of the handoff")
    message_history: List[Dict[str, Any]] = Field(default_factory=list, description="Relevant message history")
    collected_data: Dict[str, Any] = Field(default_factory=dict, description="Data collected by previous agents")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the handoff")


class HandoffManager:
    """
    Manager for agent handoffs that handles:
    - Context transfer between agents
    - Orchestrating the handoff process
    - Tracking handoff history
    """
    
    def __init__(self, registry: Optional[AgentRegistry] = None):
        """
        Initialize the handoff manager.
        
        Args:
            registry: Optional agent registry, or use the default
        """
        self.registry = registry or get_registry()
        self.handoff_history: Dict[str, List[HandoffContext]] = {}
    
    def initiate_handoff(
        self,
        source_agent_id: str,
        target_agent_id: str,
        session_id: str,
        reason: str,
        message_history: Optional[List[Dict[str, Any]]] = None,
        collected_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> HandoffContext:
        """
        Initiate a handoff from one agent to another.
        
        Args:
            source_agent_id: ID of the agent initiating the handoff
            target_agent_id: ID of the agent receiving the handoff
            session_id: ID of the user session
            reason: Reason for the handoff
            message_history: Optional message history to include
            collected_data: Optional data collected by the source agent
            metadata: Optional additional metadata
            
        Returns:
            Handoff context
            
        Raises:
            ValueError: If the source or target agent is not registered
        """
        # Validate agents
        source_metadata = self.registry.get_agent_type(source_agent_id)
        target_metadata = self.registry.get_agent_type(target_agent_id)
        
        if not source_metadata:
            raise ValueError(f"Source agent not registered: {source_agent_id}")
        
        if not target_metadata:
            raise ValueError(f"Target agent not registered: {target_agent_id}")
        
        # Create handoff context
        context = HandoffContext(
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            session_id=session_id,
            reason=reason,
            message_history=message_history or [],
            collected_data=collected_data or {},
            metadata=metadata or {}
        )
        
        # Add to history
        if session_id not in self.handoff_history:
            self.handoff_history[session_id] = []
        
        self.handoff_history[session_id].append(context)
        
        logger.info(f"Initiated handoff: {source_agent_id} -> {target_agent_id} for session {session_id}: {reason}")
        
        return context
    
    def get_handoff_history(self, session_id: str) -> List[HandoffContext]:
        """
        Get the handoff history for a session.
        
        Args:
            session_id: ID of the user session
            
        Returns:
            List of handoff contexts in chronological order
        """
        return self.handoff_history.get(session_id, [])
    
    def get_last_handoff(self, session_id: str) -> Optional[HandoffContext]:
        """
        Get the most recent handoff for a session.
        
        Args:
            session_id: ID of the user session
            
        Returns:
            Most recent handoff context, or None if no handoffs
        """
        history = self.handoff_history.get(session_id, [])
        return history[-1] if history else None
    
    def evaluate_handoff(self, current_agent_id: str, context: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Evaluate whether a handoff should occur based on the current context.
        
        Args:
            current_agent_id: ID of the current agent
            context: Current context (message, session data, etc.)
            
        Returns:
            Tuple of (should_handoff, target_agent_id, reason)
        """
        # Use the registry to evaluate handoff triggers
        target_agent_id = self.registry.evaluate_handoff_triggers(current_agent_id, context)
        
        if target_agent_id:
            # Find the matching trigger to get its description
            agent_metadata = self.registry.get_agent_type(current_agent_id)
            reason = "Handoff trigger matched"
            
            if agent_metadata:
                for trigger in agent_metadata.handoff_triggers:
                    if trigger.target_agent_id == target_agent_id:
                        reason = trigger.description
                        break
            
            return True, target_agent_id, reason
        
        return False, None, None
    
    def clear_history(self, session_id: Optional[str] = None) -> None:
        """
        Clear handoff history.
        
        Args:
            session_id: Optional session ID to clear, or all sessions if None
        """
        if session_id:
            self.handoff_history.pop(session_id, None)
        else:
            self.handoff_history.clear()


class Session:
    """
    User session that tracks active agent and provides handoff methods.
    
    This class serves as an integration point between the agent registry,
    handoff manager, and application code.
    """
    
    def __init__(
        self,
        session_id: str,
        registry: Optional[AgentRegistry] = None,
        handoff_manager: Optional[HandoffManager] = None,
        initial_agent_id: Optional[str] = None,
        initial_data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a session.
        
        Args:
            session_id: Unique identifier for this session
            registry: Optional agent registry, or use the default
            handoff_manager: Optional handoff manager, or create a new one
            initial_agent_id: Optional ID of the initial agent
            initial_data: Optional initial session data
        """
        self.session_id = session_id
        self.registry = registry or get_registry()
        self.handoff_manager = handoff_manager or HandoffManager(self.registry)
        self.active_agent_id = initial_agent_id
        self.active_agent_instance_id = None
        self.data = initial_data or {}
        self.message_history = []
    
    def set_active_agent(self, agent_id: str) -> bool:
        """
        Set the active agent for this session.
        
        Args:
            agent_id: ID of the agent type
            
        Returns:
            True if the agent was set, False if not registered
            
        Note:
            This does not perform a handoff, just switches the active agent.
        """
        if not self.registry.get_agent_type(agent_id):
            return False
        
        self.active_agent_id = agent_id
        self.active_agent_instance_id = None  # Reset instance
        return True
    
    def get_active_agent(self):
        """
        Get the active agent instance for this session.
        
        Returns:
            Agent instance
            
        Raises:
            ValueError: If no active agent is set or it can't be instantiated
        """
        if not self.active_agent_id:
            raise ValueError("No active agent set for this session")
        
        # If we already have an instance, return it
        if self.active_agent_instance_id:
            try:
                return self.registry.get_agent_instance(self.active_agent_instance_id)
            except ValueError:
                # Instance no longer exists, will create a new one
                self.active_agent_instance_id = None
        
        # Create a new instance from the registry
        from .agent_registry import AgentConfig
        config = AgentConfig(
            agent_id=self.active_agent_id,
            params={"session_id": self.session_id}
        )
        
        try:
            self.active_agent_instance_id = self.registry.instantiate_agent(config)
            return self.registry.get_agent_instance(self.active_agent_instance_id)
        except ValueError as e:
            raise ValueError(f"Failed to instantiate agent {self.active_agent_id}: {str(e)}")
    
    def handle_message(self, message: str, additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle a user message, including automatic agent handoff if needed.
        
        Args:
            message: User message
            additional_context: Additional context data
            
        Returns:
            Response including potential handoff information
            
        Raises:
            ValueError: If no active agent is set
        """
        if not self.active_agent_id:
            raise ValueError("No active agent set for this session")
        
        # Create context for evaluating handoffs
        context = {
            "message": message,
            "session_id": self.session_id,
            "session_data": self.data,
            "message_history": self.message_history,
            **(additional_context or {})
        }
        
        # Check if a handoff should occur before processing
        should_handoff, target_agent_id, reason = self.handoff_manager.evaluate_handoff(
            self.active_agent_id, context
        )
        
        if should_handoff and target_agent_id:
            return self.perform_handoff(target_agent_id, reason, message)
        
        # No handoff needed, process with current agent
        agent = self.get_active_agent()
        
        # Add user message to history
        self.message_history.append({
            "role": "user",
            "content": message,
            "timestamp": time.time()
        })
        
        # Process the message with the active agent
        try:
            response = agent.process_message(message, context)
            
            # Add agent response to history
            if "message" in response:
                self.message_history.append({
                    "role": "assistant",
                    "content": response["message"],
                    "timestamp": time.time()
                })
            
            # Check if the agent wants to hand off after processing
            if response.get("handoff_to"):
                return self.perform_handoff(
                    response["handoff_to"],
                    response.get("handoff_reason", "Agent requested handoff"),
                    message
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return {
                "message": "Sorry, there was an error processing your request.",
                "error": str(e)
            }
    
    def perform_handoff(self, target_agent_id: str, reason: str, last_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform a handoff to another agent.
        
        Args:
            target_agent_id: ID of the agent to hand off to
            reason: Reason for the handoff
            last_message: Optional last message from the user
            
        Returns:
            Response including handoff information
        """
        if not self.active_agent_id:
            logger.warning(f"Attempted handoff to {target_agent_id} but no active agent is set")
            self.active_agent_id = target_agent_id
            return {
                "message": "Let me help you with that.",
                "handoff": {
                    "from": None,
                    "to": target_agent_id,
                    "reason": reason
                }
            }
        
        # Initiate the handoff
        context = self.handoff_manager.initiate_handoff(
            self.active_agent_id,
            target_agent_id,
            self.session_id,
            reason,
            message_history=self.message_history,
            collected_data=self.data
        )
        
        # Update active agent
        previous_agent_id = self.active_agent_id
        self.active_agent_id = target_agent_id
        
        # If we have a last message, process it with the new agent
        response = {
            "handoff": {
                "from": previous_agent_id,
                "to": target_agent_id,
                "reason": reason
            }
        }
        
        if last_message:
            # Get the new agent
            try:
                agent = self.get_active_agent()
                
                # Process the message with appropriate context
                handoff_response = agent.process_message(last_message, {
                    "message": last_message,
                    "session_id": self.session_id,
                    "session_data": self.data,
                    "message_history": self.message_history,
                    "handoff_context": context.dict()
                })
                
                # Merge responses
                response.update(handoff_response)
                
                # Add agent response to history if present
                if "message" in handoff_response:
                    self.message_history.append({
                        "role": "assistant",
                        "content": handoff_response["message"],
                        "timestamp": time.time()
                    })
                
            except Exception as e:
                logger.error(f"Error processing message after handoff: {str(e)}", exc_info=True)
                response["message"] = "I'll help you with that."
                response["error"] = str(e)
        else:
            # Default message if no last message to process
            response["message"] = "I'll help you with that."
        
        return response


# Singleton handoff manager
_handoff_manager_instance = None


def get_handoff_manager() -> HandoffManager:
    """
    Get the singleton instance of the handoff manager.
    
    Returns:
        Handoff manager instance
    """
    global _handoff_manager_instance
    
    if _handoff_manager_instance is None:
        _handoff_manager_instance = HandoffManager()
    
    return _handoff_manager_instance