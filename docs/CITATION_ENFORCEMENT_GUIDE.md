# Citation Enforcement in RAG System

This document outlines the implementation of a mandatory citation system for the RAG responses in the Agno Zendesk integration. The system ensures every statement in responses is backed by at least one citation from the knowledge base, helping to prevent hallucinations and ensure factual accuracy.

## Architecture Overview

The citation enforcement system works through several key components:

1. **Synthesis Agent**: Responsible for generating responses with appropriate citations
2. **Response Validation**: Checks responses for proper citation formatting and coverage
3. **Response Regeneration**: Attempts to fix responses lacking proper citations
4. **Error Handling**: Ensures graceful fallback behavior when perfect responses cannot be generated

## Key Components

### 1. Synthesis Agent

The Synthesis Agent is the core component for response generation with citations. It:

- Builds system and user prompts that include strict citation requirements
- Processes research results to format citations appropriately
- Validates responses to ensure they contain citations
- Regenerates responses if they lack proper citations

**Key File**: `/agno_zendesk/multi_agent/agents/synthesis_agent.py`

```python
class SynthesisAgent(BaseAgent):
    """
    Synthesis Agent for generating coherent responses with citations
    from retrieved information.
    """
    
    def __init__(self, 
                 agent_id: str,
                 name: str,
                 description: str,
                 model: Optional[str] = "gpt-4o",  # Ensure we always have a model
                 temperature: float = 0.7,
                 max_tokens: int = 1000,
                 enforce_citations: bool = True,
                 enforce_multiple_citations: bool = True):
        """
        Initialize the synthesis agent.
        
        Args:
            agent_id: Agent ID
            name: Agent name
            description: Agent description
            model: LLM model to use
            temperature: Model temperature
            max_tokens: Maximum tokens for response
            enforce_citations: Whether to enforce citations
            enforce_multiple_citations: Whether to enforce multiple citations
        """
        super().__init__(agent_id, name, description)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enforce_citations = enforce_citations
        self.enforce_multiple_citations = enforce_multiple_citations
```

### 2. System Prompt Construction

The system prompt is designed to enforce strict citation requirements:

```python
def _build_system_prompt(self, context: AgentContext) -> str:
    """
    Build the system prompt for the LLM.
    """
    return (
        f"You are a knowledgeable assistant specialized in answering questions about {context.metadata.get('domain', 'technical topics')}. "
        "Your responses must adhere to these strict requirements:\n\n"
        "1. Every statement you make MUST be based ONLY on the context provided.\n"
        "2. Do NOT invent, assume, or add any information not explicitly in the context.\n"
        "3. Start your response with \"(Based on provided context)\" to acknowledge this limitation.\n"
        "4. EVERY factual statement must include at least one citation in the format [X] where X is the citation number.\n"
        "5. Format your response in clear, concise Markdown with appropriate headers and bullet points.\n"
        "6. If the context doesn't contain enough information to provide a complete answer, acknowledge the limitations of what you can answer.\n"
        "7. Never fabricate citations or reference nonexistent sources.\n"
    )
```

### 3. Response Validation

The system validates responses to ensure they contain citations according to requirements:

```python
async def _validate_response(self, response: str, citation_count: int) -> bool:
    """
    Validate the response to ensure it follows citation guidelines.
    
    Args:
        response: The generated response
        citation_count: Number of available citations
        
    Returns:
        Whether the response is valid
    """
    if not response:
        return False
        
    # Check for required prefix
    if not response.startswith("(Based on provided context)"):
        logger.warning("Response does not start with required prefix")
        return False
        
    # Count citations in response
    citation_pattern = r'\[\d+\]'
    citations_in_response = re.findall(citation_pattern, response)
    
    if not citations_in_response:
        logger.warning("Response missing citations")
        return False
        
    # Check citation coverage by counting sentences vs. citations
    sentences = re.split(r'(?<=[.!?])\s+', response)
    sentences = [s for s in sentences if len(s.strip()) > 0]
    sentences_with_citations = sum(1 for s in sentences if re.search(citation_pattern, s))
    
    # At least 75% of sentences should have citations
    citation_ratio = sentences_with_citations / len(sentences) if sentences else 0
    if citation_ratio < 0.75:
        logger.warning(f"Only {sentences_with_citations}/{len(sentences)} sentences have citations")
        return False
    
    return True
```

### 4. Response Regeneration

When validation fails, the system attempts to regenerate responses:

```python
async def _regenerate_with_citations(self, original_response: str, context: AgentContext) -> str:
    """
    Attempt to regenerate a response with proper citations if original validation failed.
    
    Args:
        original_response: The original response that failed validation
        context: The agent context with citation data
        
    Returns:
        Regenerated response with proper citations
    """
    # Create a stronger system prompt for regeneration
    enhanced_system_prompt = (
        "You MUST revise the following response to include proper citations. "
        "EVERY factual statement MUST have at least one citation in [X] format. "
        "Start with '(Based on provided context)'. "
        "DO NOT make up information - only use the provided citations."
    )
    
    # Add the original response and available citations
    formatted_citations = self._format_citations(context.citations)
    user_prompt = (
        f"Original response (missing citations):\n\n{original_response}\n\n"
        f"Available citations to use:\n\n{formatted_citations}\n\n"
        f"Revise the response to include a citation for EVERY claim using [X] format."
    )
    
    try:
        # Call the LLM for regeneration
        client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": enhanced_system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,  # Lower temperature for more deterministic output
            max_tokens=self.max_tokens
        )
        
        # Extract the regenerated response
        regenerated_text = response.choices[0].message.content
        
        # Validate the regenerated response
        is_valid = await self._validate_response(regenerated_text, len(context.citations))
        if not is_valid:
            logger.warning("Regenerated response still fails validation, making one more attempt with stronger guidance")
            
            # One more attempt with even stronger guidance
            final_system_prompt = (
                "EMERGENCY CITATION CORRECTION REQUIRED! "
                "Your response MUST include citations in [X] format after EVERY single statement. "
                "No exceptions! Start with '(Based on provided context)'. "
                "If you cannot properly cite a statement, remove it entirely."
            )
            
            final_response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": final_system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=self.max_tokens
            )
            
            return final_response.choices[0].message.content
            
        return regenerated_text
    except Exception as e:
        logger.error(f"Error regenerating response: {str(e)}")
        return original_response  # Fall back to original if regeneration fails
```

### 5. Widget Integration Error Handling

To ensure the API never returns null responses, we implemented fallback handling:

**Key File**: `/agno_zendesk/multi_agent/integration/widget_integration.py`

```python
def _format_widget_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a system result for the widget.
    """
    # Extract response with fallback to ensure we never have a null response
    response_text = result.get("response", "") 
    
    # Ensure we have a valid string response (required by API model)
    if response_text is None or not isinstance(response_text, str):
        logger.warning(f"Invalid response text: {response_text}. Using fallback response.")
        response_text = "(Based on provided context)\n\nSorry, I could not generate a valid response for your query. Please try rephrasing your question with more specific details."
    
    # Format citations for the widget
    citations = []
    for citation in result.get("citations", []):
        formatted_citation = {
            "id": citation.get("id"),
            "source": citation.get("collection", "unknown"),
            "relevance": citation.get("relevance", "Medium"),
            "content": citation.get("content", ""),
            "metadata": citation.get("metadata", {})
        }
        citations.append(formatted_citation)
    
    # Create a widget-compatible response
    widget_response = {
        "query": result.get("query", ""),
        "response": response_text,
        "conversation_id": result.get("conversation_id", ""),
        "citations": citations,
        "processing_time": result.get("processing_time", 0),
        "timestamp": datetime.now().isoformat()
    }
    
    return widget_response
```

### 6. Multi-Agent System Citation Handling

Updated the system to properly pass citation data to the API response:

**Key File**: `/agno_zendesk/multi_agent/core/system.py`

```python
async def process_query(self, 
                        query: str,
                        conversation_id: Optional[str] = None,
                        workflow_id: Optional[str] = "standard_rag",
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Process a user query through the multi-agent system.
    """
    # ... [existing code] ...
    
    # Prepare result
    result = {
        "query": query,
        "response": response,
        "conversation_id": updated_context.conversation_id,
        "workflow_id": workflow_id,
        "processing_time": (datetime.now() - context.created_at).total_seconds(),
        "citation_count": len(updated_context.citations),
        "citations": updated_context.citations,  # Make sure to pass the actual citations
        "error_count": len(updated_context.errors)
    }
    
    # ... [rest of method] ...
```

## Testing the Citation Enforcement

To test the citation enforcement:

1. Start the widget server:
   ```bash
   python scripts/run_widget_server.py
   ```

2. Send a test query through the API endpoint:
   ```bash
   curl -X POST "http://localhost:8080/widget/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "How do I align my Celestron AVX using Celestron WiFi and SkySafari?"}'
   ```

3. Verify that the response:
   - Begins with "(Based on provided context)"
   - Contains citation markers [1], [2], etc.
   - Includes the citations array in the JSON response

## Troubleshooting

Common issues and solutions:

1. **Missing Citations in Response**: Check that the system prompt is correctly enforcing citations and that the validation logic is working.

2. **Response Validation Failing**: Adjust the validation parameters or regeneration logic if responses consistently fail to meet citation requirements.

3. **API Validation Errors**: Ensure the widget integration handles null or invalid responses properly with fallback mechanisms.

4. **Model Parameter Issues**: Verify that a valid model is always specified when calling OpenAI.

## Conclusion

This citation enforcement system ensures that all responses from the RAG system are properly backed by citations from the knowledge base. By enforcing citations, the system minimizes hallucinations and provides users with more reliable, factual information with clear references to the sources.
