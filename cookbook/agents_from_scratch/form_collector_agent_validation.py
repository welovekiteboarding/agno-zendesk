import jsonschema
from jsonschema import validate, ValidationError

class SchemaValidator:
    def __init__(self, schema):
        self.schema = schema

    def validate_field(self, field_name, value):
        # Validate a single field against its schema definition
        field_schema = self.schema.get('properties', {}).get(field_name)
        if not field_schema:
            return True, None  # No schema for this field, consider valid

        try:
            validate(instance=value, schema=field_schema)
            return True, None
        except ValidationError as e:
            return False, str(e)

    def validate_all(self, data):
        # Validate entire data object against the schema
        try:
            validate(instance=data, schema=self.schema)
            return True, None
        except ValidationError as e:
            return False, str(e)

# This class provides validation methods to check user inputs against the guardrails schema,
# both for individual fields and the entire collected data.
