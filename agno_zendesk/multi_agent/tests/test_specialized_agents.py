"""
Test Specialized Agents in Multi-Agent RAG System

This script tests the specialized agents (reasoning, reflection) in the 
multi-agent RAG system with AstraDB integration.
"""

import asyncio
import os
import json
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agno_zendesk.multi_agent.core.agent_interface import AgentContext
from agno_zendesk.multi_agent.agents.reasoning_agent import ReasoningAgent
from agno_zendesk.multi_agent.agents.reflection_agent import ReflectionAgent
from agno_zendesk.multi_agent.agents.synthesis_agent import SynthesisAgent
from agno_zendesk.multi_agent.core.astradb_connector import get_astradb_connector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_specialized_agents")


async def prepare_test_context() -> AgentContext:
    """
    Prepare a test context with sample data for agent testing.
    
    Returns:
        AgentContext with sample data
    """
    # Sample query for testing
    query = "Why do I need to use two-factor authentication for my Zendesk account?"
    
    # Create a context
    context = AgentContext(query=query)
    
    # Sample formatted context (simulating research agent output)
    formatted_context = (
        "[1] (Collection: ss_guide, Relevance: High)\n"
        "Two-factor authentication adds an extra layer of security to your Zendesk account. "
        "When enabled, you'll need both your password and a verification code sent to your "
        "mobile device to sign in. This prevents unauthorized access even if your password "
        "is compromised.\n"
        "\n---\n"
        "[2] (Collection: ss_guide, Relevance: Medium)\n"
        "Zendesk requires admin users to set up two-factor authentication as part of our "
        "security compliance policies. This helps protect sensitive customer data and "
        "maintain GDPR and other regulatory compliance.\n"
        "\n---\n"
        "[3] (Collection: kb_articles, Relevance: Medium)\n"
        "Recent security breaches at various SaaS companies have highlighted the importance "
        "of using two-factor authentication. Password-only authentication is increasingly "
        "vulnerable to sophisticated phishing attacks.\n"
        "\n\nCitation Policy:\n"
        "- Every statement must reference at least one citation\n"
        "- Only use citations [1], [2], [3]\n"
        "- If information is not found in citations, clearly indicate this\n"
    )
    
    # Sample research results (simulating what would come from AstraDB)
    context.set_result("formatted_context", formatted_context)
    context.set_result("raw_search_results", {
        "ss_guide": [
            {
                "text": "Two-factor authentication adds an extra layer of security to your Zendesk account. "
                        "When enabled, you'll need both your password and a verification code sent to your "
                        "mobile device to sign in. This prevents unauthorized access even if your password "
                        "is compromised.",
                "$similarity": 0.88
            },
            {
                "text": "Zendesk requires admin users to set up two-factor authentication as part of our "
                        "security compliance policies. This helps protect sensitive customer data and "
                        "maintain GDPR and other regulatory compliance.",
                "$similarity": 0.79
            }
        ],
        "kb_articles": [
            {
                "text": "Recent security breaches at various SaaS companies have highlighted the importance "
                        "of using two-factor authentication. Password-only authentication is increasingly "
                        "vulnerable to sophisticated phishing attacks.",
                "$similarity": 0.75
            }
        ]
    })
    
    # Add citations
    context.add_citation(
        source="ss_guide",
        content="Two-factor authentication adds an extra layer of security to your Zendesk account. "
                "When enabled, you'll need both your password and a verification code sent to your "
                "mobile device to sign in. This prevents unauthorized access even if your password "
                "is compromised.",
        metadata={"relevance": "High", "id": 1}
    )
    
    context.add_citation(
        source="ss_guide",
        content="Zendesk requires admin users to set up two-factor authentication as part of our "
                "security compliance policies. This helps protect sensitive customer data and "
                "maintain GDPR and other regulatory compliance.",
        metadata={"relevance": "Medium", "id": 2}
    )
    
    context.add_citation(
        source="kb_articles",
        content="Recent security breaches at various SaaS companies have highlighted the importance "
                "of using two-factor authentication. Password-only authentication is increasingly "
                "vulnerable to sophisticated phishing attacks.",
        metadata={"relevance": "Medium", "id": 3}
    )
    
    return context


async def test_reasoning_agent():
    """Test the reasoning agent with sample data."""
    logger.info("Testing reasoning agent...")
    
    # Prepare test context
    context = await prepare_test_context()
    
    # Create reasoning agent
    reasoning_agent = ReasoningAgent(
        agent_id="test_reasoning_agent",
        name="Test Reasoning Agent",
        description="Test reasoning agent for unit tests",
        temperature=0.2  # Lower temperature for more deterministic results
    )
    
    # Check if agent can handle this context
    can_handle = await reasoning_agent.can_handle(context)
    logger.info(f"Reasoning agent can handle context: {can_handle}")
    
    if can_handle:
        # Process context with reasoning agent
        updated_context = await reasoning_agent.process(context)
        
        # Check results
        reasoning_analysis = updated_context.get_result("reasoning_analysis")
        if reasoning_analysis:
            logger.info("Reasoning agent successfully produced analysis")
            
            # Log a snippet of the analysis
            snippet = reasoning_analysis[:150] + "..." if len(reasoning_analysis) > 150 else reasoning_analysis
            logger.info(f"Analysis snippet: {snippet}")
            
            # Check for citations in the analysis
            citations_used = all(f"[{i}]" in reasoning_analysis for i in range(1, 4))
            logger.info(f"Uses all citations: {citations_used}")
            
            return True
        else:
            logger.error("Reasoning agent failed to produce analysis")
            return False
    else:
        logger.warning("Reasoning agent cannot handle this context")
        return False


async def test_synthesis_and_reflection_agents():
    """Test the synthesis and reflection agents in sequence."""
    logger.info("Testing synthesis and reflection agents...")
    
    # Prepare test context
    context = await prepare_test_context()
    
    # Create synthesis agent
    synthesis_agent = SynthesisAgent(
        agent_id="test_synthesis_agent",
        name="Test Synthesis Agent",
        description="Test synthesis agent for unit tests",
        temperature=0.2
    )
    
    # Process context with synthesis agent
    logger.info("Running synthesis agent...")
    synthesis_context = await synthesis_agent.process(context)
    
    # Check synthesis results
    synthesized_response = synthesis_context.get_result("synthesized_response")
    if not synthesized_response:
        logger.error("Synthesis agent failed to produce a response")
        return False
    
    logger.info("Synthesis agent successfully produced a response")
    snippet = synthesized_response[:150] + "..." if len(synthesized_response) > 150 else synthesized_response
    logger.info(f"Response snippet: {snippet}")
    
    # Create reflection agent
    reflection_agent = ReflectionAgent(
        agent_id="test_reflection_agent",
        name="Test Reflection Agent",
        description="Test reflection agent for unit tests",
        temperature=0.2
    )
    
    # Check if reflection agent can handle the context
    can_handle = await reflection_agent.can_handle(synthesis_context)
    logger.info(f"Reflection agent can handle context: {can_handle}")
    
    if can_handle:
        # Process context with reflection agent
        logger.info("Running reflection agent...")
        reflection_context = await reflection_agent.process(synthesis_context)
        
        # Check reflection results
        improved_response = reflection_context.get_result("improved_response")
        if improved_response:
            logger.info("Reflection agent successfully improved the response")
            
            # Log a snippet of the improved response
            snippet = improved_response[:150] + "..." if len(improved_response) > 150 else improved_response
            logger.info(f"Improved response snippet: {snippet}")
            
            # Get reflection metadata
            metadata = reflection_context.get_result("reflection_metadata")
            if metadata:
                original_length = metadata.get("original_length", 0)
                improved_length = metadata.get("improved_length", 0)
                logger.info(f"Original length: {original_length}, Improved length: {improved_length}")
            
            return True
        else:
            logger.error("Reflection agent failed to improve the response")
            return False
    else:
        logger.warning("Reflection agent cannot handle this context")
        return False


async def run_tests():
    """Run all tests."""
    # Check environment variables
    required_env_vars = ["OPENAI_API_KEY"]
    for var in required_env_vars:
        if not os.getenv(var):
            logger.error(f"Environment variable {var} is not set")
            return
    
    # Test reasoning agent
    reasoning_success = await test_reasoning_agent()
    
    # Test synthesis and reflection agents
    reflection_success = await test_synthesis_and_reflection_agents()
    
    # Report results
    logger.info("\nTest Results:")
    logger.info(f"Reasoning Agent Test: {'PASSED' if reasoning_success else 'FAILED'}")
    logger.info(f"Synthesis & Reflection Agents Test: {'PASSED' if reflection_success else 'FAILED'}")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_tests())
