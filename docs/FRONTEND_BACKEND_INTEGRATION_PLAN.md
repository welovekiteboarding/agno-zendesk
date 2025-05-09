# Frontend-Backend Integration & MVP Launch Plan

This document explains, step-by-step, how to connect your frontend (Next.js/React) to the backend FastAPI microservice for file uploads and bug report submission, test the end-to-end workflow, and prepare for MVP deployment.

---

## 1. Integrate the Frontend with the Backend

**Goal:**
- Allow users to submit bug reports with file attachments.
- Frontend requests a presigned S3 URL from the backend, uploads files, and submits bug report data (including S3 keys).

**Steps:**
1. Identify or create the bug report form component in `frontend__backup2/`.
2. On file selection:
    - POST file metadata (name, type, size) to `/generate-presigned-url` on the backend.
    - Use the returned URL to upload the file to S3 via a PUT request.
    - Store the S3 key in the form state.
3. On form submit:
    - Send the bug report data (including S3 keys) to the backend or pipeline endpoint.

**Example (pseudo-code):**
```js
// 1. Get presigned URL
const res = await fetch('/api/generate-presigned-url', { method: 'POST', body: JSON.stringify({ name, type, size }) });
const { url, key } = await res.json();

// 2. Upload file to S3
await fetch(url, { method: 'PUT', body: file, headers: { 'Content-Type': type } });

// 3. Submit bug report (with S3 key)
await fetch('/api/submit-bug', { method: 'POST', body: JSON.stringify({ ...formData, attachments: [key] }) });
```

---

## 2. End-to-End Testing

- Manually test the workflow: fill out the bug report form, attach a file, and submit.
- Confirm in S3 that the file appears in the `temp/` folder, is scanned, and is moved to `permanent/`.
- Check backend logs and Prometheus metrics for successful operations.

---

## 3. MVP Deployment

- Review `frontend/vercel.json` and `backend/Dockerfile` for deployment readiness.
- Ensure all environment variables and AWS credentials are set for production.
- Deploy frontend to Vercel and backend to Render (or your chosen platform).

---

## 4. Update Task Master

- As you complete integration and testing, update Task Master to reflect progress.
- When ready, move to the next pending task (e.g., Email-Verifier AGNO Agent).

---

# How and Why to Run the Frontend and Backend Servers in This Project

## Overview

This project uses a **FastAPI backend** (Python) and a **Next.js frontend** (React/TypeScript). Each is developed and run independently, but they communicate via HTTP APIs. Running both servers locally allows you to develop, test, and debug the full end-to-end workflow before deploying to production.

---

## How to Run the Backend

**Command:**
```sh
PYTHONPATH=/Users/welovekiteboarding/Development/agno-zendesk:/Users/welovekiteboarding/Development/agno-zendesk/backend uvicorn main:app --reload --port 8001
```

**Explanation:**
- `PYTHONPATH=...` ensures Python can resolve imports from the modular backend code (e.g., agents, api, backend).
- `uvicorn main:app` starts the FastAPI server using the `main.py` entrypoint.
- `--reload` enables hot-reloading for development (auto-restarts on code changes).
- `--port 8001` runs the backend on port 8001 to avoid conflicts with the frontend.

**Why this way?**
- The backend is structured as multiple Python packages. Setting `PYTHONPATH` to the project root and backend folder ensures all imports work.
- Running on port 8001 avoids conflicts with the frontend (which defaults to 3000+).
- Hot-reloading speeds up development.

---

## How to Run the Frontend

**IMPORTANT: Use the `frontend__backup2` folder for the latest and most complete frontend implementation.**

**Command:**
```sh
cd frontend__backup2
npm run dev
```

**Explanation:**
- `cd frontend__backup2` navigates to the most up-to-date and complete frontend codebase. **Do not use `frontend/` or `frontend__backup/`—they are outdated or incomplete.**
- `npm run dev` starts the Next.js development server.
- If port 3000 is in use, Next.js will automatically use the next available port (e.g., 3002).

**Why this way?**
- The `frontend__backup2` folder contains the latest, most complete implementation.
- Next.js’s dev server provides hot-reloading and fast feedback for UI changes.
- Running the frontend separately from the backend allows independent development and debugging.

---

## How They Work Together

- The frontend communicates with the backend via HTTP (e.g., for bug report submission, file upload presigned URLs).
- By running both servers locally, you can test the full workflow as a user would experience it in production.
- This separation mirrors the production deployment, where the frontend (e.g., on Vercel) and backend (e.g., on Render) are also independent services.

---

## Summary

- **Backend:** Run with `uvicorn` and set `PYTHONPATH` for modular imports.
- **Frontend:** Run with `npm run dev` in the `frontend__backup2` directory.
- **Ports:** Use different ports to avoid conflicts and allow both servers to run simultaneously.
- **Why:** This setup matches production, supports modular code, and enables efficient development and testing.

---

**Result:**  
You can access the frontend in your browser (e.g., http://localhost:3002), which will interact with the backend at http://localhost:8001, allowing you to test the complete application locally.

---

# Step 1: Begin Frontend Integration

- Locate or create the bug report form in `frontend__backup2/`.
- Add logic to POST file metadata to the backend and upload files to S3.
- Store the returned S3 key(s) in the form state for submission with the bug report.

---

# May 8, 2025: File Upload Integration Plan and Progress Log

## Current State
- The backend pipeline for file upload, scanning, and permanent storage is implemented and working.
- The chat UI (ChatUI.tsx) is implemented and communicates with the backend, but does not yet support file uploads.
- The S3UploadTest.tsx component demonstrates file upload logic, but is not integrated into the chat UI.

## Integration Plan for Chat UI File Uploads

### 1. Detect When Attachments Are Needed
- The chat UI must detect when the backend expects the `attachments` field (based on schema or backend response).
- This will trigger the file upload UI in the chat flow.

### 2. Prompt the User for Files
- When attachments are needed, show a file input (allowing 1–3 files, 100MB max, preferred types: image/log/doc).
- Display a message explaining the requirements and process.

### 3. Request Presigned URL and Upload to S3
- For each file selected:
  - POST file metadata (name, type, size) to `/generate-presigned-url`.
  - Use the returned URL to upload the file to S3 under `temp/`.
  - Store the returned S3 key (e.g., temp/screenshot.png) locally.

### 4. Poll for Scan Completion
- Every 2s, call a backend endpoint (e.g., `HEAD /check-file-status?key=temp/screenshot.png`).
  - 200: file is now in permanent/ (clean)
  - 404: file was deleted (virus)
  - 403: still pending (optional)
- If clean, add the permanent/ key to meta.attachments.
- If virus, show an error and allow retry.

### 5. Send Attachments to Backend
- Once all files are scanned and in permanent/, send the next chat message with meta.attachments set to the array of permanent/ S3 keys.

### 6. UI Enhancements
- Show checkmark and timestamp when file is in permanent/.
- Show retry option if a file is deleted.
- Disable message send button until scan is complete.

## Progress Log
- [x] Reviewed S3UploadTest.tsx for reusable upload logic.
- [x] Reviewed ChatUI.tsx for chat flow and backend integration.
- [ ] Plan to update ChatUI.tsx to:
  - Detect when attachments are needed
  - Integrate file upload UI and logic
  - Poll for scan completion
  - Send permanent/ S3 keys in meta.attachments
- [ ] Document all changes and decisions here as work progresses.
- [ ] May 8, 2025: Started implementation of file upload integration in ChatUI.tsx. Will:
  - Detect when attachments are needed in the chat flow
  - Render file input UI
  - Reuse S3 upload logic from S3UploadTest.tsx
  - Poll for scan completion and handle errors
  - Send permanent/ S3 keys in meta.attachments
  - Document each step and only modify what is necessary

---

# Next Steps
- Update ChatUI.tsx to support file uploads as described above, reusing S3UploadTest.tsx logic where possible.
- Document all changes and decisions in this file as work progresses.
