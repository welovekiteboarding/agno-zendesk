"""
Agent Registry: Centralized agent registration system with handoff protocol support

This module implements a registry for all agents in the system, allowing:
- Agent registration with metadata
- Agent discovery by capabilities and ID
- Handoff trigger definition and evaluation
- Agent instantiation from configuration
"""

import os
import json
import yaml
import logging
import importlib
import inspect
from typing import Dict, List, Set, Any, Optional, Callable, Type, Union, TypeVar
from enum import Enum
from pathlib import Path
from functools import wraps
from pydantic import BaseModel, Field, validator

# Set up logging
logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar('T')
AgentClass = TypeVar('AgentClass')
TriggerFunction = Callable[[Dict[str, Any]], bool]

class CapabilityType(str, Enum):
    """Enumeration of different capability types that agents can have"""
    CONVERSATIONAL = "conversational"
    FORM_COLLECTION = "form_collection"
    DATA_EXTRACTION = "data_extraction"
    EMAIL_VERIFICATION = "email_verification"
    TICKET_CREATION = "ticket_creation"
    FILE_PROCESSING = "file_processing"
    UI_INTERACTION = "ui_interaction"


class HandoffTrigger(BaseModel):
    """Definition of a trigger that causes handoff to another agent"""
    target_agent_id: str = Field(..., description="ID of the agent to hand off to")
    description: str = Field(..., description="Human-readable description of when this trigger activates")
    priority: int = Field(default=1, description="Priority of this trigger (higher numbers have precedence)")
    
    # One of the following must be provided
    condition_function: Optional[str] = Field(default=None, description="Name of function that evaluates to True/False")
    keyword_patterns: Optional[List[str]] = Field(default=None, description="List of regex patterns to match in messages")
    intent_names: Optional[List[str]] = Field(default=None, description="List of intent names that activate trigger")
    
    @validator('priority')
    def validate_priority(cls, v):
        if v < 0:
            raise ValueError("Priority must be a positive integer")
        return v
    
    @validator('condition_function', 'keyword_patterns', 'intent_names')
    def validate_trigger_condition(cls, v, values):
        # Ensure at least one trigger condition is specified
        if not values.get('condition_function') and not values.get('keyword_patterns') and not values.get('intent_names'):
            raise ValueError("At least one trigger condition must be specified")
        return v


class AgentCapability(BaseModel):
    """Definition of a capability that an agent provides"""
    type: CapabilityType = Field(..., description="Type of capability")
    description: str = Field(..., description="Description of what this capability does")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for this capability")
    ui_instructions: Optional[List[str]] = Field(default=None, description="UI instruction types this capability can use")


class AgentMetadata(BaseModel):
    """Metadata for an agent registered in the system"""
    id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Human-readable name of the agent")
    description: str = Field(..., description="Description of the agent's purpose")
    version: str = Field(..., description="Agent version")
    capabilities: Dict[str, AgentCapability] = Field(..., description="Map of capability IDs to definitions")
    input_format: Dict[str, Any] = Field(default_factory=dict, description="Expected input format")
    output_format: Dict[str, Any] = Field(default_factory=dict, description="Produced output format")
    handoff_triggers: List[HandoffTrigger] = Field(default_factory=list, description="Triggers for handing off to other agents")
    priority: int = Field(default=1, description="Agent priority (higher numbers have precedence in conflicts)")
    author: Optional[str] = Field(default=None, description="Author of the agent")
    requires: List[str] = Field(default_factory=list, description="IDs of other agents this agent depends on")
    rate_limits: Dict[str, int] = Field(default_factory=dict, description="Rate limits for various operations")
    configurable_params: Dict[str, Any] = Field(default_factory=dict, description="Parameters that can be configured")
    singleton: bool = Field(default=True, description="Whether only one instance of this agent should exist")


class AgentConfig(BaseModel):
    """Configuration for an agent instance"""
    agent_id: str = Field(..., description="ID of the agent type to instantiate")
    instance_id: Optional[str] = Field(default=None, description="Optional unique ID for this instance")
    enabled: bool = Field(default=True, description="Whether this agent is enabled")
    params: Dict[str, Any] = Field(default_factory=dict, description="Configuration parameters")


class AgentRegistryConfig(BaseModel):
    """Configuration for the entire agent registry"""
    agents: List[AgentConfig] = Field(default_factory=list, description="Agents to instantiate")
    default_agent_id: Optional[str] = Field(default=None, description="Default agent to use if no triggers match")
    hot_reload: bool = Field(default=False, description="Whether to watch for config changes and reload automatically")
    config_path: Optional[str] = Field(default=None, description="Path to the config file for hot-reloading")


class AgentRegistry:
    """
    Centralized registry for all agents in the system.
    
    The registry maintains metadata about available agent types,
    instantiates agents based on configuration, and handles
    agent handoff logic.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the agent registry.
        
        Args:
            config_path: Optional path to a YAML/JSON configuration file
        """
        # Registered agent types (metadata)
        self._agent_types: Dict[str, AgentMetadata] = {}
        
        # Instantiated agent instances
        self._agent_instances: Dict[str, Any] = {}
        
        # Classes for registered agent types
        self._agent_classes: Dict[str, Type] = {}
        
        # Default configuration
        self._config = AgentRegistryConfig()
        
        # Load configuration if provided
        if config_path:
            self.load_config(config_path)
    
    #
    # Agent Type Registration
    #
    
    def register_agent_type(self, metadata: AgentMetadata, agent_class: Type) -> None:
        """
        Register a new agent type in the registry.
        
        Args:
            metadata: Agent metadata
            agent_class: Class used to instantiate this agent type
        """
        if metadata.id in self._agent_types:
            logger.warning(f"Agent type {metadata.id} is already registered and will be overwritten")
        
        # Validate metadata
        self._validate_agent_metadata(metadata)
        
        # Store metadata and class
        self._agent_types[metadata.id] = metadata
        self._agent_classes[metadata.id] = agent_class
        
        logger.info(f"Registered agent type: {metadata.id} ({metadata.name})")
    
    def _validate_agent_metadata(self, metadata: AgentMetadata) -> None:
        """
        Validate agent metadata for consistency.
        
        Args:
            metadata: Agent metadata to validate
        
        Raises:
            ValueError: If the metadata is invalid
        """
        # Check for circular dependencies
        visited: Set[str] = set()
        to_visit: List[str] = metadata.requires.copy()
        
        while to_visit:
            agent_id = to_visit.pop()
            
            if agent_id == metadata.id:
                raise ValueError(f"Circular dependency detected for agent {metadata.id}")
            
            if agent_id in visited:
                continue
                
            visited.add(agent_id)
            
            if agent_id in self._agent_types:
                to_visit.extend(self._agent_types[agent_id].requires)
        
        # Validate handoff triggers
        for trigger in metadata.handoff_triggers:
            if trigger.target_agent_id == metadata.id:
                raise ValueError(f"Agent {metadata.id} cannot hand off to itself")
    
    def unregister_agent_type(self, agent_id: str) -> bool:
        """
        Unregister an agent type from the registry.
        
        Args:
            agent_id: ID of the agent type to unregister
            
        Returns:
            True if the agent was unregistered, False if it wasn't registered
        """
        if agent_id not in self._agent_types:
            return False
        
        # Check if any other agents depend on this one
        for other_id, metadata in self._agent_types.items():
            if agent_id in metadata.requires:
                logger.warning(f"Agent {other_id} depends on {agent_id}, which is being unregistered")
        
        # Remove all instances of this agent type
        instances_to_remove = [
            instance_id for instance_id, instance in self._agent_instances.items()
            if getattr(instance, "_agent_metadata", None) and instance._agent_metadata.id == agent_id
        ]
        
        for instance_id in instances_to_remove:
            self._agent_instances.pop(instance_id, None)
        
        # Remove the agent type
        self._agent_types.pop(agent_id)
        self._agent_classes.pop(agent_id)
        
        logger.info(f"Unregistered agent type: {agent_id}")
        return True
    
    #
    # Agent Instance Management
    #
    
    def instantiate_agent(self, config: AgentConfig) -> str:
        """
        Instantiate an agent based on configuration.
        
        Args:
            config: Agent configuration
            
        Returns:
            Instance ID of the created agent
            
        Raises:
            ValueError: If the agent type is not registered or instantiation fails
        """
        agent_id = config.agent_id
        
        if agent_id not in self._agent_types:
            raise ValueError(f"Agent type {agent_id} is not registered")
        
        metadata = self._agent_types[agent_id]
        agent_class = self._agent_classes[agent_id]
        
        # Check if this is a singleton agent and an instance already exists
        if metadata.singleton:
            for instance_id, instance in self._agent_instances.items():
                if getattr(instance, "_agent_metadata", None) and instance._agent_metadata.id == agent_id:
                    logger.info(f"Using existing singleton instance of {agent_id}")
                    return instance_id
        
        # Generate instance ID if not provided
        instance_id = config.instance_id or f"{agent_id}_{len(self._agent_instances) + 1}"
        
        # Check if instance ID is already in use
        if instance_id in self._agent_instances:
            raise ValueError(f"Agent instance ID {instance_id} is already in use")
        
        # Create agent instance
        try:
            logger.info(f"Instantiating agent {agent_id} as {instance_id}")
            
            # Create the agent instance with its configuration
            agent_instance = agent_class(**config.params)
            
            # Attach metadata to the instance
            agent_instance._agent_metadata = metadata
            agent_instance._instance_id = instance_id
            
            # Store the instance
            self._agent_instances[instance_id] = agent_instance
            
            return instance_id
            
        except Exception as e:
            logger.error(f"Failed to instantiate agent {agent_id}: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to instantiate agent {agent_id}: {str(e)}")
    
    def get_agent_instance(self, instance_id: str) -> Any:
        """
        Get an agent instance by ID.
        
        Args:
            instance_id: ID of the agent instance
            
        Returns:
            Agent instance
            
        Raises:
            ValueError: If the instance does not exist
        """
        if instance_id not in self._agent_instances:
            raise ValueError(f"Agent instance {instance_id} does not exist")
        
        return self._agent_instances[instance_id]
    
    def remove_agent_instance(self, instance_id: str) -> bool:
        """
        Remove an agent instance.
        
        Args:
            instance_id: ID of the agent instance to remove
            
        Returns:
            True if the instance was removed, False if it doesn't exist
        """
        if instance_id not in self._agent_instances:
            return False
        
        self._agent_instances.pop(instance_id)
        logger.info(f"Removed agent instance: {instance_id}")
        return True
    
    #
    # Configuration Management
    #
    
    def load_config(self, config_path: str) -> None:
        """
        Load configuration from a YAML or JSON file.
        
        Args:
            config_path: Path to the configuration file
            
        Raises:
            ValueError: If the configuration file is invalid or cannot be loaded
        """
        try:
            path = Path(config_path)
            
            if not path.exists():
                raise ValueError(f"Configuration file not found: {config_path}")
            
            # Load the configuration based on file extension
            if path.suffix.lower() in ('.yaml', '.yml'):
                with open(path, 'r') as f:
                    config_data = yaml.safe_load(f)
            elif path.suffix.lower() == '.json':
                with open(path, 'r') as f:
                    config_data = json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {path.suffix}")
            
            # Create configuration object
            self._config = AgentRegistryConfig.parse_obj(config_data)
            self._config.config_path = config_path
            
            # Instantiate agents from the configuration
            for agent_config in self._config.agents:
                if agent_config.enabled:
                    try:
                        self.instantiate_agent(agent_config)
                    except ValueError as e:
                        logger.error(f"Failed to instantiate agent {agent_config.agent_id}: {str(e)}")
            
            logger.info(f"Loaded configuration from {config_path}")
            
            # Set up hot-reloading if enabled
            if self._config.hot_reload:
                # Note: In a real implementation, this would set up a file watcher
                # to monitor changes to the config file and reload it automatically
                logger.info("Hot-reloading is enabled, but implementation is mock")
                
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to load configuration: {str(e)}")
    
    def save_config(self, config_path: Optional[str] = None) -> None:
        """
        Save current configuration to a file.
        
        Args:
            config_path: Path to save to (defaults to the loaded config path)
            
        Raises:
            ValueError: If no configuration path is provided and none was loaded
        """
        config_path = config_path or self._config.config_path
        
        if not config_path:
            raise ValueError("No configuration path provided and none was loaded")
        
        try:
            path = Path(config_path)
            
            # Convert configuration to a dictionary
            config_dict = self._config.dict(exclude={'config_path'})
            
            # Save based on file extension
            if path.suffix.lower() in ('.yaml', '.yml'):
                with open(path, 'w') as f:
                    yaml.dump(config_dict, f, default_flow_style=False)
            elif path.suffix.lower() == '.json':
                with open(path, 'w') as f:
                    json.dump(config_dict, f, indent=2)
            else:
                raise ValueError(f"Unsupported configuration file format: {path.suffix}")
            
            logger.info(f"Saved configuration to {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to save configuration: {str(e)}")
    
    #
    # Agent Discovery and Lookup
    #
    
    def get_agent_types(self) -> Dict[str, AgentMetadata]:
        """
        Get all registered agent types.
        
        Returns:
            Dictionary mapping agent IDs to their metadata
        """
        return self._agent_types.copy()
    
    def get_agent_type(self, agent_id: str) -> Optional[AgentMetadata]:
        """
        Get metadata for a specific agent type.
        
        Args:
            agent_id: ID of the agent type
            
        Returns:
            Agent metadata, or None if not registered
        """
        return self._agent_types.get(agent_id)
    
    def get_agents_by_capability(self, capability_type: Union[str, CapabilityType]) -> Dict[str, AgentMetadata]:
        """
        Get all agent types that provide a specific capability.
        
        Args:
            capability_type: Type of capability to look for
            
        Returns:
            Dictionary mapping agent IDs to their metadata
        """
        capability = capability_type if isinstance(capability_type, CapabilityType) else CapabilityType(capability_type)
        
        return {
            agent_id: metadata
            for agent_id, metadata in self._agent_types.items()
            if any(cap.type == capability for cap in metadata.capabilities.values())
        }
    
    def find_agents_by_ui_instruction(self, instruction_type: str) -> Dict[str, AgentMetadata]:
        """
        Find all agent types that can use a specific UI instruction.
        
        Args:
            instruction_type: Type of UI instruction
            
        Returns:
            Dictionary mapping agent IDs to their metadata
        """
        return {
            agent_id: metadata
            for agent_id, metadata in self._agent_types.items()
            for cap in metadata.capabilities.values()
            if cap.ui_instructions and instruction_type in cap.ui_instructions
        }
    
    def is_authorized_for_ui_instruction(self, agent_id: str, instruction_type: str) -> bool:
        """
        Check if an agent is authorized to use a specific UI instruction.
        
        Args:
            agent_id: ID of the agent type
            instruction_type: Type of UI instruction
            
        Returns:
            True if the agent can use this instruction, False otherwise
        """
        metadata = self.get_agent_type(agent_id)
        
        if not metadata:
            return False
        
        return any(
            cap.ui_instructions and instruction_type in cap.ui_instructions
            for cap in metadata.capabilities.values()
        )
    
    def get_agent_instances(self) -> Dict[str, Any]:
        """
        Get all instantiated agent instances.
        
        Returns:
            Dictionary mapping instance IDs to agent instances
        """
        return self._agent_instances.copy()
    
    #
    # Handoff Protocol
    #
    
    def evaluate_handoff_triggers(self, agent_id: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Evaluate handoff triggers for an agent to determine if control should be handed to another agent.
        
        Args:
            agent_id: ID of the current agent type
            context: Context data to evaluate triggers against (including message, session, etc.)
            
        Returns:
            ID of the agent to hand off to, or None if no triggers match
        """
        metadata = self.get_agent_type(agent_id)
        
        if not metadata:
            logger.warning(f"Cannot evaluate handoff triggers for unknown agent: {agent_id}")
            return None
        
        # Sort triggers by priority (highest first)
        triggers = sorted(metadata.handoff_triggers, key=lambda t: -t.priority)
        
        for trigger in triggers:
            should_handoff = False
            
            # Check condition function if specified
            if trigger.condition_function:
                # Format: module.function_name
                try:
                    module_name, function_name = trigger.condition_function.rsplit('.', 1)
                    module = importlib.import_module(module_name)
                    func = getattr(module, function_name)
                    should_handoff = func(context)
                except Exception as e:
                    logger.error(f"Failed to evaluate condition function {trigger.condition_function}: {str(e)}")
                    continue
            
            # Check keyword patterns if specified
            elif trigger.keyword_patterns and 'message' in context:
                import re
                message = context['message']
                for pattern in trigger.keyword_patterns:
                    if re.search(pattern, message, re.IGNORECASE):
                        should_handoff = True
                        break
            
            # Check intent names if specified
            elif trigger.intent_names and 'intents' in context:
                intents = context['intents']
                for intent in trigger.intent_names:
                    if intent in intents:
                        should_handoff = True
                        break
            
            if should_handoff:
                logger.info(f"Handoff trigger matched: {agent_id} -> {trigger.target_agent_id} ({trigger.description})")
                return trigger.target_agent_id
        
        return None
    
    def get_handoff_target(self, agent_id: str, trigger_id: str) -> Optional[str]:
        """
        Get the target agent for a specific handoff trigger.
        
        Args:
            agent_id: ID of the current agent type
            trigger_id: ID or description of the trigger
            
        Returns:
            ID of the target agent, or None if the trigger is not found
        """
        metadata = self.get_agent_type(agent_id)
        
        if not metadata:
            return None
        
        # Try to find the trigger by ID or description
        for trigger in metadata.handoff_triggers:
            if trigger_id == trigger.target_agent_id or trigger_id == trigger.description:
                return trigger.target_agent_id
        
        return None


# Decorator for registering agent classes
def register_agent(
    id: str,
    name: str,
    description: str,
    version: str,
    capabilities: Dict[str, AgentCapability],
    **kwargs
) -> Callable[[Type[T]], Type[T]]:
    """
    Decorator to register an agent class with the registry.
    
    Args:
        id: Unique identifier for the agent type
        name: Human-readable name of the agent
        description: Description of the agent's purpose
        version: Agent version
        capabilities: Dictionary of capability IDs to definitions
        **kwargs: Additional metadata fields
        
    Returns:
        Decorator function
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # Create metadata object
        metadata = AgentMetadata(
            id=id,
            name=name,
            description=description,
            version=version,
            capabilities=capabilities,
            **kwargs
        )
        
        # Get the registry instance
        registry = get_registry()
        
        # Register the agent type
        registry.register_agent_type(metadata, cls)
        
        # Return the class unchanged
        return cls
    
    return decorator


# Singleton instance of the registry
_registry_instance = None


def get_registry() -> AgentRegistry:
    """
    Get the singleton instance of the agent registry.
    
    Returns:
        Agent registry instance
    """
    global _registry_instance
    
    if _registry_instance is None:
        _registry_instance = AgentRegistry()
        
        # Try to load configuration from environment variable
        config_path = os.environ.get('AGNO_AGENT_CONFIG')
        if config_path:
            try:
                _registry_instance.load_config(config_path)
            except ValueError as e:
                logger.warning(f"Failed to load configuration from {config_path}: {str(e)}")
    
    return _registry_instance