"""
Test Widget Integration and Workflow Designer

This script tests the widget integration layer and workflow designer
components of the multi-agent RAG system with AstraDB integration.
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

from agno_zendesk.multi_agent.integration.widget_integration import get_widget_integration
from agno_zendesk.multi_agent.orchestration.workflow_designer import get_workflow_designer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_widget_integration")


async def test_workflow_designer():
    """Test the workflow designer's ability to analyze queries and design workflows."""
    logger.info("Testing workflow designer...")
    
    # Get the workflow designer
    designer = get_workflow_designer()
    
    # Test query types
    test_queries = [
        ("What is Zendesk?", "informational"),
        ("Why should I use two-factor authentication?", "reasoning"),
        ("How do I reset my password?", "procedural"),
        ("Compare Zendesk and Freshdesk", "comparative"),
        ("What's the best plan for a small business?", "recommendation"),
        ("Give me a detailed explanation of Zendesk's data model", "complex")
    ]
    
    # Test query analysis
    for query, expected_type in test_queries:
        query_type = await designer.analyze_query_type(query)
        match = query_type == expected_type
        logger.info(f"Query: '{query}'")
        logger.info(f"  Expected type: {expected_type}")
        logger.info(f"  Actual type: {query_type}")
        logger.info(f"  Match: {'✓' if match else '✗'}")
        
    # Test workflow design
    query = "Why should I use Zendesk for my customer support?"
    workflow = await designer.design_workflow(query)
    
    logger.info(f"Designed workflow: {workflow.get('id', 'unknown')}")
    logger.info(f"  Name: {workflow.get('name', 'unknown')}")
    logger.info(f"  Steps: {len(workflow.get('steps', []))}")
    
    # Test template listing
    templates = designer.list_templates()
    logger.info(f"Available templates: {len(templates)}")
    for template in templates:
        logger.info(f"  Template: {template.get('name')} ({template.get('id')})")
    
    return True


async def test_widget_integration():
    """Test the widget integration layer."""
    logger.info("Testing widget integration...")
    
    # Get the widget integration
    integration = get_widget_integration()
    
    # Test widget initialization
    config = await integration.initialize_widget()
    logger.info(f"Widget initialized with ID: {config.get('widget_id')}")
    logger.info(f"  Available workflows: {len(config.get('available_workflows', []))}")
    logger.info(f"  Available collections: {config.get('available_collections', [])}")
    
    # Test query processing
    query = "How do I set up Zendesk for my support team?"
    logger.info(f"Processing query: {query}")
    
    response = await integration.process_widget_query(
        query=query,
        conversation_id="test_conversation_1",
        metadata={"test": True, "source": "unit_test"}
    )
    
    logger.info(f"Response received in {response.get('processing_time', 0):.2f}s")
    logger.info(f"  Response length: {len(response.get('response', ''))}")
    logger.info(f"  Citations: {len(response.get('citations', []))}")
    
    # Test feedback processing
    feedback_result = await integration.provide_feedback(
        conversation_id="test_conversation_1",
        feedback={"helpful": True, "rating": 5, "comments": "Great response!"}
    )
    
    logger.info(f"Feedback processed: {feedback_result.get('status')}")
    
    return True


async def run_tests():
    """Run all tests."""
    # Check environment variables
    required_env_vars = ["ASTRA_ENDPOINT", "ASTRA_TOKEN", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Tests will be skipped")
        return
    
    # Test workflow designer
    try:
        workflow_designer_result = await test_workflow_designer()
    except Exception as e:
        logger.error(f"Error testing workflow designer: {str(e)}")
        workflow_designer_result = False
    
    # Test widget integration
    try:
        widget_integration_result = await test_widget_integration()
    except Exception as e:
        logger.error(f"Error testing widget integration: {str(e)}")
        widget_integration_result = False
    
    # Report results
    logger.info("\nTest Results:")
    logger.info(f"Workflow Designer Test: {'PASSED' if workflow_designer_result else 'FAILED'}")
    logger.info(f"Widget Integration Test: {'PASSED' if widget_integration_result else 'FAILED'}")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_tests())
