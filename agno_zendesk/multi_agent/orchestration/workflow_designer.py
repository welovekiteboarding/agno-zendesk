"""
Workflow Designer for Multi-Agent Architecture

This module provides functionality for creating and managing agent workflows.
It enables dynamic creation of workflows tailored to different query types.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
import json
from datetime import datetime
import os

from ..registry.agent_registry import get_agent_registry
from ..core.agent_interface import AgentContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("workflow_designer")


class WorkflowDesigner:
    """
    Designer for creating and managing agent workflows.
    Helps determine the optimal agent workflow for different query types.
    """
    
    def __init__(self):
        """Initialize the workflow designer."""
        self.registry = get_agent_registry()
        self.workflow_templates = {}
        self._load_default_templates()
    
    def _load_default_templates(self) -> None:
        """Load default workflow templates."""
        # Simple RAG workflow
        self.workflow_templates["simple_rag"] = {
            "name": "Simple RAG Workflow",
            "description": "Basic retrieval-augmented generation workflow",
            "query_types": ["factual", "informational"],
            "steps": [
                {"agents": ["leader_agent"], "parallel": False},
                {"agents": ["research_agent"], "parallel": False},
                {"agents": ["synthesis_agent"], "parallel": False}
            ]
        }
        
        # Reasoning-enhanced RAG workflow
        self.workflow_templates["reasoning_rag"] = {
            "name": "Reasoning RAG Workflow",
            "description": "RAG workflow with logical reasoning capabilities",
            "query_types": ["reasoning", "why", "how", "explanation"],
            "steps": [
                {"agents": ["leader_agent"], "parallel": False},
                {"agents": ["research_agent"], "parallel": False},
                {"agents": ["reasoning_agent"], "parallel": False},
                {"agents": ["synthesis_agent"], "parallel": False}
            ]
        }
        
        # Quality-focused RAG workflow
        self.workflow_templates["quality_rag"] = {
            "name": "Quality-Enhanced RAG Workflow",
            "description": "RAG workflow with reflection for improved quality",
            "query_types": ["important", "critical", "sensitive"],
            "steps": [
                {"agents": ["leader_agent"], "parallel": False},
                {"agents": ["research_agent"], "parallel": False},
                {"agents": ["synthesis_agent"], "parallel": False},
                {"agents": ["reflection_agent"], "parallel": False}
            ]
        }
        
        # Comprehensive RAG workflow
        self.workflow_templates["comprehensive_rag"] = {
            "name": "Comprehensive RAG Workflow",
            "description": "Complete RAG workflow with all specialized agents",
            "query_types": ["complex", "comprehensive", "detailed"],
            "steps": [
                {"agents": ["leader_agent"], "parallel": False},
                {"agents": ["research_agent"], "parallel": False},
                {"agents": ["reasoning_agent"], "parallel": False},
                {"agents": ["synthesis_agent"], "parallel": False},
                {"agents": ["reflection_agent"], "parallel": False}
            ]
        }
    
    def register_template(self, 
                         template_id: str,
                         name: str,
                         description: str,
                         query_types: List[str],
                         steps: List[Dict[str, Any]]) -> bool:
        """
        Register a new workflow template.
        
        Args:
            template_id: Unique identifier for the template
            name: Human-readable name for the template
            description: Detailed description of the workflow
            query_types: List of query types this template is suitable for
            steps: List of workflow steps
            
        Returns:
            True if registration was successful, False otherwise
        """
        if template_id in self.workflow_templates:
            logger.warning(f"Template {template_id} already exists, overwriting")
            
        self.workflow_templates[template_id] = {
            "name": name,
            "description": description,
            "query_types": query_types,
            "steps": steps
        }
        
        logger.info(f"Registered workflow template: {name} ({template_id})")
        return True
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a workflow template by ID.
        
        Args:
            template_id: Unique identifier for the template
            
        Returns:
            The template if found, None otherwise
        """
        return self.workflow_templates.get(template_id)
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List all registered workflow templates.
        
        Returns:
            List of all registered templates
        """
        return [
            {"id": template_id, **template}
            for template_id, template in self.workflow_templates.items()
        ]
    
    async def analyze_query_type(self, query: str) -> str:
        """
        Analyze a query to determine its type.
        
        Args:
            query: The user query
            
        Returns:
            Detected query type
        """
        query_lower = query.lower()
        
        # Look for question type indicators
        if any(term in query_lower for term in ["why", "how come", "reason", "explain"]):
            return "reasoning"
        
        if any(term in query_lower for term in ["how to", "steps", "process", "procedure"]):
            return "procedural"
            
        if any(term in query_lower for term in ["compare", "better", "difference", "versus", "vs."]):
            return "comparative"
            
        if any(term in query_lower for term in ["best", "recommend", "suggest", "should i"]):
            return "recommendation"
            
        if any(term in query_lower for term in ["complex", "detailed", "comprehensive", "thorough"]):
            return "complex"
        
        # Default to informational for simpler queries
        return "informational"
    
    async def design_workflow(self, 
                             query: str, 
                             context: Optional[AgentContext] = None,
                             workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Design a workflow for the given query.
        
        Args:
            query: The user query
            context: Optional context with additional metadata
            workflow_id: Optional explicit workflow ID to use
            
        Returns:
            Designed workflow definition
        """
        # If a specific workflow is requested, use it
        if workflow_id and workflow_id in self.registry.workflows:
            logger.info(f"Using explicitly requested workflow: {workflow_id}")
            return self.registry.get_workflow(workflow_id)
        
        # Otherwise, determine the appropriate workflow based on query analysis
        query_type = await self.analyze_query_type(query)
        logger.info(f"Analyzed query type: {query_type}")
        
        # Find the best matching template
        best_template_id = "simple_rag"  # Default template
        
        for template_id, template in self.workflow_templates.items():
            query_types = template.get("query_types", [])
            if query_type in query_types:
                best_template_id = template_id
                break
        
        logger.info(f"Selected workflow template: {best_template_id}")
        template = self.workflow_templates[best_template_id]
        
        # Design the workflow based on the template
        workflow_id = f"custom_{best_template_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create workflow with steps from the template
        steps = []
        for i, step_template in enumerate(template["steps"]):
            step = {
                "id": f"step_{i+1}",
                "agents": step_template["agents"],
                "parallel": step_template.get("parallel", False)
            }
            steps.append(step)
        
        # Register the new workflow
        self.registry.register_workflow(
            workflow_id=workflow_id,
            name=f"Custom {template['name']}",
            description=f"Custom workflow based on {template['name']} template",
            steps=steps
        )
        
        logger.info(f"Created custom workflow: {workflow_id}")
        return self.registry.get_workflow(workflow_id)
    
    async def create_workflow_from_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a workflow from a query analysis.
        
        Args:
            analysis: Query analysis containing agent roles and other metadata
            
        Returns:
            Created workflow definition
        """
        agent_roles = analysis.get("agent_roles", ["research", "synthesis"])
        
        # Map roles to agent IDs
        role_to_agent = {
            "planning": "leader_agent",
            "research": "research_agent",
            "reasoning": "reasoning_agent",
            "synthesis": "synthesis_agent",
            "reflection": "reflection_agent"
        }
        
        # Create workflow steps
        steps = []
        for i, role in enumerate(agent_roles):
            agent_id = role_to_agent.get(role)
            if agent_id:
                step = {
                    "id": f"step_{i+1}",
                    "agents": [agent_id],
                    "parallel": False
                }
                steps.append(step)
        
        # Add leader agent as first step if not already included
        if "leader_agent" not in [step["agents"][0] for step in steps]:
            steps.insert(0, {
                "id": "step_1",
                "agents": ["leader_agent"],
                "parallel": False
            })
        
        # Register the workflow
        workflow_id = f"analysis_workflow_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.registry.register_workflow(
            workflow_id=workflow_id,
            name=f"Analysis-Based Workflow",
            description=f"Workflow created from query analysis",
            steps=steps
        )
        
        logger.info(f"Created workflow from analysis: {workflow_id}")
        return self.registry.get_workflow(workflow_id)


# Singleton instance of the workflow designer
_designer_instance = None

def get_workflow_designer() -> WorkflowDesigner:
    """
    Get the singleton instance of the workflow designer.
    
    Returns:
        WorkflowDesigner instance
    """
    global _designer_instance
    
    if _designer_instance is None:
        _designer_instance = WorkflowDesigner()
        
    return _designer_instance
