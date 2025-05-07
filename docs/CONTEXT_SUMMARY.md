# Context Summary

## Task 1: Create Guardrails Schema for Form Collection

- Created foundational JSON schema structure with required bug report fields and types.
- Added regex pattern validations for email and app version fields.
- Implemented minimum line count validations for descriptive fields.
- Defined enumeration constraints for severity/impact field.
- Added support for optional attachments and GDPR consent.
- Verified schema with Ajv JSON schema validator tests covering valid and invalid payloads.

This comprehensive work ensures robust validation and data integrity for bug report submissions in the system.
The code changes can be summarized as follows:

1. **Added `__init__.py` file**: This file marks the `agents_from_scratch` directory as a Python package.

2. **Added compiled Python files**: Several compiled Python files (`.pyc` files) have been added to the `__pycache__` directory, indicating that the code has been compiled and cached for faster execution.

3. **Added new Python files**: The following new Python files have been added:
   - `form_collector_agent.py`: Defines the `FormCollectorAgent` class, which is the main agent class responsible for collecting and processing user input.
   - `form_collector_
