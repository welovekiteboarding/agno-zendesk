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
            'hasAttachments',  # NEW: yes/no step
            'attachments',     # NEW: only if hasAttachments is yes
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
            'reporterName': "I'm the bug reporting assistant. To get started with your report, what is your name?",
            'reporterEmail': "Thanks! Please provide your email address so we can follow up if needed.",
            'appVersion': "Now I need the exact app version in the format: 8.0.0 (1234). You can find this in the app by going to Help > scroll to the bottom.",
            'deviceOS': "What device and OS are you using? (e.g., iPad Pro 11\" M2, iPadOS 17.4)",
            'stepsToReproduce': "Please provide the steps to reproduce the bug (at least 3 steps):",
            'expectedResult': "What was the expected result when you performed these steps?",
            'actualResult': "What was the actual result that occurred instead?",
            'severity': "How would you rate the severity of this bug? (Critical/High/Medium/Low)",
            'hasAttachments': "Would you like to upload any screenshots or files to help explain the issue? (yes/no)",
            'attachments': "Please upload your attachments now.",
            'gdprConsent': "Last question: Do you consent to storing diagnostic data for troubleshooting? (yes/no)"
        }
        return prompts.get(field_name, f"Please provide {field_name}")

    def process_message(self, message: str, attachments: Optional[Dict[str, Any]] = None) -> str:
        current_field = self.get_next_field()
        if not current_field:
            return "Great! I have all the required information. Is there anything else you'd like to add?"

        # Special handling for initial greeting
        if current_field == 'reporterName' and message.lower() in ['hi', 'hello', 'hey', 'bug', 'report a bug']:
            return "Welcome to the bug reporting system. I'll guide you through submitting a detailed bug report. " + self.get_field_prompt('reporterName')

        # Special handling for hasAttachments
        if current_field == 'hasAttachments':
            if message.strip().lower() in ['yes', 'y']:
                self.collected_fields['hasAttachments'] = 'yes'
                return self.get_field_prompt('attachments')
            else:
                self.collected_fields['hasAttachments'] = 'no'
                # Skip attachments, go to next field
                next_field = self.get_next_field()
                return self.get_field_prompt(next_field) if next_field else "Thank you! All required fields are complete."

        # Special handling for attachments
        if current_field == 'attachments':
            if attachments and attachments.get('attachments'):
                self.collected_fields['attachments'] = attachments['attachments']
                next_field = self.get_next_field()
                return self.get_field_prompt(next_field) if next_field else "Thank you! All required fields are complete."
            else:
                return self.get_field_prompt('attachments')

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