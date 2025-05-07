import boto3
import os
import subprocess

BUCKET_NAME = 'bug-uploads-prod'
REGION = 'us-east-1'
TEMP_PREFIX = 'temp/'

s3 = boto3.client('s3', region_name=REGION)

def scan_file_with_clamav(local_path):
    # Assumes clamscan is installed and in PATH
    result = subprocess.run(['clamscan', local_path], capture_output=True, text=True)
    if 'OK' in result.stdout:
        return True, result.stdout
    return False, result.stdout

def handle_upload_event(bucket, key):
    # Download file
    local_path = f"/tmp/{os.path.basename(key)}"
    s3.download_file(bucket, key, local_path)
    # Scan file
    clean, output = scan_file_with_clamav(local_path)
    if clean:
        print(f"File {key} is clean.")
        # Mark as ready for transfer (could update DB or move to next step)
    else:
        print(f"File {key} is INFECTED! Quarantining or deleting.")
        # Optionally move to quarantine or delete
        s3.delete_object(Bucket=bucket, Key=key)
    os.remove(local_path)
    return clean, output

# Example usage: handle_upload_event(BUCKET_NAME, 'temp/example.png')
# In production, this would be triggered by S3 event notification (e.g., via Lambda or webhook)
