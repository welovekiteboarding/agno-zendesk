from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
# Always load .env from the project root, regardless of CWD
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

print("[DEBUG] Starting FastAPI app...")
app = FastAPI(title="Bug‑Report LLM Backend")

# Allow both production and local development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bug-widget.vercel.app", "http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
print("[DEBUG] CORS middleware added.")

from api.routes.form_collector_chat import router as fc_router
print("[DEBUG] Importing and registering form_collector_chat router...")
app.include_router(
    fc_router,
    prefix="/api/form-collector",
    tags=["Form‑Collector"]
)
print("[DEBUG] form_collector_chat router registered with prefix /api/form-collector.")

from backend.attachment_upload_service import app as upload_app
print("[DEBUG] Mounting attachment_upload_service app...")
app.mount("", upload_app)
print("[DEBUG] attachment_upload_service app mounted.")
