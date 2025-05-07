import logging
import boto3
import os
import time
from datetime import datetime, timezone

BUCKET_NAME = 'bug-uploads-prod'
REGION = 'us-east-1'
TEMP_PREFIX = 'temp/'
CLEANUP_THRESHOLD_SECONDS = 24 * 3600  # 1 day

s3 = boto3.client('s3', region_name=REGION)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def cleanup_abandoned_uploads():
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=TEMP_PREFIX)
    now = datetime.now(timezone.utc)
    if 'Contents' not in response:
        logging.info('No files to clean up.')
        return
    for obj in response['Contents']:
        key = obj['Key']
        last_modified = obj['LastModified']
        age = (now - last_modified).total_seconds()
        if age > CLEANUP_THRESHOLD_SECONDS:
            s3.delete_object(Bucket=BUCKET_NAME, Key=key)
            logging.info(f"Deleted abandoned upload: {key} (age: {age/3600:.1f} hours)")
        else:
            logging.info(f"Retained: {key} (age: {age/3600:.1f} hours)")

if __name__ == "__main__":
    cleanup_abandoned_uploads()
