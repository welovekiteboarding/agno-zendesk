import json
from form_collector_agent_main import FormCollectorAgentApp
import json
import os

def load_schema():
    schema_path = os.path.join(os.path.dirname(__file__), '../../schemas/bug_report.schema.json')
    with open(schema_path, 'r') as f:
        return json.load(f)

schema = load_schema()
from unittest.mock import MagicMock

def main():
    # Mock LLM client for demonstration
    llm_client = MagicMock()

    # Initialize the agent application
    agent_app = FormCollectorAgentApp(llm_client, schema)

    print(agent_app.start())

    while not agent_app.is_complete():
        print("Enter your input. Finish with an empty line:")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        user_input = "\\n".join(lines)
        response = agent_app.handle_user_input(user_input)
        print(response)

    print("Bug report collection complete.")
    print("Collected data:")
    print(json.dumps(agent_app.state.collected_fields, indent=2))

if __name__ == "__main__":
    main()
