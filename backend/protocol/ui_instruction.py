"""
UI Instruction Protocol: Backend implementation for sending UI instructions to the frontend

This module provides a Python implementation of the UI Instruction Protocol,
which allows backend systems to send structured UI instructions to the frontend.
"""

import json
import re
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Literal

from pydantic import BaseModel, Field, validator

# UI Instruction Types
class UIInstructionType(str, Enum):
    """Enumeration of supported UI instruction types"""
    SHOW_FILE_UPLOAD = "show_file_upload"
    REQUEST_EMAIL = "request_email"
    DISPLAY_FORM = "display_form"
    SHOW_AUTH_PROMPT = "show_auth_prompt"
    SHOW_SELECTION_MENU = "show_selection_menu"
    SHOW_PROGRESS_INDICATOR = "show_progress_indicator"
    SHOW_CONFIRMATION_DIALOG = "show_confirmation_dialog"


# UI Instruction Metadata
class UIInstructionMetadata(BaseModel):
    """Metadata for a UI instruction"""
    priority: Literal["low", "normal", "high"] = "normal"
    sequence: Optional[int] = None
    version: str
    agent_id: Optional[str] = None


# UI Instruction Model
class UIInstruction(BaseModel):
    """
    UI Instruction sent from backend to frontend
    
    This model defines the structure of UI instructions that can be sent
    from backend systems to the frontend to request specific UI elements
    or interactions.
    """
    instruction_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    metadata: UIInstructionMetadata

    @validator('instruction_type')
    def validate_instruction_type(cls, v):
        """Validate the instruction type"""
        valid_types = [t.value for t in UIInstructionType]
        if v not in valid_types:
            raise ValueError(f"Invalid instruction_type: {v}. Must be one of: {', '.join(valid_types)}")
        return v

    @validator('parameters')
    def validate_parameters(cls, v, values):
        """Validate parameters based on instruction type"""
        instruction_type = values.get('instruction_type')
        if not instruction_type:
            return v

        # Validate parameters for different instruction types
        if instruction_type == UIInstructionType.SHOW_FILE_UPLOAD.value:
            # Validate file upload parameters
            if 'max_files' not in v:
                raise ValueError("Missing required parameter: max_files")
            if 'max_size_mb' not in v:
                raise ValueError("Missing required parameter: max_size_mb")
            if 'accepted_types' not in v:
                raise ValueError("Missing required parameter: accepted_types")
            if 'upload_url' not in v:
                raise ValueError("Missing required parameter: upload_url")

        elif instruction_type == UIInstructionType.REQUEST_EMAIL.value:
            # Validate email request parameters
            if 'prompt' not in v:
                raise ValueError("Missing required parameter: prompt")

        # Add validation for other instruction types as needed
            
        return v


# Validation Functions
def validate_ui_instruction(instruction: Dict[str, Any]) -> None:
    """
    Validate a UI instruction against the schema.
    
    Args:
        instruction: UI instruction to validate
        
    Raises:
        ValueError: If the instruction is invalid
    """
    # Convert to Pydantic model for validation
    UIInstruction.parse_obj(instruction)


def serialize_ui_instruction(instruction: Union[UIInstruction, Dict[str, Any]], pretty: bool = False) -> str:
    """
    Serialize a UI instruction to JSON.
    
    Args:
        instruction: UI instruction to serialize
        pretty: Whether to format the JSON with indentation
        
    Returns:
        JSON string
    """
    # Convert to Pydantic model if it's a dict
    if isinstance(instruction, dict):
        instruction = UIInstruction.parse_obj(instruction)
    
    # Validate and serialize
    return instruction.json(indent=2 if pretty else None)


def deserialize_ui_instruction(json_str: str) -> UIInstruction:
    """
    Deserialize a JSON string to a UI instruction.
    
    Args:
        json_str: JSON string to deserialize
        
    Returns:
        UI instruction
        
    Raises:
        ValueError: If the JSON is invalid
    """
    try:
        data = json.loads(json_str)
        return UIInstruction.parse_obj(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {str(e)}")


def create_file_upload_instruction(
    max_files: int,
    max_size_mb: int,
    accepted_types: List[str],
    upload_url: str,
    agent_id: Optional[str] = None,
    priority: str = "normal"
) -> UIInstruction:
    """
    Create a file upload instruction.
    
    Args:
        max_files: Maximum number of files
        max_size_mb: Maximum file size in MB
        accepted_types: List of accepted MIME types
        upload_url: URL to upload files to
        agent_id: Optional ID of the agent creating this instruction
        priority: Priority of this instruction
        
    Returns:
        UI instruction
    """
    return UIInstruction(
        instruction_type=UIInstructionType.SHOW_FILE_UPLOAD.value,
        parameters={
            "max_files": max_files,
            "max_size_mb": max_size_mb,
            "accepted_types": accepted_types,
            "upload_url": upload_url
        },
        metadata=UIInstructionMetadata(
            priority=priority,
            version="1.0.0",
            agent_id=agent_id
        )
    )


def create_email_request_instruction(
    prompt: str,
    validation_regex: Optional[str] = None,
    agent_id: Optional[str] = None,
    priority: str = "normal"
) -> UIInstruction:
    """
    Create an email request instruction.
    
    Args:
        prompt: Prompt text to display
        validation_regex: Optional regex for email validation
        agent_id: Optional ID of the agent creating this instruction
        priority: Priority of this instruction
        
    Returns:
        UI instruction
    """
    params = {
        "prompt": prompt
    }
    
    if validation_regex:
        params["validation_regex"] = validation_regex
    
    return UIInstruction(
        instruction_type=UIInstructionType.REQUEST_EMAIL.value,
        parameters=params,
        metadata=UIInstructionMetadata(
            priority=priority,
            version="1.0.0",
            agent_id=agent_id
        )
    )


def create_form_display_instruction(
    title: str,
    fields: List[Dict[str, Any]],
    submit_label: str = "Submit",
    agent_id: Optional[str] = None,
    priority: str = "normal"
) -> UIInstruction:
    """
    Create a form display instruction.
    
    Args:
        title: Form title
        fields: List of field definitions
        submit_label: Label for the submit button
        agent_id: Optional ID of the agent creating this instruction
        priority: Priority of this instruction
        
    Returns:
        UI instruction
    """
    return UIInstruction(
        instruction_type=UIInstructionType.DISPLAY_FORM.value,
        parameters={
            "title": title,
            "fields": fields,
            "submit_label": submit_label
        },
        metadata=UIInstructionMetadata(
            priority=priority,
            version="1.0.0",
            agent_id=agent_id
        )
    )


def create_confirmation_dialog_instruction(
    title: str,
    message: str,
    confirm_label: str = "Confirm",
    cancel_label: str = "Cancel",
    agent_id: Optional[str] = None,
    priority: str = "high"
) -> UIInstruction:
    """
    Create a confirmation dialog instruction.
    
    Args:
        title: Dialog title
        message: Dialog message
        confirm_label: Label for the confirm button
        cancel_label: Label for the cancel button
        agent_id: Optional ID of the agent creating this instruction
        priority: Priority of this instruction
        
    Returns:
        UI instruction
    """
    return UIInstruction(
        instruction_type=UIInstructionType.SHOW_CONFIRMATION_DIALOG.value,
        parameters={
            "title": title,
            "message": message,
            "confirm_label": confirm_label,
            "cancel_label": cancel_label
        },
        metadata=UIInstructionMetadata(
            priority=priority,
            version="1.0.0",
            agent_id=agent_id
        )
    )


def create_progress_indicator_instruction(
    message: str,
    progress: Optional[int] = None,
    indeterminate: bool = True,
    agent_id: Optional[str] = None,
    priority: str = "normal"
) -> UIInstruction:
    """
    Create a progress indicator instruction.
    
    Args:
        message: Message to display
        progress: Optional progress percentage (0-100)
        indeterminate: Whether the progress is indeterminate
        agent_id: Optional ID of the agent creating this instruction
        priority: Priority of this instruction
        
    Returns:
        UI instruction
    """
    params = {
        "message": message,
        "indeterminate": indeterminate
    }
    
    if progress is not None:
        params["progress"] = progress
        params["indeterminate"] = False
    
    return UIInstruction(
        instruction_type=UIInstructionType.SHOW_PROGRESS_INDICATOR.value,
        parameters=params,
        metadata=UIInstructionMetadata(
            priority=priority,
            version="1.0.0",
            agent_id=agent_id
        )
    )