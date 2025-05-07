class PromptTemplates:
    @staticmethod
    def initial_prompt():
        return (
            "Welcome to the bug report collector. "
            "I will guide you through providing all the necessary information to submit a bug report."
        )

    @staticmethod
    def ask_for_field(field_name):
        if field_name == "appVersion":
            return (
                "Now, please provide the exact appVersion in the following format: 8.0.0 (1234)"
            )
        if field_name == "stepsToReproduce":
            return (
                "Please provide the steps to reproduce the bug as a multi-line input, "
                "with at least 3 lines. Please use the following format:\n"
                "Step 1: Do X \n"
                "Step 2: Then do Y \n"
                "Step 3: Result is Z"
            )
        return f"Please provide the {field_name.replace('_', ' ')}."

    @staticmethod
    def follow_up_prompt(field_name):
        return f"The {field_name.replace('_', ' ')} you provided seems incomplete or invalid. Could you please clarify or provide it again?"

    @staticmethod
    def completion_message():
        return "Thank you for providing all the required information. Your bug report is complete."

# This module provides prompt templates for guiding users through the bug report collection process,
# including initial greetings, field requests, follow-up clarifications, and completion acknowledgments.
