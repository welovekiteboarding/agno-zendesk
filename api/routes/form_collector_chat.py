print("[DEBUG] Loading form_collector_chat.py...")
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from agents.form_collector.form_collector import FormCollectorAgent
import json
import os
from openai import OpenAI, OpenAIError

print("[DEBUG] Creating APIRouter for form_collector_chat...")
router = APIRouter()

# ----- request / response schemas -----
class ChatRequest(BaseModel):
    session_id: str
    user_message: str
    meta: Optional[Dict[str, Any]] = None  # optional extras (e.g., file URLs)

class ChatResponse(BaseModel):
    assistant_message: str
    done: bool                      # True when schema passes
    progress: Optional[str] = None  # "3 / 9 fields"

# ----- in‑memory session store (swap for Redis later) -----
_sessions: Dict[str, FormCollectorAgent] = {}

# Load your bug report schema (adjust path as needed)
from pathlib import Path
SCHEMA_PATH = Path(__file__).parent.parent.parent / "schemas" / "bug_report.schema.json"
with open(SCHEMA_PATH) as f:
    BUG_REPORT_SCHEMA = json.load(f)

# OpenAI LLM client
class OpenAILLM:
    def __init__(self, model="gpt-3.5-turbo"):
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")
        self._client = None
        if not self.api_key:
            print("[WARN] OPENAI_API_KEY not set in environment, LLM features will be disabled")
        else:
            try:
                self._client = OpenAI(api_key=self.api_key)
                # Test the client
                test_response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                print("[INFO] OpenAI client initialized successfully")
            except Exception as e:
                print(f"[ERROR] Failed to initialize OpenAI client: {str(e)}")
                self._client = None

    def chat(self, prompt: str) -> str:
        # If no client, return a reasonable fallback response
        if not self._client:
            return prompt

        try:
            print(f"[DEBUG] Making OpenAI chat completion request with prompt: {prompt}")
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=256
            )
            response_text = response.choices[0].message.content
            print(f"[DEBUG] Got response from OpenAI: {response_text}")
            return response_text
        except Exception as e:
            print(f"[ERROR] OpenAI API error: {str(e)}")
            return prompt

# Initialize LLM client
print("[DEBUG] Initializing OpenAI LLM client...")
LLM_CLIENT = OpenAILLM()

def get_session(session_id: str) -> FormCollectorAgent:
    if session_id not in _sessions:
        print(f"[DEBUG] Creating new session for {session_id}")
        _sessions[session_id] = FormCollectorAgent(LLM_CLIENT, BUG_REPORT_SCHEMA)
    return _sessions[session_id]

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    print(f"[DEBUG] Received POST /chat with session_id={req.session_id} user_message={req.user_message}")
    agent = get_session(req.session_id)
    try:
        reply = agent.process_message(req.user_message, attachments=req.meta.get("attachments") if req.meta else None)
        done = agent.is_form_complete()
        progress = f"{len(agent.get_collected_fields())} / {len(BUG_REPORT_SCHEMA.get('required', []))}"
        print(f"[DEBUG] Agent reply: {reply}, done: {done}, progress: {progress}")
        return ChatResponse(
            assistant_message=reply.split("(Note:")[0].strip(),  # Remove any error notes
            done=done,
            progress=progress,
        )
    except Exception as e:
        print(f"[DEBUG] Exception in chat endpoint: {e}")
        raise HTTPException(status_code=400, detail=str(e))
