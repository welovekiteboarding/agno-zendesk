from form_collector_agent_validation_integration import FormCollectorAgentWithValidation
from form_collector_agent_llm import FormCollectorAgentLLM
from form_collector_agent_conversation import ConversationState
from form_collector_agent_json_output import JsonOutputHandler

class FormCollectorAgentApp:
    def __init__(self, llm_client, schema):
        self.agent = FormCollectorAgentWithValidation(llm_client, schema)
        self.llm = FormCollectorAgentLLM(llm_client)
        self.state = self.agent.state
        self.json_output = JsonOutputHandler(self.state)

    def start(self):
        welcome_message = self.agent.start_conversation()
        self.state.add_to_history(welcome_message)
        return welcome_message

    def handle_user_input(self, user_input):
        self.state.add_to_history({"user": user_input})

        response = self.agent.process_message(user_input)

        self.state.add_to_history({"agent": response})

        # If the bug report is complete, show the JSON output
        if response == "Thank you! Your bug report is complete.":
            output = self.json_output.generate_output()
            return response + "\n\nCollected Bug Report JSON:\n" + output

        return response

    def is_complete(self):
        required_fields = self.agent.schema.get("required", [])
        return self.state.all_fields_valid(required_fields)

# This main application class integrates the agent framework with validation,
# LLM interaction, conversation state management, and JSON output generation.
