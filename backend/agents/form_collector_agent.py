"""
Form Collector Agent: Specialized agent for collecting structured form data

This agent is responsible for collecting form data based on a JSON schema,
guiding the user through the form fields, and validating their input.
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List, Set, Union
from pathlib import Path

from ..agent_registry import register_agent, AgentCapability, CapabilityType, HandoffTrigger
from .base_agent import BaseAgent

# Set up logging
logger = logging.getLogger(__name__)

@register_agent(
    id="form_collector",
    name="Form Collection Agent",
    description="Collects form information for bug reports",
    version="1.0.0",
    capabilities={
        "form_collection": AgentCapability(
            type=CapabilityType.FORM_COLLECTION,
            description="Collects structured form data based on a JSON schema",
            ui_instructions=["show_file_upload", "request_email", "display_form"]
        ),
        "data_extraction": AgentCapability(
            type=CapabilityType.DATA_EXTRACTION,
            description="Extracts structured data from user messages",
        )
    },
    handoff_triggers=[
        HandoffTrigger(
            target_agent_id="email_verifier",
            description="Form collection complete, needs email verification",
            priority=2,
            condition_function="backend.agents.form_collector_agent.is_form_complete"
        )
    ],
    priority=2,
    input_format={
        "message": "string",
        "session_data": "object"
    },
    output_format={
        "message": "string",
        "ui_instruction": "optional string",
        "data": "optional object",
        "handoff_to": "optional string"
    },
    singleton=False,
    rate_limits={
        "ui_instructions_per_minute": 5
    }
)
class FormCollectorAgent(BaseAgent):
    """
    Agent that collects structured form data based on a JSON schema.
    
    This agent guides the user through a form completion process, validates their
    input against a schema, and asks follow-up questions until all required fields
    are completed.
    """
    
    def initialize(self, schema_path: Optional[str] = None, max_retries: int = 3, **kwargs):
        """
        Initialize the agent with a JSON schema.
        
        Args:
            schema_path: Path to the JSON schema file
            max_retries: Maximum number of retries for invalid inputs
            **kwargs: Additional configuration parameters
        """
        self.max_retries = max_retries
        self.collected_data = {}
        self.current_field = None
        self.retry_count = {}
        self.schema = {}
        self.required_fields = []
        self.completed_fields = set()
        
        # Load schema if provided
        if schema_path:
            try:
                with open(schema_path, 'r') as f:
                    self.schema = json.load(f)
                    
                # Extract required fields
                self.required_fields = self.schema.get('required', [])
                
                logger.info(f"Loaded schema with {len(self.required_fields)} required fields")
                
            except Exception as e:
                logger.error(f"Failed to load schema from {schema_path}: {str(e)}")
    
    def process_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a user message and continue the form collection flow.
        
        Args:
            message: User message text
            context: Additional context information
            
        Returns:
            Response dictionary with next prompt or handoff information
        """
        # Update activity timestamp
        self.update_last_activity()
        
        # If we're coming from a handoff, initialize with session data
        if 'handoff_context' in context:
            handoff_data = context['handoff_context']
            collected_data = handoff_data.get('collected_data', {})
            if collected_data:
                self.collected_data = collected_data
                self.completed_fields = set(collected_data.keys())
                logger.info(f"Initialized from handoff with {len(self.completed_fields)} fields")
        
        # Process the current message
        result = {
            "message": "",
            "data": self.collected_data
        }
        
        # If we have a current field, try to extract and validate it
        if self.current_field:
            field_name = self.current_field
            
            # Mock implementation of field extraction and validation
            # In a real implementation, this would use an LLM or other techniques
            valid, value, error = self._extract_and_validate_field(field_name, message)
            
            if valid:
                # Store the value
                self.collected_data[field_name] = value
                self.completed_fields.add(field_name)
                self.current_field = None
                
                result["message"] = f"Great! I've recorded your {field_name}. "
                
                # If this is the email field, add UI instruction
                if field_name == "email":
                    result["ui_instruction"] = "request_email"
                    result["ui_instruction_params"] = {
                        "prompt": "Please confirm your email address:",
                        "validation_regex": "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"
                    }
            else:
                # Increment retry count
                self.retry_count[field_name] = self.retry_count.get(field_name, 0) + 1
                
                # Check if we've exceeded max retries
                if self.retry_count[field_name] > self.max_retries:
                    # Skip this field and move on
                    self.current_field = None
                    result["message"] = f"Let's move on and come back to {field_name} later. "
                else:
                    # Ask again with error message
                    result["message"] = f"I'm having trouble understanding your {field_name}. {error} Please try again."
                    return result
        
        # Check if we have any remaining required fields
        remaining_fields = [f for f in self.required_fields if f not in self.completed_fields]
        
        if not remaining_fields:
            # All required fields completed, check if we should hand off
            completion_percentage = 100
            result["message"] += f"Thank you! I've collected all the required information. "
            
            # Add handoff to email verifier if we have an email
            if "email" in self.collected_data:
                result["handoff_to"] = "email_verifier"
                result["handoff_reason"] = "Form collection complete, needs email verification"
            else:
                # Ask for email as the last step
                self.current_field = "email"
                result["message"] += "Finally, I need your email address for this bug report."
                
                # Add UI instruction for email
                result["ui_instruction"] = "request_email"
                result["ui_instruction_params"] = {
                    "prompt": "Please enter your email address:",
                    "validation_regex": "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"
                }
        else:
            # Pick the next field to collect
            if not self.current_field:
                self.current_field = remaining_fields[0]
            
            # Calculate completion percentage
            completion_percentage = int((len(self.completed_fields) / len(self.required_fields)) * 100)
            
            # Ask for the current field
            result["message"] += self._generate_field_prompt(self.current_field)
            
            # If asking for attachment, add UI instruction
            if self.current_field == "attachments":
                result["ui_instruction"] = "show_file_upload"
                result["ui_instruction_params"] = {
                    "max_files": 3,
                    "max_size_mb": 10,
                    "accepted_types": ["image/png", "image/jpeg", "application/pdf"],
                    "upload_url": "/api/upload"
                }
        
        # Add progress information
        result["progress"] = {
            "percentage": completion_percentage,
            "completed_fields": len(self.completed_fields),
            "total_fields": len(self.required_fields)
        }
        
        return result
    
    def _extract_and_validate_field(self, field_name: str, message: str) -> tuple[bool, Any, Optional[str]]:
        """
        Extract and validate a field value from a message.
        
        Args:
            field_name: Name of the field to extract
            message: User message text
            
        Returns:
            Tuple of (is_valid, value, error_message)
        """
        # This is a simplified mock implementation
        # In a real agent, this would use the JSON schema for validation
        
        if field_name == "email":
            # Simple email validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            match = re.search(email_pattern, message)
            
            if match:
                return True, match.group(0), None
            else:
                return False, None, "I couldn't find a valid email address."
        
        elif field_name == "description":
            # Check minimum length
            if len(message.strip()) < 20:
                return False, None, "Please provide a more detailed description (at least 20 characters)."
            else:
                return True, message.strip(), None
        
        elif field_name == "steps_to_reproduce":
            # Check for numbered steps
            lines = [line.strip() for line in message.split('\n') if line.strip()]
            if len(lines) < 3:
                return False, None, "Please provide at least 3 steps to reproduce the issue."
            else:
                return True, message.strip(), None
        
        elif field_name == "attachments":
            # For attachments, we'd normally extract file IDs from a UI upload
            # Here we just check if the message mentions attachments
            if "attached" in message.lower() or "upload" in message.lower():
                return True, ["mock_attachment_id"], None
            else:
                return False, None, "Please upload one or more files using the upload button."
        
        # Default case - accept any non-empty input
        if message.strip():
            return True, message.strip(), None
        else:
            return False, None, "Please provide a non-empty value."
    
    def _generate_field_prompt(self, field_name: str) -> str:
        """
        Generate a prompt to ask for a specific field.
        
        Args:
            field_name: Name of the field to ask for
            
        Returns:
            Prompt text
        """
        prompts = {
            "title": "What's the title of your bug report?",
            "description": "Please describe the bug in detail.",
            "steps_to_reproduce": "What are the steps to reproduce this issue? Please provide at least 3 numbered steps.",
            "expected_result": "What did you expect to happen?",
            "actual_result": "What actually happened?",
            "attachments": "Please upload any screenshots or files that help demonstrate the issue.",
            "email": "What email address should we use to contact you about this bug?",
            "severity": "How severe is this issue? (Low, Medium, High, Critical)"
        }
        
        # Get the field properties from the schema
        field_props = {}
        if self.schema and "properties" in self.schema:
            field_props = self.schema.get("properties", {}).get(field_name, {})
        
        # Use custom prompt from schema if available
        if "prompt" in field_props:
            return field_props["prompt"]
        
        # Otherwise use default prompt
        return prompts.get(field_name, f"Please provide your {field_name}:")


# Helper function used by handoff trigger
def is_form_complete(context: Dict[str, Any]) -> bool:
    """
    Check if form collection is complete and ready for email verification.
    
    Args:
        context: Context information including session data
        
    Returns:
        True if the form is complete and has an email for verification
    """
    # Get the session data
    session_data = context.get("session_data", {})
    
    # Check if the data contains an email
    if "email" not in session_data:
        return False
    
    # For this example, we consider the form complete if it has at least 3 fields
    return len(session_data) >= 3