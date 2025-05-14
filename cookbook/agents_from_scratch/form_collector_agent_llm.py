class FormCollectorAgentLLM:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        import logging
        import inspect
        import datetime
        import json
        import os
        
        # Setup logging
        self.logging = logging
        self.inspect = inspect
        self.datetime = datetime
        self.json = json
        
        # Create logger specifically for LLM calls
        self.logger = logging.getLogger('form_collector_llm')
        self.logger.setLevel(logging.INFO)
        
        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        
        # Add handler to logger if not already added
        if not self.logger.handlers:
            self.logger.addHandler(ch)
        
        # Log initialization
        self.logger.info("FormCollectorAgentLLM initialized")
        
        # Create a log directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        # Also create a file handler for persistent logs
        fh = logging.FileHandler('logs/form_collector_llm.log')
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        if len(self.logger.handlers) < 2:
            self.logger.addHandler(fh)

    def format_message(self, prompt):
        # Format the prompt for the LLM API
        return {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }

    def send_message(self, prompt):
        # Get the caller information
        caller_frame = self.inspect.currentframe().f_back
        caller_info = self.inspect.getframeinfo(caller_frame)
        caller_function = caller_info.function
        caller_filename = caller_info.filename
        caller_lineno = caller_info.lineno
        
        # Format timestamp
        timestamp = self.datetime.datetime.now().isoformat()
        
        # Log the API call details before sending
        self.logger.info(f"LLM API Call - Timestamp: {timestamp}")
        self.logger.info(f"Called from: {caller_filename}:{caller_lineno} in {caller_function}()")
        
        # Truncate prompt for logging if too long
        log_prompt = prompt[:500] + "..." if len(prompt) > 500 else prompt
        self.logger.info(f"Prompt: {log_prompt}")
        
        # Format and send the message
        message = self.format_message(prompt)
        
        # Log additional details
        self.logger.info(f"Model: {message.get('model')}, Temperature: {message.get('temperature')}")
        
        try:
            # Measure response time
            start_time = self.datetime.datetime.now()
            response = self.llm_client.chat.completions.create(**message)
            end_time = self.datetime.datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Get response content
            content = response.choices[0].message["content"]
            
            # Log success
            self.logger.info(f"Response received in {duration:.2f} seconds")
            
            # Log truncated response content
            log_content = content[:500] + "..." if len(content) > 500 else content
            self.logger.info(f"Response content: {log_content}")
            
            # Log token usage if available
            if hasattr(response, 'usage'):
                self.logger.info(f"Token usage: {self.json.dumps(response.usage)}")
            
            return content
        except Exception as e:
            # Log error
            self.logger.error(f"API call failed: {str(e)}")
            raise

    def generate_prompt(self, collected_fields, missing_fields):
        # Generate a prompt to ask user for missing fields
        prompt = "Please provide the following information:\n"
        for field in missing_fields:
            prompt += f"- {field}\n"
        return prompt

    def collect_fields(self, collected_fields, schema):
        # Determine missing fields based on schema and collected fields
        required_fields = schema.get("required", [])
        missing_fields = [f for f in required_fields if f not in collected_fields]
        return missing_fields

    def process_user_input(self, user_input, collected_fields, schema):
        # Placeholder for processing user input and updating collected fields
        # This would include parsing user input and validating against schema
        # For now, just echo back the input
        return f"Received: {user_input}"

# This class can be integrated with FormCollectorAgent to handle LLM interactions.
