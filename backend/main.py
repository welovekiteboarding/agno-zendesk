from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

print("[DEBUG] Starting FastAPI app...")
app = FastAPI(title="Bug‑Report LLM Backend")

# Allow both production and local development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bug-widget.vercel.app", "http://localhost:3000", "http://localhost:3002"],
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
