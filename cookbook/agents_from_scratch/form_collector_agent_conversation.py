class ConversationState:
    def __init__(self):
        self.collected_fields = {}
        self.validation_status = {}
        self.history = []
        self.session_active = True

    def update_field(self, field_name, value, valid=True):
        self.collected_fields[field_name] = value
        self.validation_status[field_name] = valid

    def get_field(self, field_name):
        return self.collected_fields.get(field_name)

    def is_field_valid(self, field_name):
        return self.validation_status.get(field_name, False)

    def all_fields_valid(self, required_fields):
        return all(self.validation_status.get(field, False) for field in required_fields)

    def add_to_history(self, message):
        self.history.append(message)

    def get_history(self):
        return self.history

    def end_session(self):
        self.session_active = False

    def is_session_active(self):
        return self.session_active

# This class manages the conversation state, tracks collected fields and their validation status,
# maintains conversation history, and handles session lifecycle.
