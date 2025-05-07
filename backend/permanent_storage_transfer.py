import boto3

BUCKET_NAME = 'bug-uploads-prod'
REGION = 'us-east-1'
TEMP_PREFIX = 'temp/'
PERMANENT_PREFIX = 'permanent/'

s3 = boto3.client('s3', region_name=REGION)

def move_to_permanent_storage(filename):
    temp_key = f"{TEMP_PREFIX}{filename}"
    perm_key = f"{PERMANENT_PREFIX}{filename}"
    # Copy file to permanent location
    s3.copy_object(Bucket=BUCKET_NAME, CopySource={"Bucket": BUCKET_NAME, "Key": temp_key}, Key=perm_key)
    # Optionally, update metadata or prepare for Zendesk here
    # Delete from temp
    s3.delete_object(Bucket=BUCKET_NAME, Key=temp_key)
    print(f"Moved {filename} to permanent storage.")
    return perm_key

# Example usage: move_to_permanent_storage('example.png')
