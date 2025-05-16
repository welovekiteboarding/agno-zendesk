"""
Test Script for Multi-Agent RAG System with AstraDB

This script tests the multi-agent RAG system with AstraDB integration.
It executes a sample query through the system and displays the results.
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

from agno_zendesk.multi_agent.core.system import get_multi_agent_system
from agno_zendesk.multi_agent.core.astradb_connector import get_astradb_connector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_multi_agent_rag")


async def verify_astradb_connection() -> bool:
    """Verify connection to AstraDB."""
    try:
        connector = await get_astradb_connector()
        return True
    except Exception as e:
        logger.error(f"Failed to connect to AstraDB: {str(e)}")
        return False


async def test_multi_agent_rag(query: str) -> Dict[str, Any]:
    """
    Test the multi-agent RAG system with a query.
    
    Args:
        query: The query to test
        
    Returns:
        Dictionary containing test results
    """
    logger.info(f"Testing multi-agent RAG system with query: {query}")
    
    # Check environment variables
    required_env_vars = ["ASTRA_ENDPOINT", "ASTRA_TOKEN", "OPENAI_API_KEY"]
    for var in required_env_vars:
        if not os.getenv(var):
            logger.error(f"Environment variable {var} is not set")
            return {"success": False, "error": f"Environment variable {var} is not set"}
    
    # Verify AstraDB connection
    astra_connection = await verify_astradb_connection()
    if not astra_connection:
        return {"success": False, "error": "Failed to connect to AstraDB"}
    
    # Initialize the multi-agent system
    collections = ["ss_guide"]  # Use only the ss_guide collection for this test
    system = get_multi_agent_system(collections=collections)
    
    # Process the query
    start_time = datetime.now()
    result = await system.process_query(query=query)
    processing_time = (datetime.now() - start_time).total_seconds()
    
    # Add test metadata
    test_result = {
        "success": True,
        "query": query,
        "processing_time": processing_time,
        "system_info": system.get_system_info(),
        "result": result
    }
    
    return test_result


async def run_test() -> None:
    """Run the test with a sample query."""
    # Sample query
    query = "How do I reset my password in the Zendesk admin portal?"
    
    # Run the test
    test_result = await test_multi_agent_rag(query)
    
    # Display results
    if test_result.get("success", False):
        logger.info("Test Successful!")
        logger.info(f"Query: {test_result['query']}")
        logger.info(f"Processing Time: {test_result['processing_time']:.2f} seconds")
        
        # Display the response
        response = test_result.get("result", {}).get("response", "No response generated")
        logger.info("\nGenerated Response:")
        print("\n" + "="*80)
        print(response)
        print("="*80 + "\n")
        
        # Display system info
        system_info = test_result.get("system_info", {})
        agent_count = system_info.get("registry", {}).get("agent_count", 0)
        workflow_count = system_info.get("registry", {}).get("workflow_count", 0)
        logger.info(f"System Info: {agent_count} agents, {workflow_count} workflows")
        
    else:
        logger.error(f"Test Failed: {test_result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    # Run the test
    asyncio.run(run_test())
