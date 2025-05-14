print("[DEBUG] Loading agno_agent_chat.py...")
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import json
from pathlib import Path
import logging

# Import Agno dependencies
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude

# Import Form Collector Agent
from agents.form_collector.form_collector import FormCollectorAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agno_agent_chat")

print("[DEBUG] Creating APIRouter for agno_agent_chat...")
router = APIRouter()

# ----- request / response schemas -----
class ChatRequest(BaseModel):
    session_id: str
    user_message: str
    meta: Optional[Dict[str, Any]] = None  # optional extras (e.g., file URLs)

class ChatResponse(BaseModel):
    assistant_message: str
    done: bool = False
    progress: Optional[str] = None
    agent_type: str = "agno"  # Indicates which agent is responding

# ----- in‑memory session store (swap for Redis later) -----
_sessions: Dict[str, Dict[str, Any]] = {}

# Load your bug report schema
SCHEMA_PATH = Path(__file__).parent.parent.parent / "schemas" / "bug_report.schema.json"
with open(SCHEMA_PATH) as f:
    BUG_REPORT_SCHEMA = json.load(f)

# Configure Agno Models based on available API keys
def get_agno_model():
    """Initialize the appropriate LLM model based on available API keys"""
    # Try Anthropic first
    if os.getenv("ANTHROPIC_API_KEY"):
        logger.info("Using Anthropic Claude model")
        return Claude(id="claude-3-7-sonnet-latest")
    # Fall back to OpenAI
    elif os.getenv("OPENAI_API_KEY"):
        logger.info("Using OpenAI model")
        return OpenAIChat(id="gpt-4o")
    # If no API keys are available
    else:
        logger.warning("No API keys found for Anthropic or OpenAI")
        return None

# Instructions for the Agno agent
AGNO_INSTRUCTIONS = [
    "You are Agno, a helpful general-purpose AI assistant.",
    "You can answer questions about any topic, provide information, and assist with various tasks.",
    "If a user indicates they want to report a bug, hand off to the form collector agent.",
    "Keep responses concise, helpful, and conversational.",
    "Do not introduce yourself as a bug reporting assistant.",
    "Be helpful, friendly, and courteous at all times."
]

def initialize_form_collector(session_id: str):
    """Initialize a form collector agent for the given session"""
    from api.routes.form_collector_chat import LLM_CLIENT
    
    logger.info(f"Initializing form collector for session {session_id}")
    form_collector = FormCollectorAgent(LLM_CLIENT, BUG_REPORT_SCHEMA)
    return form_collector

def get_session(session_id: str) -> Dict[str, Any]:
    """Get or create a session for the given session_id"""
    if session_id not in _sessions:
        logger.info(f"Creating new Agno agent session for {session_id}")
        
        # Initialize Agno agent
        model = get_agno_model()
        if model:
            agno_agent = Agent(
                model=model,
                instructions=AGNO_INSTRUCTIONS,
                markdown=True
            )
        else:
            agno_agent = None
            logger.warning("Could not initialize Agno agent due to missing API keys")
        
        # Create session container
        _sessions[session_id] = {
            "agno_agent": agno_agent,
            "form_collector": None,
            "current_agent": "agno",  # Start with Agno agent
            "history": []
        }
    
    return _sessions[session_id]

def should_handoff_to_form_collector(message: str) -> bool:
    """Determine if the conversation should be handed off to the form collector"""
    # Basic keywords that might indicate a bug report
    bug_report_indicators = [
        "report a bug", "submit a bug", "found a bug", "report an issue",
        "having a problem with", "not working", "broken", "doesn't work",
        "issue with", "error in", "problem with", "failed to", "crashes",
        "glitch", "defect", "malfunction"
    ]
    
    message_lower = message.lower()
    
    for indicator in bug_report_indicators:
        if indicator in message_lower:
            return True
    
    return False

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    logger.info(f"Received POST /chat with session_id={req.session_id} user_message={req.user_message}")
    
    # Get or create session
    session = get_session(req.session_id)
    
    try:
        # Determine if this is a handoff situation (from Agno to Form Collector)
        if session["current_agent"] == "agno" and should_handoff_to_form_collector(req.user_message):
            logger.info("Handing off from Agno agent to Form Collector agent")
            
            # Initialize form collector if not already done
            if not session["form_collector"]:
                session["form_collector"] = initialize_form_collector(req.session_id)
            
            # Generate handoff message from Agno agent
            if session["agno_agent"]:
                handoff_prompt = "The user wants to report a bug. Generate a brief handoff message explaining that you're transferring them to the bug reporting system, and they'll be guided through a form."
                handoff_response = session["agno_agent"].run(handoff_prompt)
                handoff_message = handoff_response.content
            else:
                handoff_message = "I'll transfer you to our specialized bug reporting system now. You'll be guided through a simple form to collect the necessary details."
            
            # Update session to use form collector for future messages
            session["current_agent"] = "form_collector"
            
            # Get initial message from form collector
            form_collector = session["form_collector"]
            initial_prompt = form_collector.get_field_prompt('reporterName')
            
            # Combine handoff message with initial form collector prompt
            combined_message = f"{handoff_message}\n\n{initial_prompt}"
            
            # Return the combined message
            return ChatResponse(
                assistant_message=combined_message,
                agent_type="agno->form_collector"  # Indicates a handoff
            )
        
        # Handle form collector messages
        elif session["current_agent"] == "form_collector":
            # Initialize form collector if not already done
            if not session["form_collector"]:
                session["form_collector"] = initialize_form_collector(req.session_id)
            
            # Process message with form collector
            form_collector = session["form_collector"]
            reply = form_collector.process_message(req.user_message, attachments=req.meta.get("attachments") if req.meta else None)
            done = form_collector.is_form_complete()
            
            if done:
                # If form is complete, revert to Agno agent for follow-up conversation
                session["current_agent"] = "agno"
            
            # Get progress info
            progress = f"{len(form_collector.get_collected_fields())} / {len(BUG_REPORT_SCHEMA.get('required', []))}"
            
            return ChatResponse(
                assistant_message=reply.split("(Note:")[0].strip(),  # Remove any error notes
                done=done,
                progress=progress,
                agent_type="form_collector"
            )
        
        # Handle Agno agent messages
        else:  # session["current_agent"] == "agno"
            agno_agent = session["agno_agent"]
            
            if agno_agent:
                # Process with Agno agent
                response = agno_agent.run(req.user_message)
                return ChatResponse(
                    assistant_message=response.content,
                    agent_type="agno"
                )
            else:
                # Fallback if no API keys are available
                return ChatResponse(
                    assistant_message="I'm currently unable to process your request due to configuration issues. Please try again later or contact support.",
                    agent_type="fallback"
                )
                
    except Exception as e:
        logger.error(f"Exception in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))