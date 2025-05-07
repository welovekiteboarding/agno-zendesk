class FollowUpHandler:
    def __init__(self, state):
        self.state = state

    def needs_follow_up(self, field_name):
        # Determine if a field needs a follow-up question
        return not self.state.is_field_valid(field_name)

    def generate_follow_up(self, field_name):
        # Generate a follow-up question for a specific field
        return f"Could you please clarify or provide a valid {field_name.replace('_', ' ')}?"

# This class handles generating follow-up questions for incomplete or invalid fields,
# ensuring the user provides all necessary information for the bug report.
