"""
Agent Registry for Multi-Agent System

This module provides the registry for managing agent registration and discovery.
It serves as the central repository of all available agents and workflows.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Set
import json
from datetime import datetime

from ..core.agent_interface import Agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent_registry")


class AgentRegistry:
    """
    Registry for agents and workflows in the multi-agent system.
    Provides functions to register, discover, and manage agents.
    """
    
    def __init__(self):
        """Initialize an empty agent registry."""
        self.agents: Dict[str, Agent] = {}
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self.agent_capabilities: Dict[str, Set[str]] = {}
        
    def register_agent(self, agent: Agent) -> bool:
        """
        Register an agent with the registry.
        
        Args:
            agent: The agent to register
            
        Returns:
            True if registration was successful, False otherwise
        """
        if agent.agent_id in self.agents:
            logger.warning(f"Agent with ID {agent.agent_id} already exists, overwriting")
            
        self.agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")
        
        # Initialize capabilities set for this agent
        self.agent_capabilities[agent.agent_id] = set()
        
        return True
        
    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the registry.
        
        Args:
            agent_id: ID of the agent to unregister
            
        Returns:
            True if unregistration was successful, False otherwise
        """
        if agent_id not in self.agents:
            logger.warning(f"Agent with ID {agent_id} does not exist")
            return False
            
        self.agents.pop(agent_id)
        self.agent_capabilities.pop(agent_id, None)
        logger.info(f"Unregistered agent: {agent_id}")
        
        return True
        
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: ID of the agent to retrieve
            
        Returns:
            The agent if found, None otherwise
        """
        return self.agents.get(agent_id)
        
    def list_agents(self) -> List[Agent]:
        """
        List all registered agents.
        
        Returns:
            List of all registered agents
        """
        return list(self.agents.values())
        
    def get_agents_by_role(self, role: str) -> List[Agent]:
        """
        Get all agents with the specified role.
        
        Args:
            role: Role to filter agents by
            
        Returns:
            List of agents with the specified role
        """
        return [
            agent for agent in self.agents.values()
            if agent.role.lower() == role.lower()
        ]
        
    def register_agent_capability(self, agent_id: str, capability: str) -> bool:
        """
        Register a capability for an agent.
        
        Args:
            agent_id: ID of the agent
            capability: The capability to register
            
        Returns:
            True if registration was successful, False otherwise
        """
        if agent_id not in self.agents:
            logger.warning(f"Agent with ID {agent_id} does not exist")
            return False
            
        if agent_id not in self.agent_capabilities:
            self.agent_capabilities[agent_id] = set()
            
        self.agent_capabilities[agent_id].add(capability)
        logger.info(f"Registered capability '{capability}' for agent {agent_id}")
        
        return True
        
    def get_agents_by_capability(self, capability: str) -> List[Agent]:
        """
        Get all agents with the specified capability.
        
        Args:
            capability: Capability to filter agents by
            
        Returns:
            List of agents with the specified capability
        """
        agent_ids = [
            agent_id for agent_id, capabilities in self.agent_capabilities.items()
            if capability in capabilities
        ]
        
        return [
            self.agents[agent_id] for agent_id in agent_ids
            if agent_id in self.agents
        ]
        
    def register_workflow(self, 
                         workflow_id: str,
                         name: str,
                         description: str,
                         steps: List[Dict[str, Any]]) -> bool:
        """
        Register a workflow with the registry.
        
        Args:
            workflow_id: Unique identifier for the workflow
            name: Human-readable name for the workflow
            description: Detailed description of the workflow
            steps: List of steps in the workflow, each containing agent IDs
            
        Returns:
            True if registration was successful, False otherwise
        """
        # Validate steps
        for i, step in enumerate(steps):
            step_id = step.get("id", f"step_{i+1}")
            agent_ids = step.get("agents", [])
            
            # Ensure all agents exist
            for agent_id in agent_ids:
                if agent_id not in self.agents:
                    logger.warning(f"Workflow {workflow_id}, step {step_id}: " 
                                  f"Agent {agent_id} does not exist")
                    
        # Create workflow
        workflow = {
            "id": workflow_id,
            "name": name,
            "description": description,
            "steps": steps,
            "created_at": datetime.now().isoformat()
        }
        
        self.workflows[workflow_id] = workflow
        logger.info(f"Registered workflow: {name} ({workflow_id})")
        
        return True
        
    def unregister_workflow(self, workflow_id: str) -> bool:
        """
        Unregister a workflow from the registry.
        
        Args:
            workflow_id: ID of the workflow to unregister
            
        Returns:
            True if unregistration was successful, False otherwise
        """
        if workflow_id not in self.workflows:
            logger.warning(f"Workflow with ID {workflow_id} does not exist")
            return False
            
        self.workflows.pop(workflow_id)
        logger.info(f"Unregistered workflow: {workflow_id}")
        
        return True
        
    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a workflow by ID.
        
        Args:
            workflow_id: ID of the workflow to retrieve
            
        Returns:
            The workflow if found, None otherwise
        """
        return self.workflows.get(workflow_id)
        
    def list_workflows(self) -> List[Dict[str, Any]]:
        """
        List all registered workflows.
        
        Returns:
            List of all registered workflows
        """
        return list(self.workflows.values())
        
    def get_registry_info(self) -> Dict[str, Any]:
        """
        Get information about the registry.
        
        Returns:
            Dictionary containing registry metadata
        """
        agent_info = []
        for agent in self.agents.values():
            agent_info.append({
                "id": agent.agent_id,
                "name": agent.name,
                "role": agent.role,
                "capabilities": list(self.agent_capabilities.get(agent.agent_id, set()))
            })
            
        workflow_info = []
        for workflow in self.workflows.values():
            workflow_info.append({
                "id": workflow["id"],
                "name": workflow["name"],
                "steps": len(workflow["steps"])
            })
            
        return {
            "agent_count": len(self.agents),
            "workflow_count": len(self.workflows),
            "agents": agent_info,
            "workflows": workflow_info
        }


# Singleton instance of the agent registry
_registry_instance = None

def get_agent_registry() -> AgentRegistry:
    """
    Get the singleton instance of the agent registry.
    
    Returns:
        AgentRegistry instance
    """
    global _registry_instance
    
    if _registry_instance is None:
        _registry_instance = AgentRegistry()
        
    return _registry_instance
