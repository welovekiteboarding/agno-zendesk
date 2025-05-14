"""
Base Agent: Abstract base class for all agents in the system

This module provides a common interface and utilities for all agent implementations,
ensuring consistency in behavior and integration with the agent registry.
"""

import abc
import time
import logging
from typing import Dict, Any, Optional, List, Set, Union

from ..agent_registry import AgentCapability, CapabilityType, HandoffTrigger

# Set up logging
logger = logging.getLogger(__name__)

class BaseAgent(abc.ABC):
    """
    Abstract base class for all agents in the system.
    
    All agents must implement the process_message method to handle user messages,
    and should provide appropriate capabilities and handoff triggers through
    their registration.
    """
    
    def __init__(self, session_id: Optional[str] = None, **kwargs):
        """
        Initialize the agent.
        
        Args:
            session_id: Optional session ID for this agent instance
            **kwargs: Additional configuration parameters
        """
        self.session_id = session_id
        self.config = kwargs
        self.last_activity = time.time()
        
        # This will be set by the agent registry when registered
        self._agent_metadata = None
        self._instance_id = None
        
        # Initialize the agent
        self.initialize(**kwargs)
    
    def initialize(self, **kwargs):
        """
        Initialize the agent with configuration parameters.
        
        Subclasses should override this method to perform any necessary setup.
        
        Args:
            **kwargs: Configuration parameters
        """
        pass
    
    @abc.abstractmethod
    def process_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a user message and return a response.
        
        Args:
            message: User message text
            context: Additional context information
            
        Returns:
            Response dictionary, which may include:
            - message: Response text to show to the user
            - ui_instruction: Optional UI instruction to show specialized UI elements
            - handoff_to: Optional ID of agent to hand off to
            - handoff_reason: Optional reason for the handoff
            - data: Optional data extracted/processed by this agent
            - metadata: Optional additional metadata
        """
        raise NotImplementedError("Agents must implement process_message")
    
    def get_capabilities(self) -> Dict[str, str]:
        """
        Get the capabilities of this agent.
        
        Returns:
            Dictionary mapping capability IDs to their descriptions
        """
        if not self._agent_metadata:
            return {}
        
        return {
            capability_id: capability.description
            for capability_id, capability in self._agent_metadata.capabilities.items()
        }
    
    def get_id(self) -> Optional[str]:
        """
        Get the agent type ID.
        
        Returns:
            Agent type ID, or None if not registered
        """
        return self._agent_metadata.id if self._agent_metadata else None
    
    def get_instance_id(self) -> Optional[str]:
        """
        Get the agent instance ID.
        
        Returns:
            Agent instance ID, or None if not registered
        """
        return self._instance_id
    
    def update_last_activity(self):
        """Update the timestamp of the last activity"""
        self.last_activity = time.time()
    
    def is_idle(self, timeout_seconds: int = 300) -> bool:
        """
        Check if the agent has been idle for the specified time.
        
        Args:
            timeout_seconds: Number of seconds to consider as idle
            
        Returns:
            True if the agent has been idle for longer than the timeout
        """
        return (time.time() - self.last_activity) > timeout_seconds