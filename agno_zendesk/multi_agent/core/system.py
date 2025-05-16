"""
Multi-Agent System Core Implementation

This module provides the main entry point for the multi-agent system.
It initializes all components and provides the API for interacting with the system.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
import json
from datetime import datetime
import os

from .agent_interface import Agent, AgentContext
from ..orchestration.orchestrator import AgentOrchestrator
from ..registry.agent_registry import get_agent_registry, AgentRegistry
from ..agents.research_agent import ResearchAgent
from ..agents.synthesis_agent import SynthesisAgent
from ..agents.leader_agent import LeaderAgent
from ..agents.reasoning_agent import ReasoningAgent
from ..agents.reflection_agent import ReflectionAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("multi_agent_system")


class MultiAgentSystem:
    """
    Core system for the multi-agent architecture.
    Initializes and manages all components of the system.
    """
    
    def __init__(self, 
                collections: Optional[List[str]] = None,
                load_default_agents: bool = True):
        """
        Initialize the multi-agent system.
        
        Args:
            collections: List of AstraDB collections to use
            load_default_agents: Whether to load default agents
        """
        self.registry = get_agent_registry()
        self.orchestrator = AgentOrchestrator(self.registry)
        self.collections = collections or ["ss_guide", "kb_articles"]
        
        # Initialize system
        if load_default_agents:
            self._load_default_agents()
    
    def _load_default_agents(self) -> None:
        """Load default agents into the registry."""
        logger.info("Loading default agents")
        
        # Create and register the leader agent
        leader_agent = LeaderAgent(
            agent_id="leader_agent",
            name="Leader Agent",
            description="Coordinates agent execution and workflow planning"
        )
        self.registry.register_agent(leader_agent)
        
        # Create and register the research agent
        research_agent = ResearchAgent(
            agent_id="research_agent",
            name="Research Agent",
            description="Retrieves information from AstraDB collections",
            collections=self.collections
        )
        self.registry.register_agent(research_agent)
        
        # Create and register the reasoning agent
        reasoning_agent = ReasoningAgent(
            agent_id="reasoning_agent",
            name="Reasoning Agent",
            description="Performs logical analysis and reasoning on retrieved information"
        )
        self.registry.register_agent(reasoning_agent)
        
        # Create and register the synthesis agent
        synthesis_agent = SynthesisAgent(
            agent_id="synthesis_agent",
            name="Synthesis Agent",
            description="Synthesizes retrieved information into coherent responses"
        )
        self.registry.register_agent(synthesis_agent)
        
        # Create and register the reflection agent
        reflection_agent = ReflectionAgent(
            agent_id="reflection_agent",
            name="Reflection Agent",
            description="Reviews and improves responses for accuracy and completeness"
        )
        self.registry.register_agent(reflection_agent)
        
        # Register agent capabilities
        self.registry.register_agent_capability("leader_agent", "planning")
        self.registry.register_agent_capability("leader_agent", "workflow_design")
        self.registry.register_agent_capability("research_agent", "vector_search")
        self.registry.register_agent_capability("research_agent", "multi_collection_search")
        self.registry.register_agent_capability("reasoning_agent", "logical_analysis")
        self.registry.register_agent_capability("reasoning_agent", "causal_reasoning")
        self.registry.register_agent_capability("synthesis_agent", "response_generation")
        self.registry.register_agent_capability("synthesis_agent", "citation_formatting")
        self.registry.register_agent_capability("reflection_agent", "response_improvement")
        self.registry.register_agent_capability("reflection_agent", "hallucination_detection")
        
        # Register standard workflow
        self.registry.register_workflow(
            workflow_id="standard_rag",
            name="Standard RAG Workflow",
            description="Standard retrieval-augmented generation workflow",
            steps=[
                {
                    "id": "step_1",
                    "agents": ["leader_agent"],
                    "parallel": False
                },
                {
                    "id": "step_2",
                    "agents": ["research_agent"],
                    "parallel": False
                },
                {
                    "id": "step_3",
                    "agents": ["synthesis_agent"],
                    "parallel": False
                },
                {
                    "id": "step_4",
                    "agents": ["reflection_agent"],
                    "parallel": False
                }
            ]
        )
        
        # Register enhanced reasoning workflow
        self.registry.register_workflow(
            workflow_id="reasoning_rag",
            name="Reasoning-Enhanced RAG Workflow",
            description="RAG workflow with logical reasoning and analysis capabilities",
            steps=[
                {
                    "id": "step_1",
                    "agents": ["leader_agent"],
                    "parallel": False
                },
                {
                    "id": "step_2",
                    "agents": ["research_agent"],
                    "parallel": False
                },
                {
                    "id": "step_3",
                    "agents": ["reasoning_agent"],
                    "parallel": False
                },
                {
                    "id": "step_4",
                    "agents": ["synthesis_agent"],
                    "parallel": False
                },
                {
                    "id": "step_5",
                    "agents": ["reflection_agent"],
                    "parallel": False
                }
            ]
        )
        
        logger.info("Default agents and workflow loaded")
    
    async def process_query(self, 
                           query: str,
                           conversation_id: Optional[str] = None,
                           workflow_id: Optional[str] = "standard_rag",
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user query through the multi-agent system.
        
        Args:
            query: The user query
            conversation_id: Optional conversation ID
            workflow_id: Workflow ID to use (defaults to standard_rag)
            metadata: Additional metadata
            
        Returns:
            Dictionary containing the response and processing details
        """
        logger.info(f"Processing query: {query}")
        
        # Create agent context
        context = AgentContext(
            query=query,
            conversation_id=conversation_id,
            metadata=metadata or {}
        )
        
        # Execute the workflow
        if workflow_id:
            updated_context = await self.orchestrator.execute_workflow(
                workflow_id=workflow_id,
                context=context
            )
        else:
            # Use dynamic orchestration if no workflow specified
            updated_context = await self.orchestrator.dynamic_orchestration(context)
        
        # Extract the response from context
        response = updated_context.get_result("synthesized_response")
        
        # Prepare result
        result = {
            "query": query,
            "response": response,
            "conversation_id": updated_context.conversation_id,
            "workflow_id": workflow_id,
            "processing_time": (datetime.now() - context.created_at).total_seconds(),
            "citation_count": len(updated_context.citations),
            "citations": updated_context.citations,  # Make sure to pass the actual citations
            "error_count": len(updated_context.errors)
        }
        
        # Include errors if any
        if updated_context.errors:
            result["errors"] = [
                {"agent": error["agent_id"], "message": error["error_message"]}
                for error in updated_context.errors
            ]
        
        logger.info(f"Query processing completed. Response length: {len(response) if response else 0}")
        return result
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get information about the multi-agent system.
        
        Returns:
            Dictionary containing system information
        """
        registry_info = self.registry.get_registry_info()
        telemetry = self.orchestrator.get_execution_telemetry()
        
        return {
            "registry": registry_info,
            "telemetry": telemetry,
            "collections": self.collections
        }


# Singleton instance of the multi-agent system
_system_instance = None

def get_multi_agent_system(collections: Optional[List[str]] = None) -> MultiAgentSystem:
    """
    Get the singleton instance of the multi-agent system.
    
    Args:
        collections: Optional list of collections to use
        
    Returns:
        MultiAgentSystem instance
    """
    global _system_instance
    
    if _system_instance is None:
        _system_instance = MultiAgentSystem(collections=collections)
        
    return _system_instance
