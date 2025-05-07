from cookbook.agents_from_scratch.form_collector_agent_prompts import PromptTemplates

class ConversationFlow:
    def __init__(self, state, llm_agent, input_processor):
        self.state = state
        self.llm_agent = llm_agent
        self.input_processor = input_processor

    def next_prompt(self, schema):
        required_fields = schema.get("required", [])
        for field in required_fields:
            if not self.state.is_field_valid(field):
                if self.state.get_field(field) is None:
                    return PromptTemplates.ask_for_field(field)
                else:
                    return PromptTemplates.follow_up_prompt(field)
        return PromptTemplates.completion_message()

    def handle_user_response(self, field_name, user_input):
        valid, cleaned_input, error = self.input_processor.process_input(field_name, user_input)
        if valid:
            self.state.update_field(field_name, cleaned_input, valid=True)
            return None, None
        else:
            return None, error

# This class manages the conversation flow by determining the next prompt to send to the user,
# handling user responses, validating inputs, and updating the conversation state accordingly.
