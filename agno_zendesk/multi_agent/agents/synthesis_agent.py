"""
Synthesis Agent Implementation

This agent specializes in synthesizing information retrieved from AstraDB 
and producing coherent responses with proper citations.
"""

import logging
import json
import re
import os
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

from ..core.agent_interface import Agent, AgentContext

# For OpenAI integration
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("synthesis_agent")


class SynthesisAgent(Agent):
    """
    Agent specializing in synthesizing information and generating coherent responses.
    Ensures proper citation usage and context integration in response generation.
    """
    
    def __init__(self, 
                 agent_id: str,
                 name: str,
                 description: str,
                 model: Optional[str] = "gpt-4o",
                 temperature: float = 0.7,
                 max_tokens: int = 1000,
                 enforce_citations: bool = True,
                 enforce_multiple_citations: bool = True):
        """
        Initialize the synthesis agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            description: Detailed description of the agent's purpose
            model: LLM model to use for synthesis
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in generated response
            enforce_citations: Whether to enforce citations in responses
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            role="synthesis",
            model=model
        )
        
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enforce_citations = enforce_citations
        
    async def can_handle(self, context: AgentContext) -> bool:
        """
        Check if this agent can handle the given context.
        Synthesis agent requires research results to be present.
        
        Args:
            context: The agent context
            
        Returns:
            True if the agent can handle the context, False otherwise
        """
        # Check if we have formatted context from research
        has_formatted_context = "formatted_context" in context.results
        
        # Check if we have citations
        has_citations = len(context.citations) > 0
        
        return has_formatted_context or has_citations
    
    def _build_system_prompt(self, context: AgentContext) -> str:
        """
        Build the system prompt for the OpenAI model that matches the other widget approach
        """
        system_prompt = (
            "IMPORTANT: You are an AI assistant specializing in astronomy software and equipment. "
            "You ONLY use the provided context to answer questions but aim to be thorough and engaging.\n\n"
            
            "STRICT RULES:\n"
            "1. ONLY use information explicitly stated in the provided context\n"
            "2. EVERY statement must include a citation (e.g. [1], [2])\n"
            "3. If you cannot find relevant information in the context, respond EXACTLY with:\n"
            "   \"Sorry, I cannot generate a reply given your query and the context I retrieved. "
            "Please consider providing more information in your requests; i.e. program, version, feature, "
            "operating system, specific problem, etc.\"\n"
            "4. Do not make assumptions or inferences beyond what is directly stated\n"
            "5. Do not mention that you are using context or citations\n"
            "6. Start every response with \"(Based on provided context)\"\n\n"
            
            "RESPONSE STYLE:\n"
            "1. Be thorough and detailed in your explanations\n"
            "2. Break down complex procedures into clear, manageable steps\n"
            "3. Use a friendly, conversational tone\n"
            "4. After answering, suggest related topics or offer to explain in more detail\n"
            "5. If the user's question is broad, start with an overview and offer to dive deeper into specific aspects\n\n"
            
            "RESPONSE FORMAT:\n"
            "1. Start with a brief overview of what you'll cover\n"
            "2. Use \"###\" for main section headings\n"
            "3. Use **bold** for emphasis and UI elements\n"
            "4. Use bullet points (-) for lists\n"
            "5. Use numbered steps (1.) for procedures\n"
            "6. Include relevant citations after each statement [X]\n"
            "7. End with a follow-up suggestion or offer for more details\n"
        )
        
        # Add citation requirements if enabled
        if self.enforce_citations:
            system_prompt += (
                f"\n\nCitation Requirements:\n"
                f"- EVERY factual claim must be supported by at least one citation.\n"
                f"- Only use the numbered citations provided in the context.\n"
                f"- If information cannot be found in the context, clearly state this rather than making things up.\n"
                f"- In your response, use the citation format [X] where X is the citation number.\n"
            )
            
        return system_prompt
    
    def _build_user_prompt(self, context: AgentContext) -> str:
        """
        Build the user prompt for the synthesis agent.
        
        Args:
            context: The agent context
            
        Returns:
            User prompt for the LLM
        """
        # Get the formatted context with citations from the research agent
        formatted_context = ""
        if "formatted_context" in context.results:
            formatted_context = context.get_result("formatted_context")
        
        # Extract all citations from the context object
        citation_texts = []
        for i, citation in enumerate(context.citations, 1):
            source = citation.get("source", "Unknown")
            content = citation.get("content", "")
            citation_texts.append(f"[{i}] (Collection: {source})\n{content}\n")
        
        # Combine formatted context with direct citation access
        enhanced_context = formatted_context
        if not formatted_context and citation_texts:
            enhanced_context = "\n---\n".join(citation_texts)
        
        # Build the user prompt with enhanced citation context
        # Format citations to match the approach of the other widget
        relevant_citations = []
        for i, citation in enumerate(citation_texts, 1):
            # Extract relevance from citation if available
            relevance_match = re.search(r'\$(similarity|score): ([0-9.]+)', citation, re.IGNORECASE)
            relevance_score = float(relevance_match.group(2)) if relevance_match else 0.5
            relevance_indicator = "High" if relevance_score > 0.7 else "Medium" if relevance_score > 0.5 else "Low"
            
            # Format citation with relevance indicator
            formatted_citation = f"[{i}] (Relevance: {relevance_indicator})\n{citation}"
            relevant_citations.append(formatted_citation)
        
        formatted_citations = "\n---\n".join(relevant_citations)
        
        # Add citation policy similar to the other widget - with stronger enforcement
        citation_policy = (
            f"\n\nCitation Policy:\n"
            f"- CRITICAL: EVERY statement you make MUST reference at least one citation [X]\n"
            f"- Citations MUST appear after each sentence or claim - not just at the end of paragraphs\n"
            f"- Only use citations [1] through [{len(citation_texts)}]\n"
            f"- Start your response with '(Based on provided context)'\n"
            f"- If information is not found in citations, respond EXACTLY with: 'Sorry, I cannot generate a reply given your query and the context I retrieved. "
            f"Please consider providing more information in your requests; i.e. program, version, feature, operating system, specific problem, etc.'"
        )
        
        user_prompt = (
            f"Query: {context.query}\n\n"
            f"Here is the relevant context from the documentation. Use ALL of this information to answer the user's question:\n\n"
            f"{formatted_citations}\n"
            f"{citation_policy}"
        )
        
        return user_prompt
        
    async def process(self, context: AgentContext) -> AgentContext:
        """
        Process the given context by synthesizing information into a response.
        
        Args:
            context: The agent context
            
        Returns:
            Updated context with synthesized response
        """
        logger.info(f"Synthesis agent processing for query: {context.query}")
        
        try:
            # Build prompts
            system_prompt = self._build_system_prompt(context)
            user_prompt = self._build_user_prompt(context)
            
            # Get API key
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            # Initialize OpenAI client
            client = openai.AsyncOpenAI(api_key=openai_api_key)
            
            # Call the OpenAI API
            logger.info(f"Calling OpenAI with model: {self.model}")
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Extract the response text
            response_text = response.choices[0].message.content
            
            # Validate citations if enforcement is enabled
            if self.enforce_citations and response_text:
                try:
                    is_valid = await self._validate_response(response_text, len(context.citations))
                    if not is_valid:
                        logger.warning("Response missing citations, requesting regeneration")
                        new_response = await self._regenerate_with_citations(response_text, context)
                        # Ensure we always have a valid string response
                        if new_response and isinstance(new_response, str):
                            response_text = new_response
                except Exception as e:
                    logger.error(f"Error validating citations: {str(e)}")
                    # Do not update response_text if validation fails
            
            # Add the response to the context
            context.set_result("synthesized_response", response_text)
            
            # Add memory entry for this operation
            context.update_memory({
                "agent": self.name,
                "action": "synthesis",
                "response_length": len(response_text) if response_text else 0,
                "model_used": self.model,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info("Synthesis completed successfully")
            return context
            
        except Exception as e:
            logger.error(f"Error in synthesis agent: {str(e)}")
            context.add_error(
                self.agent_id,
                f"Synthesis failed: {str(e)}"
            )
            return context
            
    async def _validate_response(self, response: str, citation_count: int) -> bool:
        """
        Validate that the response follows citation guidelines.
        
        Args:
            response: Generated response to validate
            citation_count: Number of available citations
            
        Returns:
            True if valid, False otherwise
        """
        if not self.enforce_citations:
            return True
            
        # Check for citation pattern [X] where X is a number
        citation_pattern = r"\[(\d+)\]"
        used_citations = re.findall(citation_pattern, response)
        
        if not used_citations:
            logger.warning("Response missing citations")
            return False
        
        # Make sure response starts with appropriate prefix
        if not response.strip().startswith("(Based on provided context)"):
            logger.warning("Response missing required prefix '(Based on provided context)'")
            return False
            
        # Count sentences without citations (each sentence should have a citation)
        sentences = re.split(r'[.!?]\s+', response)
        sentences_with_citations = sum(1 for sentence in sentences if re.search(citation_pattern, sentence))
        if sentences_with_citations < len(sentences) * 0.8:  # At least 80% of sentences should have citations
            logger.warning(f"Only {sentences_with_citations}/{len(sentences)} sentences have citations")
            return False
        
        # Enforce multiple citations if required
        if self.enforce_multiple_citations and len(set(used_citations)) < 2:
            logger.warning("Response doesn't use multiple citations")
            return False
            
        # Convert to integers and check range
        try:
            used_citation_nums = [int(c) for c in used_citations]
            for num in used_citation_nums:
                if num < 1 or num > citation_count:
                    logger.warning(f"Invalid citation number: {num}")
                    return False
        except ValueError:
            logger.warning("Invalid citation format")
            return False
            
        return True
        
    async def _regenerate_with_citations(self, response_text: str, context: AgentContext) -> str:
        """
        Regenerate response with proper citations when validation fails.
        
        Args:
            response_text: The original response that failed validation
            context: The agent context containing citations
            
        Returns:
            Regenerated response with proper citations
        """
        try:
            # Get API key
            openai_api_key = os.getenv("OPENAI_API_KEY")
            client = openai.AsyncOpenAI(api_key=openai_api_key)
            
            # Create a stronger system prompt that emphasizes citation requirements
            enhanced_system_prompt = self._build_system_prompt(context) + """
            
            CRITICAL CITATION REQUIREMENT:
            1. You MUST start your response with "(Based on provided context)"
            2. EVERY statement or claim MUST be followed by at least one citation in [X] format
            3. You MUST use at least 2 different citations from the provided context
            4. Citations should appear AFTER each sentence, not just at the end of paragraphs
            5. If you cannot find information in the citations, say: "Sorry, I cannot generate a reply given your query and the context I retrieved."
            """
            
            # Request a fixed version with proper citations
            fix_prompt = (
                f"The following response is missing proper citations or formatting. Please rewrite it to include citation references "
                f"in the format [X] after EACH statement or claim. Use at least 2 different citations from 1 to {len(context.citations)}.\n\n"
                f"Original response:\n{response_text}\n\n"
                f"Rewritten response with proper citations after EACH statement (start with '(Based on provided context)'):"
            )
            
            # Make a new API call with enhanced citation requirements
            fix_response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": enhanced_system_prompt},
                    {"role": "user", "content": fix_prompt}
                ],
                temperature=0.2,  # Lower temperature for stricter adherence to requirements
                max_tokens=self.max_tokens
            )
            
            fixed_response = fix_response.choices[0].message.content
            
            # Add a fallback response in case all citation enforcement fails
            fallback_response = "(Based on provided context)\n\nSorry, I cannot generate a reply given your query and the context I retrieved. Please consider providing more information in your requests; i.e. program, version, feature, operating system, specific problem, etc."
            
            # Validate the fixed response
            try:
                is_valid = await self._validate_response(fixed_response, len(context.citations))
                if not is_valid:
                    logger.warning("Regenerated response still fails validation, making one more attempt with stronger guidance")
                    
                    # One more attempt with even stronger guidance
                    final_attempt_prompt = (
                        f"CRITICAL ERROR: Your response STILL lacks proper citations.\n\n"
                        f"REQUIREMENTS:\n"
                        f"1. START WITH: '(Based on provided context)'\n"
                        f"2. After EVERY SINGLE SENTENCE, add a citation like [1] or [2]\n"
                        f"3. Use AT LEAST citations [1] and [2]\n"
                        f"4. DO NOT say 'According to' - just state facts followed by citations\n\n"
                        f"EXAMPLE FORMAT:\n"
                        f"(Based on provided context)\n"
                        f"SkySafari helps connect to telescopes via WiFi. [1] The connection process requires specific hardware. [2] Users can control movement with the app. [1]\n\n"
                        f"Now rewrite with proper citations:"
                    )
                    
                    try:
                        final_attempt = await client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": enhanced_system_prompt},
                                {"role": "user", "content": final_attempt_prompt}
                            ],
                            temperature=0.1,  # Even lower temperature for strict adherence
                            max_tokens=self.max_tokens
                        )
                        
                        final_response = final_attempt.choices[0].message.content
                        if final_response and isinstance(final_response, str):
                            return final_response
                    except Exception as e:
                        logger.error(f"Error in final citation attempt: {str(e)}")
                        return fallback_response
                        
                return fixed_response
            except Exception as e:
                logger.error(f"Error validating regenerated response: {str(e)}")
                return fallback_response
            
        except Exception as e:
            logger.error(f"Error regenerating with citations: {str(e)}")
            # Return original response if regeneration fails
            return response_text
