"""
Multi-Agent Orchestration Layer

This module implements the orchestrator that coordinates the interactions between agents,
manages the execution flow, and handles the distribution of context.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Set, Tuple
import json
import time
from datetime import datetime

from ..core.agent_interface import Agent, AgentContext
from ..registry.agent_registry import AgentRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator")


class AgentOrchestrator:
    """
    Coordinates the execution of agents in the multi-agent system.
    Manages agent dependencies, execution flow, and context distribution.
    """
    
    def __init__(self, registry: AgentRegistry):
        """
        Initialize the orchestrator with an agent registry.
        
        Args:
            registry: The agent registry containing all available agents
        """
        self.registry = registry
        self.execution_history: List[Dict[str, Any]] = []
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        
    async def execute_single_agent(self, 
                                agent: Agent, 
                                context: AgentContext) -> Tuple[Agent, AgentContext]:
        """
        Execute a single agent with the given context.
        
        Args:
            agent: The agent to execute
            context: The current context
            
        Returns:
            Tuple of (agent, updated_context)
        """
        start_time = time.time()
        logger.info(f"Executing agent: {agent.name} ({agent.agent_id})")
        
        try:
            # Check if agent can handle this context
            can_handle = await agent.can_handle(context)
            if not can_handle:
                logger.warning(f"Agent {agent.name} cannot handle this context")
                context.add_error(
                    agent.agent_id, 
                    f"Agent {agent.name} refused to handle context"
                )
                return agent, context
            
            # Process the context
            updated_context = await agent.process(context)
            
            # Record execution in history
            execution_time = time.time() - start_time
            self.execution_history.append({
                "agent_id": agent.agent_id,
                "agent_name": agent.name,
                "conversation_id": context.conversation_id,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "success": True
            })
            
            return agent, updated_context
            
        except Exception as e:
            logger.error(f"Error executing agent {agent.name}: {str(e)}")
            execution_time = time.time() - start_time
            
            # Record failed execution
            self.execution_history.append({
                "agent_id": agent.agent_id,
                "agent_name": agent.name,
                "conversation_id": context.conversation_id,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            })
            
            # Handle the error through the agent
            try:
                updated_context = await agent.handle_error(context, e)
                return agent, updated_context
            except Exception as handle_e:
                logger.error(f"Error handling error in agent {agent.name}: {str(handle_e)}")
                context.add_error(
                    agent.agent_id,
                    f"Failed to execute and handle error: {str(e)}. Handler error: {str(handle_e)}"
                )
                return agent, context
    
    async def execute_agents(self, 
                             agent_ids: List[str],
                             context: AgentContext,
                             sequential: bool = True) -> AgentContext:
        """
        Execute multiple agents with the given context.
        
        Args:
            agent_ids: List of agent IDs to execute
            context: The current context
            sequential: If True, execute agents sequentially; otherwise in parallel
            
        Returns:
            Updated context after all agents have executed
        """
        if not agent_ids:
            logger.warning("No agents specified for execution")
            return context
            
        # Resolve agent IDs to actual agent instances
        agents = []
        for agent_id in agent_ids:
            agent = self.registry.get_agent(agent_id)
            if agent:
                agents.append(agent)
            else:
                logger.warning(f"Agent {agent_id} not found in registry")
                context.add_error("orchestrator", f"Agent {agent_id} not found")
                
        if not agents:
            logger.warning("No valid agents to execute")
            return context
            
        # Execute agents according to the specified strategy
        if sequential:
            # Execute agents one at a time, passing context sequentially
            for agent in agents:
                _, context = await self.execute_single_agent(agent, context)
                
            return context
        else:
            # Execute agents in parallel
            # Note: Each agent gets a copy of the initial context
            # Results will be merged afterward
            tasks = []
            for agent in agents:
                # Create a shallow copy of context for each agent
                agent_context = AgentContext(
                    query=context.query,
                    conversation_id=context.conversation_id,
                    metadata=context.metadata.copy()
                )
                # Copy relevant parts of original context
                agent_context.short_term_memory = context.short_term_memory.copy()
                
                # Create task for this agent
                task = asyncio.create_task(
                    self.execute_single_agent(agent, agent_context)
                )
                tasks.append((agent, task))
                
            # Wait for all agents to complete
            agent_results = []
            for agent, task in tasks:
                try:
                    _, agent_context = await task
                    agent_results.append((agent, agent_context))
                except Exception as e:
                    logger.error(f"Error in parallel execution of agent {agent.name}: {str(e)}")
                    context.add_error(agent.agent_id, f"Parallel execution failed: {str(e)}")
            
            # Merge results into the original context
            for agent, agent_context in agent_results:
                # Merge memory entries
                context.short_term_memory.extend(agent_context.short_term_memory)
                
                # Merge results
                for key, value in agent_context.results.items():
                    context.results[f"{agent.agent_id}_{key}"] = value
                    
                # Merge citations
                context.citations.extend(agent_context.citations)
                
                # Merge errors
                context.errors.extend(agent_context.errors)
                
            # Update timestamp
            context.updated_at = datetime.now()
            
            return context
    
    async def execute_workflow(self,
                               workflow_id: str,
                               context: AgentContext) -> AgentContext:
        """
        Execute a predefined workflow of agents.
        
        Args:
            workflow_id: ID of the workflow to execute
            context: The current context
            
        Returns:
            Updated context after workflow execution
        """
        workflow = self.registry.get_workflow(workflow_id)
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            context.add_error("orchestrator", f"Workflow {workflow_id} not found")
            return context
            
        logger.info(f"Executing workflow: {workflow['name']} ({workflow_id})")
        
        # Record active workflow
        self.active_workflows[context.conversation_id] = {
            "workflow_id": workflow_id,
            "start_time": datetime.now(),
            "steps_completed": 0,
            "steps_total": len(workflow["steps"])
        }
        
        # Execute each step in the workflow
        for i, step in enumerate(workflow["steps"]):
            step_id = step.get("id", f"step_{i+1}")
            step_agents = step.get("agents", [])
            step_parallel = step.get("parallel", False)
            
            logger.info(f"Executing workflow step {step_id}: {step_agents}")
            
            # Execute the agents in this step
            context = await self.execute_agents(
                agent_ids=step_agents,
                context=context,
                sequential=not step_parallel
            )
            
            # Update workflow progress
            workflow_state = self.active_workflows.get(context.conversation_id)
            if workflow_state:
                workflow_state["steps_completed"] = i + 1
                
            # Check for termination condition
            if step.get("is_terminal", False) or context.metadata.get("terminate_workflow", False):
                logger.info(f"Workflow {workflow_id} terminated after step {step_id}")
                break
                
        # Remove from active workflows
        self.active_workflows.pop(context.conversation_id, None)
        
        # Mark workflow as completed in context
        context.metadata["completed_workflow"] = workflow_id
        context.metadata["workflow_completed_at"] = datetime.now().isoformat()
        
        return context
    
    async def dynamic_orchestration(self, context: AgentContext) -> AgentContext:
        """
        Dynamically orchestrate agents based on query analysis and context.
        
        Args:
            context: The current context
            
        Returns:
            Updated context after dynamic orchestration
        """
        # Retrieve all available agents
        all_agents = self.registry.list_agents()
        
        # First, we need to determine which agents can handle this context
        capable_agents = []
        for agent in all_agents:
            try:
                can_handle = await agent.can_handle(context)
                if can_handle:
                    capable_agents.append(agent)
            except Exception as e:
                logger.warning(f"Error checking if agent {agent.name} can handle context: {str(e)}")
        
        if not capable_agents:
            logger.warning("No agents can handle this context")
            context.add_error("orchestrator", "No agents can handle this context")
            return context
            
        logger.info(f"Found {len(capable_agents)} agents capable of handling this context")
        
        # Determine the best execution strategy based on agent roles
        # For now, we'll use a simple heuristic:
        # 1. Start with Research agents (data gathering)
        # 2. Then Process agents (reasoning, analysis)
        # 3. Finally Response agents (synthesis, generation)
        
        role_ordering = {
            "research": 1,    # Research roles first
            "retrieval": 1,
            "planning": 2,    # Planning second
            "reasoning": 3,   # Reasoning third
            "synthesis": 4,   # Synthesis fourth 
            "response": 5     # Response last
        }
        
        # Sort agents by role priority
        capable_agents.sort(key=lambda a: role_ordering.get(a.role.lower(), 99))
        
        # Execute agents in priority order
        for agent in capable_agents:
            _, context = await self.execute_single_agent(agent, context)
            
            # Check if we should stop processing
            if context.metadata.get("terminate_orchestration", False):
                logger.info(f"Orchestration terminated by agent {agent.name}")
                break
        
        return context
        
    async def execute_strategy(self, 
                               strategy: str,
                               context: AgentContext,
                               **kwargs) -> AgentContext:
        """
        Execute a specific orchestration strategy.
        
        Args:
            strategy: The orchestration strategy to use
            context: The current context
            **kwargs: Additional arguments for the strategy
            
        Returns:
            Updated context after executing the strategy
        """
        if strategy == "single_agent":
            agent_id = kwargs.get("agent_id")
            if not agent_id:
                raise ValueError("agent_id must be provided for single_agent strategy")
                
            agent = self.registry.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
                
            _, context = await self.execute_single_agent(agent, context)
            return context
            
        elif strategy == "sequential":
            agent_ids = kwargs.get("agent_ids", [])
            if not agent_ids:
                raise ValueError("agent_ids must be provided for sequential strategy")
                
            return await self.execute_agents(agent_ids, context, sequential=True)
            
        elif strategy == "parallel":
            agent_ids = kwargs.get("agent_ids", [])
            if not agent_ids:
                raise ValueError("agent_ids must be provided for parallel strategy")
                
            return await self.execute_agents(agent_ids, context, sequential=False)
            
        elif strategy == "workflow":
            workflow_id = kwargs.get("workflow_id")
            if not workflow_id:
                raise ValueError("workflow_id must be provided for workflow strategy")
                
            return await self.execute_workflow(workflow_id, context)
            
        elif strategy == "dynamic":
            return await self.dynamic_orchestration(context)
            
        else:
            raise ValueError(f"Unknown orchestration strategy: {strategy}")
    
    def get_execution_telemetry(self) -> Dict[str, Any]:
        """
        Get telemetry data about agent executions.
        
        Returns:
            Dictionary containing execution telemetry
        """
        # Aggregate execution statistics
        agent_stats = {}
        for execution in self.execution_history:
            agent_id = execution["agent_id"]
            if agent_id not in agent_stats:
                agent_stats[agent_id] = {
                    "name": execution["agent_name"],
                    "executions": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_time": 0,
                    "avg_time": 0
                }
                
            stats = agent_stats[agent_id]
            stats["executions"] += 1
            stats["successful"] += 1 if execution["success"] else 0
            stats["failed"] += 0 if execution["success"] else 1
            stats["total_time"] += execution.get("execution_time", 0)
            
        # Calculate averages
        for agent_id, stats in agent_stats.items():
            if stats["executions"] > 0:
                stats["avg_time"] = stats["total_time"] / stats["executions"]
                
        return {
            "agent_stats": agent_stats,
            "total_executions": len(self.execution_history),
            "active_workflows": len(self.active_workflows)
        }
