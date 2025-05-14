#!/usr/bin/env python3
"""
Test script for Agent Registry and Handoff Protocol.

This script demonstrates basic functionality of the Agent Registry
and Handoff Protocol by registering example agents and simulating handoffs.
"""

import os
import sys
import time
import logging
import argparse
from typing import Dict, Any

from backend.agent_registry import (
    get_registry, AgentCapability, CapabilityType, HandoffTrigger,
    register_agent, AgentConfig, AgentMetadata
)
from backend.agent_handoff import get_handoff_manager, Session
from backend.agents.base_agent import BaseAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Example Agent classes
class TestAgentA(BaseAgent):
    """Simple test agent that echoes messages"""
    
    def process_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Agent A processing: {message}")
        
        # Check for handoff keyword
        if "handoff" in message.lower():
            return {
                "message": "I'll transfer you to Agent B for more help.",
                "handoff_to": "test_agent_b",
                "handoff_reason": "User requested handoff"
            }
        
        return {
            "message": f"Agent A response: You said '{message}'",
            "data": {"processed_by": "agent_a"}
        }


class TestAgentB(BaseAgent):
    """Another test agent"""
    
    def process_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Agent B processing: {message}")
        
        # Check for handoff context
        if "handoff_context" in context:
            return {
                "message": f"Agent B here! I received a handoff from Agent A. You said '{message}'",
                "data": {"processed_by": "agent_b", "handoff_received": True}
            }
        
        return {
            "message": f"Agent B response: You said '{message}'",
            "data": {"processed_by": "agent_b"}
        }


# Register the test agents
@register_agent(
    id="test_agent_a",
    name="Test Agent A",
    description="A simple test agent",
    version="1.0.0",
    capabilities={
        "echo": AgentCapability(
            type=CapabilityType.CONVERSATIONAL,
            description="Echoes user messages",
            ui_instructions=["show_confirmation_dialog"]
        )
    },
    handoff_triggers=[
        HandoffTrigger(
            target_agent_id="test_agent_b",
            description="Handoff when user mentions 'handoff'",
            keyword_patterns=["handoff", "transfer"]
        )
    ],
    priority=1
)
class RegisteredAgentA(TestAgentA):
    """Agent A registered with decorator"""
    pass


# Main test function
def run_tests():
    """Run tests for the Agent Registry and Handoff Protocol"""
    
    logger.info("Starting Agent Registry tests")
    
    # Get the registry
    registry = get_registry()
    
    # Register Agent B manually
    agent_b_metadata = AgentMetadata(
        id="test_agent_b",
        name="Test Agent B",
        description="Another test agent",
        version="1.0.0",
        capabilities={
            "advanced_echo": AgentCapability(
                type=CapabilityType.CONVERSATIONAL,
                description="Advanced message processing",
                ui_instructions=["show_selection_menu"]
            )
        },
        priority=2
    )
    registry.register_agent_type(agent_b_metadata, TestAgentB)
    
    logger.info("Registered test agents")
    
    # List all registered agents
    agent_types = registry.get_agent_types()
    logger.info(f"Registered agent types: {', '.join(agent_types.keys())}")
    
    # Test agent discovery
    echo_agents = registry.get_agents_by_capability(CapabilityType.CONVERSATIONAL)
    logger.info(f"Agents with conversational capability: {', '.join(echo_agents.keys())}")
    
    # Test UI instruction authorization
    dialog_agents = registry.find_agents_by_ui_instruction("show_confirmation_dialog")
    logger.info(f"Agents that can use confirmation dialogs: {', '.join(dialog_agents.keys())}")
    
    # Test agent instantiation
    config_a = AgentConfig(agent_id="test_agent_a")
    instance_id_a = registry.instantiate_agent(config_a)
    logger.info(f"Instantiated Agent A with instance ID: {instance_id_a}")
    
    # Test session and handoffs
    logger.info("\nTesting session and handoffs:")
    
    # Create a session with Agent A
    session = Session(
        session_id="test_session",
        registry=registry,
        initial_agent_id="test_agent_a"
    )
    
    # Process a message with Agent A
    logger.info("Sending message to Agent A")
    response_a = session.handle_message("Hello from the test script")
    logger.info(f"Response from Agent A: {response_a.get('message')}")
    
    # Trigger a handoff to Agent B
    logger.info("Sending message with handoff keyword")
    response_handoff = session.handle_message("I want to handoff to Agent B please")
    logger.info(f"Handoff response: {response_handoff.get('message')}")
    
    # Verify the handoff occurred
    if session.active_agent_id == "test_agent_b":
        logger.info("✅ Handoff successful: Active agent is now Agent B")
    else:
        logger.error(f"❌ Handoff failed: Active agent is {session.active_agent_id}")
    
    # Process a message with Agent B after handoff
    logger.info("Sending message to Agent B after handoff")
    response_b = session.handle_message("Did the handoff work?")
    logger.info(f"Response from Agent B: {response_b.get('message')}")
    
    # Get handoff history
    handoff_history = get_handoff_manager().get_handoff_history("test_session")
    logger.info(f"\nHandoff history: {len(handoff_history)} handoffs recorded")
    for i, handoff in enumerate(handoff_history):
        logger.info(f"Handoff {i+1}: {handoff.source_agent_id} -> {handoff.target_agent_id} ({handoff.reason})")
    
    logger.info("\nAll tests completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the Agent Registry and Handoff Protocol")
    parser.add_argument("--config", type=str, help="Path to agent configuration file")
    args = parser.parse_args()
    
    # Set environment variable for config if provided
    if args.config:
        os.environ["AGNO_AGENT_CONFIG"] = args.config
    
    try:
        run_tests()
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        sys.exit(1)