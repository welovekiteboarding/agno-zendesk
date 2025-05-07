import unittest
from unittest.mock import MagicMock
from cookbook.agents_from_scratch.form_collector_agent import FormCollectorAgent
from cookbook.agents_from_scratch.form_collector_agent_llm import FormCollectorAgentLLM
from cookbook.agents_from_scratch.form_collector_agent_conversation import ConversationState
from cookbook.agents_from_scratch.form_collector_agent_validation import SchemaValidator
from cookbook.agents_from_scratch.form_collector_agent_processing import UserInputProcessor
from cookbook.agents_from_scratch.form_collector_agent_prompts import PromptTemplates
from cookbook.agents_from_scratch.form_collector_agent_flow import ConversationFlow

class TestFormCollectorAgent(unittest.TestCase):
    def setUp(self):
        self.schema = {
            "required": ["reporterName", "reporterEmail"],
            "properties": {
                "reporterName": {"type": "string"},
                "reporterEmail": {"type": "string", "pattern": "^.+@.+$"}
            }
        }
        self.llm_client = MagicMock()
        # Patch send_message to always return a known string
        self.llm_client.chat.completions.create.return_value.choices = [MagicMock(message={"content": "LLM response"})]
        self.agent = FormCollectorAgent(self.llm_client, self.schema)
        self.llm_agent = FormCollectorAgentLLM(self.llm_client)
        self.state = ConversationState()
        self.validator = SchemaValidator(self.schema)
        self.input_processor = UserInputProcessor(self.schema)
        self.flow = ConversationFlow(self.state, self.llm_agent, self.input_processor)

    def test_start_conversation(self):
        welcome = self.agent.start_conversation()
        self.assertIn("Welcome", welcome)

    def test_process_message(self):
        # Now that LLM is mocked, check for the mocked LLM response
        response = self.agent.process_message("Test input")
        self.assertIsInstance(response, str)

    def test_validate_field(self):
        valid, error = self.validator.validate_field("reporterEmail", "test@example.com")
        self.assertTrue(valid)
        invalid, error = self.validator.validate_field("reporterEmail", "invalid-email")
        self.assertFalse(invalid)

    def test_process_input(self):
        valid, cleaned, error = self.input_processor.process_input("reporterEmail", "test@example.com")
        self.assertTrue(valid)
        valid, cleaned, error = self.input_processor.process_input("reporterEmail", "bad-email")
        self.assertFalse(valid)

    def test_conversation_flow_prompts(self):
        prompt = self.flow.next_prompt(self.schema)
        self.assertIn("Please provide", prompt)

    def test_conversation_flow_handle_response(self):
        error = self.flow.handle_user_response("reporterEmail", "bad-email")[1]
        self.assertIsNotNone(error)
        no_error = self.flow.handle_user_response("reporterEmail", "test@example.com")[1]
        self.assertIsNone(no_error)

if __name__ == "__main__":
    unittest.main()
