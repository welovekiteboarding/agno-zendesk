from form_collector_agent import FormCollectorAgent
from form_collector_agent_validation import SchemaValidator
from form_collector_agent_conversation import ConversationState
from form_collector_agent_followup import FollowUpHandler

class FormCollectorAgentWithValidation(FormCollectorAgent):
    def __init__(self, llm_client, schema):
        super().__init__(llm_client, schema)
        self.validator = SchemaValidator(schema)
        self.state = ConversationState()
        self.followup = FollowUpHandler(self.state)

    def process_message(self, user_input):
        # Determine which field to validate next
        required_fields = self.schema.get('required', [])
        for field in required_fields:
            if not self.state.is_field_valid(field):
                # Validate user input for this field
                is_valid, error = self.validator.validate_field(field, user_input)
                if is_valid:
                    self.state.update_field(field, user_input, valid=True)
                    # Check if form is complete
                    if self.state.all_fields_valid(required_fields):
                        return "Thank you! Your bug report is complete."
                    else:
                        # Prompt for next missing field
                        next_field = next(f for f in required_fields if not self.state.is_field_valid(f))
                        if self.followup.needs_follow_up(next_field):
                            return self.followup.generate_follow_up(next_field)
                        if next_field == "appVersion":
                            return "Got it. Now, please provide the exact appVersion in the following format: 8.0.0 (1234)"
                        if next_field == "stepsToReproduce":
                            return (
                                "Got it. Now, please provide the steps to reproduce as a multi-line input, "
                                "with at least 3 lines. Please use the following format:\n"
                                "Step 1: Do X \n"
                                "Step 2: Then do Y \n"
                                "Step 3: Result is Z"
                            )
                        return f"Got it. Now, please provide the {next_field.replace('_', ' ')}."
                else:
                    return f"Invalid input for {field}: {error}. Please try again."
        return "All fields are already collected and valid."
