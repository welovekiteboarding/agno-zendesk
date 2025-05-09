from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
import boto3
import os
from datetime import timedelta, datetime, timezone
from typing import List
import logging
from prometheus_client import Counter, Gauge, start_http_server
from botocore.exceptions import ClientError

BUCKET_NAME = 'bug-upload-scanner'
REGION = os.environ.get('AWS_DEFAULT_REGION', 'ca-central-1')  # Change as needed
MAX_FILE_SIZE_MB = 100
ALLOWED_TYPES = ["image/png", "image/jpeg", "application/pdf", "text/plain"]  # Extend as needed

TEMP_PREFIX = 'temp/'
PERMANENT_PREFIX = 'permanent/'
CLEANUP_THRESHOLD_SECONDS = 24 * 3600  # 1 day

s3 = boto3.client('s3', region_name=REGION)
app = FastAPI()

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Prometheus metrics
PRESIGNED_URLS_GENERATED = Counter('presigned_urls_generated', 'Number of presigned URLs generated')
UPLOADS_CLEANED = Counter('uploads_cleaned', 'Number of abandoned uploads cleaned')

# Add a Gauge for number of files in temp and permanent
FILES_IN_TEMP = Gauge('files_in_temp', 'Number of files in temp folder')
FILES_IN_PERMANENT = Gauge('files_in_permanent', 'Number of files in permanent folder')

# Start Prometheus metrics server
start_http_server(8000)

class FileMeta(BaseModel):
    name: str
    type: str
    size: int  # bytes

@app.post("/generate-presigned-url")
def generate_presigned_url(meta: FileMeta, request: Request):
    print(f"[DEBUG] Incoming presign request: name={meta.name}, type={meta.type}, size={meta.size}")
    print(f"[DEBUG] HTTP headers: {dict(request.headers)}")
    if meta.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        logging.warning(f"File size exceeds limit: {meta.size} bytes")
        raise HTTPException(status_code=400, detail="File size exceeds 100MB limit.")
    if meta.type not in ALLOWED_TYPES:
        logging.warning(f"File type not allowed: {meta.type}")
        raise HTTPException(status_code=400, detail="File type not allowed.")
    key = f"temp/{meta.name}"
    try:
        url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': key,
                'ContentType': meta.type
            },
            ExpiresIn=900  # 15 minutes
        )
        PRESIGNED_URLS_GENERATED.inc()
        logging.info(f"Generated presigned URL for {key}")
        print(f"[DEBUG] Presigned URL: {url}")
        return {"url": url, "key": key, "expires_in": 900}
    except Exception as e:
        logging.error(f"Failed to generate presigned URL for {key}: {str(e)}")
        print(f"[DEBUG] Presign error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate presigned URL: {str(e)}")

@app.get("/admin/list-files")
def list_files(folder: str = "temp"):
    prefix = TEMP_PREFIX if folder == "temp" else PERMANENT_PREFIX
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
    files = []
    if 'Contents' in response:
        for obj in response['Contents']:
            files.append({
                "key": obj['Key'],
                "last_modified": obj['LastModified'],
                "size": obj['Size']
            })
    return {"files": files}

@app.post("/admin/cleanup-abandoned-uploads")
def cleanup_abandoned_uploads():
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=TEMP_PREFIX)
    now = datetime.now(timezone.utc)
    deleted = []
    if 'Contents' in response:
        for obj in response['Contents']:
            key = obj['Key']
            last_modified = obj['LastModified']
            age = (now - last_modified).total_seconds()
            if age > CLEANUP_THRESHOLD_SECONDS:
                s3.delete_object(Bucket=BUCKET_NAME, Key=key)
                deleted.append(key)
                logging.info(f"Deleted abandoned upload: {key}")
    UPLOADS_CLEANED.inc(len(deleted))
    logging.info(f"Cleanup complete: {len(deleted)} files deleted.")
    return {"deleted": deleted, "message": f"Deleted {len(deleted)} abandoned uploads."}

@app.get("/admin/monitor")
def monitor_files():
    temp_files = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=TEMP_PREFIX)
    perm_files = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PERMANENT_PREFIX)
    temp_count = len(temp_files.get('Contents', []))
    perm_count = len(perm_files.get('Contents', []))
    FILES_IN_TEMP.set(temp_count)
    FILES_IN_PERMANENT.set(perm_count)
    return {
        "temp_count": temp_count,
        "permanent_count": perm_count,
        "temp_files": [f["Key"] for f in temp_files.get('Contents', [])],
        "permanent_files": [f["Key"] for f in perm_files.get('Contents', [])]
    }

@app.head("/check-file-status")
def check_file_status(key: str):
    try:
        obj = s3.head_object(Bucket=BUCKET_NAME, Key=key)
        # Return AWS metadata in headers
        headers = {
            "x-s3-bucket": BUCKET_NAME,
            "x-s3-key": key,
            "x-s3-region": REGION,
            "x-s3-etag": obj.get("ETag", ""),
            "x-s3-lastmodified": str(obj.get("LastModified", "")),
        }
        return Response(status_code=200, headers=headers)
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return Response(status_code=404)
        raise HTTPException(status_code=500, detail="Unexpected S3 error: " + str(e))

# To run: uvicorn backend.attachment_upload_service:app --reload
