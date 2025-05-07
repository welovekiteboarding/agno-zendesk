from cookbook.agents_from_scratch.form_collector_agent_validation import SchemaValidator

class UserInputProcessor:
    def __init__(self, schema):
        self.validator = SchemaValidator(schema)

    def process_input(self, field_name, user_input):
        # Validate user input for a specific field
        is_valid, error = self.validator.validate_field(field_name, user_input)
        if is_valid:
            return True, user_input, None
        else:
            return False, None, error

# This class handles processing and validation of user inputs for individual fields,
# returning validation status, cleaned input, and error messages if any.
