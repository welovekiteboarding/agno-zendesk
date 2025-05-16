"""
Core Agent Interface Definition

This module defines the core Agent interface that all specialized agents must implement.
It establishes the contract for agent communication and execution within the multi-agent system.
"""

import abc
from typing import Dict, List, Any, Optional, Union, Callable
import asyncio
import uuid
from datetime import datetime


class AgentContext:
    """
    Context object passed between agents containing shared state and conversation history.
    """
    
    def __init__(self, 
                 query: str = "", 
                 conversation_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a new agent context.
        
        Args:
            query: The original user query
            conversation_id: Unique identifier for the conversation
            metadata: Additional metadata for the context
        """
        self.query = query
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        
        # Memory and state tracking
        self.short_term_memory: List[Dict[str, Any]] = []
        self.agent_states: Dict[str, Any] = {}
        
        # For tracking progress and results
        self.results: Dict[str, Any] = {}
        self.citations: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        
    def update_memory(self, entry: Dict[str, Any]) -> None:
        """Add an entry to the short-term memory."""
        self.short_term_memory.append(entry)
        self.updated_at = datetime.now()
        
    def get_result(self, key: str) -> Any:
        """Get a result by key."""
        return self.results.get(key)
    
    def set_result(self, key: str, value: Any) -> None:
        """Set a result by key."""
        self.results[key] = value
        self.updated_at = datetime.now()
        
    def add_citation(self, source: str, content: str, metadata: Dict[str, Any]) -> None:
        """Add a citation to the context."""
        self.citations.append({
            "id": len(self.citations) + 1,
            "source": source,
            "content": content,
            "metadata": metadata,
            "created_at": datetime.now()
        })
        
    def add_error(self, agent_id: str, error_message: str, exception: Optional[Exception] = None) -> None:
        """Add an error to the context."""
        self.errors.append({
            "agent_id": agent_id,
            "error_message": error_message,
            "exception": str(exception) if exception else None,
            "timestamp": datetime.now()
        })


class Agent(abc.ABC):
    """
    Abstract base class for all agents in the multi-agent system.
    Defines the required interface for agent communication and execution.
    """
    
    def __init__(self, 
                 agent_id: str,
                 name: str,
                 description: str,
                 role: str,
                 model: Optional[str] = None):
        """
        Initialize a new agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            description: Detailed description of the agent's purpose
            role: The agent's role in the multi-agent system
            model: The name of the LLM model to use (if applicable)
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.role = role
        self.model = model
        self.created_at = datetime.now()
        self.tools: List[Dict[str, Any]] = []
        
    @abc.abstractmethod
    async def process(self, context: AgentContext) -> AgentContext:
        """
        Process the given context and return an updated context.
        This is the main entry point for agent execution.
        
        Args:
            context: The current context containing conversation state
        
        Returns:
            Updated context with new results/insights
        """
        pass
    
    @abc.abstractmethod
    async def can_handle(self, context: AgentContext) -> bool:
        """
        Determine if this agent can handle the given context.
        Used by the orchestrator to select appropriate agents.
        
        Args:
            context: The current context containing conversation state
            
        Returns:
            True if the agent can handle this context, False otherwise
        """
        pass
    
    def register_tool(self, tool: Dict[str, Any]) -> None:
        """
        Register a tool with this agent.
        
        Args:
            tool: Tool definition including name, description, and callable
        """
        self.tools.append(tool)
        
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about this agent for the registry.
        
        Returns:
            Dictionary containing agent metadata
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "role": self.role,
            "model": self.model,
            "created_at": self.created_at,
            "tools": [t["name"] for t in self.tools]
        }
    
    async def handle_error(self, context: AgentContext, error: Exception) -> AgentContext:
        """
        Handle an error that occurred during processing.
        
        Args:
            context: The current context containing conversation state
            error: The exception that occurred
            
        Returns:
            Updated context with error information
        """
        context.add_error(self.agent_id, f"Error in {self.name} agent", error)
        return context
