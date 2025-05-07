import re
from typing import Dict, Optional, Any
import json

class FormCollectorAgent:
    def __init__(self, llm_client, schema):
        self.llm = llm_client
        self.schema = schema
        self.collected_fields = {}
        self.field_order = [
            'reporterName',
            'reporterEmail',
            'appVersion',
            'deviceOS',
            'stepsToReproduce',
            'expectedResult',
            'actualResult',
            'severity',
            'gdprConsent'
        ]

    def validate_field(self, field_name: str, value: str) -> bool:
        """Validate a field value against schema rules."""
        if not value:
            return False
            
        field_props = self.schema["properties"][field_name]
        
        if field_name == "reporterName":
            return bool(value.strip())
            
        elif field_name == "reporterEmail":
            try:
                pattern = field_props["pattern"]
                return bool(re.match(pattern, value))
            except Exception as e:
                print(f"[ERROR] Email validation error: {str(e)}")
                # Fallback to basic email validation
                basic_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                return bool(re.match(basic_pattern, value))
                
        elif field_name == "appVersion":
            pattern = field_props["pattern"]
            return bool(re.match(pattern, value))
            
        elif field_name in ["stepsToReproduce", "expectedResult", "actualResult"]:
            # Clean the input
            value = value.strip()
            
            # Count steps by different delimiters
            newline_steps = value.split('\n')
            comma_steps = value.split(',')
            # Look for numbered steps like "1. Step" or "1) Step"
            numbered_steps = re.findall(r'\d+[\.\)]?\s*\w+.*?(?=\d+[\.\)]|\Z)', value, re.DOTALL)
            
            # Use the delimiter that gives us the most valid steps
            steps = max([newline_steps, comma_steps, numbered_steps], key=lambda x: len([s for s in x if s.strip()]))
            valid_steps = [s for s in steps if s.strip()]
            
            min_lines = 3 if field_name == "stepsToReproduce" else 1
            return len(valid_steps) >= min_lines
            
        elif field_name == "severity":
            return value in field_props["enum"]
            
        elif field_name == "gdprConsent":
            consent = str(value).lower()
            return consent in ['true', 'yes', '1']
            
        return bool(value.strip())  # Default to non-empty for other fields

    def get_next_field(self) -> Optional[str]:
        """Get the next field that needs to be collected."""
        for field in self.field_order:
            if field not in self.collected_fields:
                return field
        return None

    def get_field_prompt(self, field_name: str) -> str:
        """Get the appropriate prompt for a field."""
        prompts = {
            'reporterName': "Hi! I can help you submit a bug report. What is your name?",
            'reporterEmail': "Please provide your email address.",
            'appVersion': "Please provide the exact app version in the format: 8.0.0 (1234)",
            'deviceOS': "Please provide your device model and OS version (e.g., iPad Pro 11\" M2, iPadOS 17.4)",
            'stepsToReproduce': "Please provide the steps to reproduce the bug (at least 3 steps):",
            'expectedResult': "What was the expected result?",
            'actualResult': "What was the actual result?",
            'severity': "How severe is this bug? (Critical/High/Medium/Low)",
            'gdprConsent': "Do you consent to storing diagnostic data? (yes/no)"
        }
        return prompts.get(field_name, f"Please provide {field_name}")

    def process_message(self, message: str, attachments: Optional[Dict[str, Any]] = None) -> str:
        current_field = self.get_next_field()
        if not current_field:
            return "Great! I have all the required information. Is there anything else you'd like to add?"

        # Special handling for initial greeting
        if current_field == 'reporterName' and message.lower() in ['hi', 'hello', 'hey']:
            return self.get_field_prompt('reporterName')

        # Handle field validation
        if self.validate_field(current_field, message):
            self.collected_fields[current_field] = message
            next_field = self.get_next_field()
            return self.get_field_prompt(next_field) if next_field else "Thank you! All required fields are complete."
        else:
            return f"The {current_field} provided seems incomplete or invalid. {self.get_field_prompt(current_field)}"

    def is_form_complete(self) -> bool:
        """Check if all required fields are collected and valid."""
        return all(field in self.collected_fields for field in self.schema["required"])

    def get_collected_fields(self) -> Dict[str, Any]:
        """Return the currently collected fields."""
        return self.collected_fields.copy()