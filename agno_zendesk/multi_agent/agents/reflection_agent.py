"""
Reflection Agent Implementation

This agent specializes in analyzing and improving responses from other agents,
ensuring accuracy, completeness, and alignment with best practices.
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
logger = logging.getLogger("reflection_agent")


class ReflectionAgent(Agent):
    """
    Agent specializing in analyzing and improving responses.
    Acts as a final review step before delivering responses to users.
    """
    
    def __init__(self, 
                 agent_id: str,
                 name: str,
                 description: str,
                 model: str = "gpt-4o",
                 temperature: float = 0.3,
                 max_tokens: int = 1000,
                 check_hallucinations: bool = True,
                 check_completeness: bool = True,
                 improve_formatting: bool = True):
        """
        Initialize the reflection agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            description: Detailed description of the agent's purpose
            model: LLM model to use for reflection
            temperature: Temperature for LLM calls
            max_tokens: Maximum tokens for responses
            check_hallucinations: Whether to check for hallucinations
            check_completeness: Whether to check for completeness
            improve_formatting: Whether to improve response formatting
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            role="reflection",
            model=model
        )
        
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.check_hallucinations = check_hallucinations
        self.check_completeness = check_completeness
        self.improve_formatting = improve_formatting
        
    async def can_handle(self, context: AgentContext) -> bool:
        """
        Check if this agent can handle the given context.
        Reflection agent requires a synthesized response to reflect on.
        
        Args:
            context: The agent context
            
        Returns:
            True if the agent can handle the context, False otherwise
        """
        # We need a synthesized response to reflect on
        has_synthesized_response = "synthesized_response" in context.results
        
        return has_synthesized_response
    
    def _build_system_prompt(self, context: AgentContext) -> str:
        """
        Build the system prompt for the reflection agent.
        
        Args:
            context: The agent context
            
        Returns:
            System prompt for the LLM
        """
        system_prompt = (
            f"You are a reflection agent that analyzes and improves responses before they're delivered to users. "
            f"Your task is to ensure responses are accurate, complete, well-formatted, and helpful. "
            f"\n\nGuidelines:\n"
        )
        
        if self.check_hallucinations:
            system_prompt += (
                f"1. Check for hallucinations or unsupported claims:\n"
                f"   - Verify all factual statements are supported by the provided context\n"
                f"   - Ensure citations are used correctly\n"
                f"   - Remove or modify any claims that aren't supported by the context\n"
            )
        
        if self.check_completeness:
            system_prompt += (
                f"2. Check for completeness:\n"
                f"   - Ensure the response fully addresses the user's query\n"
                f"   - Verify that no important information from the context was omitted\n"
                f"   - Add any missing relevant information from the context\n"
            )
        
        if self.improve_formatting:
            system_prompt += (
                f"3. Improve formatting and readability:\n"
                f"   - Ensure clear paragraph structure and logical flow\n"
                f"   - Add headers or bullet points if they would improve clarity\n"
                f"   - Make sure citations are formatted consistently\n"
            )
        
        system_prompt += (
            f"\nProduce an improved version of the response that maintains the core information "
            f"while addressing any issues you identify. Maintain all citations in the format [X]."
        )
        
        return system_prompt
    
    def _build_user_prompt(self, context: AgentContext) -> str:
        """
        Build the user prompt for the reflection agent.
        
        Args:
            context: The agent context
            
        Returns:
            User prompt for the LLM
        """
        # Get the original query and synthesized response
        query = context.query
        synthesized_response = context.get_result("synthesized_response")
        
        # Get the original context with citations
        formatted_context = context.get_result("formatted_context")
        
        # Build the user prompt
        user_prompt = (
            f"Original Query: {query}\n\n"
            f"Current Response:\n{synthesized_response}\n\n"
            f"Original Context:\n{formatted_context}\n\n"
            f"Please analyze this response and improve it by:\n"
        )
        
        if self.check_hallucinations:
            user_prompt += "- Checking for and correcting any hallucinations or unsupported claims\n"
        
        if self.check_completeness:
            user_prompt += "- Ensuring the response completely addresses the original query\n"
        
        if self.improve_formatting:
            user_prompt += "- Improving formatting and readability while maintaining all citations\n"
        
        user_prompt += "\nProvide the improved response:"
        
        return user_prompt
        
    async def process(self, context: AgentContext) -> AgentContext:
        """
        Process the given context by reflecting on and improving the synthesized response.
        
        Args:
            context: The agent context
            
        Returns:
            Updated context with improved response
        """
        logger.info(f"Reflection agent processing response for query: {context.query}")
        
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
            improved_response = response.choices[0].message.content
            
            # Get the original response for comparison
            original_response = context.get_result("synthesized_response")
            
            # Add the improved response to the context
            context.set_result("improved_response", improved_response)
            
            # Replace the synthesized response with the improved one
            context.set_result("synthesized_response", improved_response)
            
            # Store the reflection metadata
            reflection_metadata = {
                "original_length": len(original_response) if original_response else 0,
                "improved_length": len(improved_response) if improved_response else 0,
                "timestamp": datetime.now().isoformat()
            }
            context.set_result("reflection_metadata", reflection_metadata)
            
            # Add memory entry for this operation
            context.update_memory({
                "agent": self.name,
                "action": "reflection",
                "reflection_metadata": reflection_metadata,
                "model_used": self.model,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Reflection completed successfully")
            return context
            
        except Exception as e:
            logger.error(f"Error in reflection agent: {str(e)}")
            context.add_error(
                self.agent_id,
                f"Reflection failed: {str(e)}"
            )
            return context
