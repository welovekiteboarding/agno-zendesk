"""
Reasoning Agent Implementation

This agent specializes in performing logical reasoning and analysis on information
retrieved from AstraDB, helping to evaluate and compare options.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
import json
import os
from datetime import datetime

from ..core.agent_interface import Agent, AgentContext

# For OpenAI integration
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reasoning_agent")


class ReasoningAgent(Agent):
    """
    Agent specializing in logical reasoning and analysis.
    Analyzes context from other agents to draw logical conclusions.
    """
    
    def __init__(self, 
                 agent_id: str,
                 name: str,
                 description: str,
                 model: str = "gpt-4o",
                 temperature: float = 0.3,
                 max_tokens: int = 1000):
        """
        Initialize the reasoning agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            description: Detailed description of the agent's purpose
            model: LLM model to use for reasoning
            temperature: Temperature for LLM calls
            max_tokens: Maximum tokens for responses
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            role="reasoning",
            model=model
        )
        
        self.temperature = temperature
        self.max_tokens = max_tokens
        
    async def can_handle(self, context: AgentContext) -> bool:
        """
        Check if this agent can handle the given context.
        Reasoning agent requires research results to work with.
        
        Args:
            context: The agent context
            
        Returns:
            True if the agent can handle the context, False otherwise
        """
        # We need formatted context or citations to analyze
        has_formatted_context = "formatted_context" in context.results
        has_citations = len(context.citations) > 0
        
        # We also check if this query needs reasoning/analysis
        query_requires_reasoning = self._query_requires_reasoning(context.query)
        
        return (has_formatted_context or has_citations) and query_requires_reasoning
    
    def _query_requires_reasoning(self, query: str) -> bool:
        """
        Determine if a query likely requires reasoning.
        
        Args:
            query: The user query
            
        Returns:
            True if the query likely requires reasoning, False otherwise
        """
        reasoning_indicators = [
            "why", "how", "explain", "analyze", "compare", "contrast", 
            "evaluate", "pros and cons", "benefits", "drawbacks",
            "should I", "better", "worse", "differences", "similarities"
        ]
        
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in reasoning_indicators)
    
    def _build_system_prompt(self, context: AgentContext) -> str:
        """
        Build the system prompt for the reasoning agent.
        
        Args:
            context: The agent context
            
        Returns:
            System prompt for the LLM
        """
        system_prompt = (
            f"You are a reasoning agent that analyzes information to reach logical conclusions. "
            f"Your task is to carefully analyze the context provided and draw well-supported conclusions. "
            f"\n\nGuidelines:\n"
            f"1. Carefully analyze all information in the provided context.\n"
            f"2. Identify key facts, principles, and relationships between concepts.\n"
            f"3. Apply logical reasoning to draw well-supported conclusions.\n"
            f"4. Always cite specific pieces of information from the context using [X] citation format.\n"
            f"5. Evaluate different perspectives or options when appropriate.\n"
            f"6. Acknowledge limitations and uncertainties in your analysis.\n"
            f"7. Organize your reasoning in a clear, step-by-step manner.\n"
            f"8. Focus on explaining WHY and HOW rather than just WHAT.\n"
        )
        
        return system_prompt
    
    def _build_user_prompt(self, context: AgentContext) -> str:
        """
        Build the user prompt for the reasoning agent.
        
        Args:
            context: The agent context
            
        Returns:
            User prompt for the LLM
        """
        # Get the formatted context with citations
        formatted_context = context.get_result("formatted_context")
        
        # Build the user prompt
        user_prompt = (
            f"Query requiring analysis: {context.query}\n\n"
            f"Context with Citations:\n"
            f"{formatted_context}\n\n"
            f"Please carefully analyze this information and provide a logical, well-reasoned analysis. "
            f"Focus on explaining the underlying principles, cause-effect relationships, and drawing "
            f"well-supported conclusions. Use citations [X] to reference specific information from the context."
        )
        
        return user_prompt
        
    async def process(self, context: AgentContext) -> AgentContext:
        """
        Process the given context by applying logical reasoning.
        
        Args:
            context: The agent context
            
        Returns:
            Updated context with reasoning analysis
        """
        logger.info(f"Reasoning agent processing query: {context.query}")
        
        try:
            # Build prompts
            system_prompt = self._build_system_prompt(context)
            user_prompt = self._build_user_prompt(context)
            
            # Get API key
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            # Initialize OpenAI client
            client = openai.AsyncOpenAI(api_key=openai_api_key)
            
            # Call the OpenAI API
            logger.info(f"Calling OpenAI with model: {self.model}")
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Extract the response text
            reasoning_analysis = response.choices[0].message.content
            
            # Add the analysis to the context
            context.set_result("reasoning_analysis", reasoning_analysis)
            
            # Add memory entry for this operation
            context.update_memory({
                "agent": self.name,
                "action": "reasoning",
                "analysis_length": len(reasoning_analysis) if reasoning_analysis else 0,
                "model_used": self.model,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Reasoning analysis completed successfully")
            return context
            
        except Exception as e:
            logger.error(f"Error in reasoning agent: {str(e)}")
            context.add_error(
                self.agent_id,
                f"Reasoning analysis failed: {str(e)}"
            )
            return context
