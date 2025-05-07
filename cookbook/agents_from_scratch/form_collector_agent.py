from cookbook.agents_from_scratch.form_collector_agent_conversation import ConversationState
from cookbook.agents_from_scratch.form_collector_agent_validation import SchemaValidator
from cookbook.agents_from_scratch.form_collector_agent_prompts import PromptTemplates
from cookbook.agents_from_scratch.form_collector_agent_json_output import JsonOutputHandler
from cookbook.agents_from_scratch.form_collector_agent_llm import FormCollectorAgentLLM

class FormCollectorAgent:
    def __init__(self, llm_client, schema):
        self.llm_client = llm_client
        self.schema = schema
        self.state = ConversationState()
        self.validator = SchemaValidator(schema)
        self.session_active = False
        self.json_output = JsonOutputHandler(self.state)
        self.llm_agent = FormCollectorAgentLLM(llm_client)

    def start_conversation(self):
        self.state = ConversationState()
        self.session_active = True
        welcome = PromptTemplates.initial_prompt()
        self.state.add_to_history(welcome)
        return welcome

    def process_message(self, user_input, attachments=None):
        required_fields = self.schema.get('required', [])
        next_field = None
        for field in required_fields:
            if not self.state.is_field_valid(field):
                next_field = field
                break
        # Handle attachments if provided
        if attachments is not None:
            self.state.update_field('attachments', attachments, valid=True)
        if next_field is None:
            return (
                PromptTemplates.completion_message()
                + "\n\nCollected Bug Report JSON:\n"
                + self.json_output.generate_output()
            )
        try:
            is_valid, error = self.validator.validate_field(next_field, user_input)
        except Exception as e:
            return f"An error occurred during validation: {str(e)}. Please try again or contact support."
        if is_valid:
            self.state.update_field(next_field, user_input, valid=True)
            if self.state.all_fields_valid(required_fields):
                return (
                    PromptTemplates.completion_message()
                    + "\n\nCollected Bug Report JSON:\n"
                    + self.json_output.generate_output()
                )
            else:
                next_missing = next(f for f in required_fields if not self.state.is_field_valid(f))
                # Use LLM to generate a dynamic prompt for the next field
                try:
                    prompt = self.llm_agent.send_message(PromptTemplates.ask_for_field(next_missing))
                except Exception as e:
                    prompt = PromptTemplates.ask_for_field(next_missing) + f"\n(Note: LLM unavailable: {str(e)})"
                return prompt
        else:
            self.state.update_field(next_field, user_input, valid=False)
            # Use LLM to clarify the follow-up prompt
            try:
                followup = self.llm_agent.send_message(PromptTemplates.follow_up_prompt(next_field))
            except Exception as e:
                followup = PromptTemplates.follow_up_prompt(next_field) + f"\n(Note: LLM unavailable: {str(e)})"
            return followup

    def get_collected_fields(self):
        return self.state.collected_fields

    def is_form_complete(self):
        required_fields = self.schema.get('required', [])
        return self.state.all_fields_valid(required_fields)

    def get_history(self):
        return self.state.get_history()
