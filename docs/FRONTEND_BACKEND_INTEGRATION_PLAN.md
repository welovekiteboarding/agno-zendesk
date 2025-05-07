# Frontend-Backend Integration & MVP Launch Plan

This document explains, step-by-step, how to connect your frontend (Next.js/React) to the backend FastAPI microservice for file uploads and bug report submission, test the end-to-end workflow, and prepare for MVP deployment.

---

## 1. Integrate the Frontend with the Backend

**Goal:**
- Allow users to submit bug reports with file attachments.
- Frontend requests a presigned S3 URL from the backend, uploads files, and submits bug report data (including S3 keys).

**Steps:**
1. Identify or create the bug report form component in `frontend/`.
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

# Step 1: Begin Frontend Integration

- Locate or create the bug report form in `frontend/`.
- Add logic to POST file metadata to the backend and upload files to S3.
- Store the returned S3 key(s) in the form state for submission with the bug report.

# Next Steps
- After implementing the above, proceed to end-to-end testing as described.
