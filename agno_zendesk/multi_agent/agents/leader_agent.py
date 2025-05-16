"""
Leader Agent Implementation

This agent coordinates execution flow across multiple specialized agents,
determining which agents to involve based on query analysis.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
import json
import os
from datetime import datetime

from ..core.agent_interface import Agent, AgentContext
from ..registry.agent_registry import get_agent_registry

# For OpenAI integration
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("leader_agent")


class LeaderAgent(Agent):
    """
    Agent that serves as the orchestrator and coordinator for the multi-agent system.
    Analyzes queries to determine execution flow and agent selection.
    """
    
    def __init__(self, 
                 agent_id: str,
                 name: str,
                 description: str,
                 model: str = "gpt-4o",
                 temperature: float = 0.2):
        """
        Initialize the leader agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            description: Detailed description of the agent's purpose
            model: LLM model to use for query analysis
            temperature: Temperature for LLM calls
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            role="planning",
            model=model
        )
        
        self.temperature = temperature
        
    async def can_handle(self, context: AgentContext) -> bool:
        """
        Check if this agent can handle the given context.
        Leader agent can handle any context with a query.
        
        Args:
            context: The agent context
            
        Returns:
            True if the agent can handle the context, False otherwise
        """
        return bool(context.query.strip())
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze a query to determine the appropriate agent workflow.
        
        Args:
            query: The user query to analyze
            
        Returns:
            Dictionary containing query analysis results
        """
        logger.info(f"Analyzing query: {query}")
        
        # Get API key
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Initialize OpenAI client
        client = openai.AsyncOpenAI(api_key=openai_api_key)
        
        # System prompt for query analysis with domain-aware collection guidance
        system_prompt = (
            f"You are a query analysis system for a multi-agent architecture specialized in astronomy software and equipment. "
            f"Your task is to analyze queries and determine which agent roles would be best for handling them. "
            f"You must identify the query domain and select the most relevant AstraDB collections based on that domain."
            f"\n\nAvailable Agent Roles:\n"
            f"- 'research': Retrieves information from databases\n"
            f"- 'synthesis': Combines information into coherent responses\n"
            f"- 'reasoning': Performs logical reasoning and analysis\n"
            f"- 'planning': Creates structured plans for complex queries\n"
            f"\n\nAvailable AstraDB Collections By Domain:\n"
            f"- SkySafari Domain: 'skysafari' (contains SkySafari app documentation and guides)\n"
            f"- Starry Night Domain: 'starrynight' (contains Starry Night software documentation), 'starry_night_faq' (contains Starry Night email/registration info)\n"
            f"- Celestron Telescopes Domain: 'celestron_pdfs' (contains Celestron telescope user guides)\n"
            f"- Multi-Domain Content: 'youtube' (contains videos about SkySafari, SkyPortal, Starry Night, and telescopes)\n"
            f"\n\nIMPORTANT SELECTION RULES:\n"
            f"1. For SkySafari-specific questions, use ONLY the 'skysafari' collection\n"
            f"2. For Starry Night-specific questions, use ONLY 'starrynight' and 'starry_night_faq' collections\n"
            f"3. For Celestron telescope questions, use ONLY the 'celestron_pdfs' collection\n"
            f"4. For questions about media content or video tutorials, include the 'youtube' collection\n"
            f"5. For questions that span multiple domains (e.g., 'How to use Celestron with SkySafari?'), include the relevant collections from each domain\n"
            f"6. NEVER include collections from unrelated domains - this causes confusion in the response\n"
        )
        
        # User prompt for query analysis with domain identification
        user_prompt = (
            f"Analyze the following query:\n\n"
            f"{query}\n\n"
            f"Provide the following information in JSON format:\n"
            f"1. query_type: A classification of the query (e.g., 'informational', 'procedural', 'troubleshooting')\n"
            f"2. agent_roles: An array of agent roles to involve, in the order they should execute\n"
            f"3. domain: The primary domain of the query (e.g., 'SkySafari', 'Starry Night', 'Celestron', or 'Multiple')\n"
            f"4. collections: An array of AstraDB collections to search based on the domain\n"
            f"5. reasoning: A brief explanation of your domain identification and collection selection\n"
        )
        
        # Call the OpenAI API
        response = await client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature
        )
        
        # Extract and parse the JSON response
        try:
            analysis = json.loads(response.choices[0].message.content)
            logger.info(f"Query analysis completed: {analysis}")
            return analysis
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing query analysis response: {str(e)}")
            # Return a default analysis with domain-specific collections
            return {
                "query_type": "informational",
                "agent_roles": ["research", "synthesis"],
                "domain": "Multiple",
                "collections": ["skysafari", "youtube"],  # Default to SkySafari collection and videos as a fallback
                "reasoning": "Failed to parse analysis, using default workflow with SkySafari collections"
            }
    
    async def process(self, context: AgentContext) -> AgentContext:
        """
        Process the given context by orchestrating the agent workflow.
        
        Args:
            context: The agent context
            
        Returns:
            Updated context after the workflow execution
        """
        query = context.query
        logger.info(f"Leader agent processing query: {query}")
        
        try:
            # Analyze the query
            analysis = await self.analyze_query(query)
            
            # Store the analysis in the context
            context.set_result("query_analysis", analysis)
            
            # Add to context metadata for other agents to use
            context.metadata["query_type"] = analysis.get("query_type", "informational")
            context.metadata["target_collections"] = analysis.get("collections", ["ss_guide"])
            
            # Get the agent registry
            registry = get_agent_registry()
            
            # Set up the agent workflow based on analysis
            agent_roles = analysis.get("agent_roles", ["research", "synthesis"])
            
            # Add memory entry for query analysis
            context.update_memory({
                "agent": self.name,
                "action": "query_analysis",
                "query_type": analysis.get("query_type", "informational"),
                "agent_roles": agent_roles,
                "collections": analysis.get("collections", ["ss_guide"]),
                "timestamp": datetime.now().isoformat()
            })
            
            # Generate execution plan
            execution_plan = {
                "plan_id": f"plan_{context.conversation_id}",
                "query": query,
                "query_type": analysis.get("query_type", "informational"),
                "agent_sequence": agent_roles,
                "target_collections": analysis.get("collections", ["ss_guide"]),
                "reasoning": analysis.get("reasoning", "Default execution plan"),
                "created_at": datetime.now().isoformat()
            }
            
            context.set_result("execution_plan", execution_plan)
            
            logger.info(f"Leader agent completed processing. Execution plan: {execution_plan}")
            return context
            
        except Exception as e:
            logger.error(f"Error in leader agent: {str(e)}")
            context.add_error(
                self.agent_id,
                f"Leader agent processing failed: {str(e)}"
            )
            
            # Create a fallback execution plan
            fallback_plan = {
                "plan_id": f"fallback_{context.conversation_id}",
                "query": query,
                "query_type": "informational",
                "agent_sequence": ["research", "synthesis"],
                "target_collections": ["ss_guide"],
                "reasoning": f"Fallback due to error: {str(e)}",
                "created_at": datetime.now().isoformat()
            }
            
            context.set_result("execution_plan", fallback_plan)
            return context
