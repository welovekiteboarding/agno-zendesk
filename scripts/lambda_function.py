import boto3
import os
import subprocess

def scan_file_with_clamav(local_path):
    result = subprocess.run(['clamscan', local_path], capture_output=True, text=True)
    if 'OK' in result.stdout:
        return True, result.stdout
    return False, result.stdout

def move_to_permanent_storage(s3, bucket, filename):
    temp_key = f"temp/{filename}"
    perm_key = f"permanent/{filename}"
    s3.copy_object(Bucket=bucket, CopySource={"Bucket": bucket, "Key": temp_key}, Key=perm_key)
    s3.delete_object(Bucket=bucket, Key=temp_key)
    return perm_key

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        filename = os.path.basename(key)
        local_path = f"/tmp/{filename}"
        s3.download_file(bucket, key, local_path)
        clean, output = scan_file_with_clamav(local_path)
        if clean:
            move_to_permanent_storage(s3, bucket, filename)
            print(f"{key} is clean and moved to permanent storage.")
        else:
            s3.delete_object(Bucket=bucket, Key=key)
            print(f"{key} is INFECTED and deleted.")
        os.remove(local_path)
    return {'statusCode': 200, 'body': 'Processed S3 event.'}
