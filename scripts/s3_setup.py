import boto3
import json

BUCKET_NAME = 'bug-uploads-prod'
REGION = 'us-east-1'  # Change as needed

s3 = boto3.client('s3', region_name=REGION)

# 1. Create bucket if it doesn't exist
def create_bucket():
    buckets = [b['Name'] for b in s3.list_buckets()['Buckets']]
    if BUCKET_NAME not in buckets:
        s3.create_bucket(Bucket=BUCKET_NAME, CreateBucketConfiguration={'LocationConstraint': REGION})
        print(f"Bucket {BUCKET_NAME} created.")
    else:
        print(f"Bucket {BUCKET_NAME} already exists.")

# 2. Set CORS policy
def set_cors():
    cors_config = {
        'CORSRules': [{
            'AllowedHeaders': ['*'],
            'AllowedMethods': ['PUT', 'POST', 'GET'],
            'AllowedOrigins': ['*'],  # Restrict in production
            'ExposeHeaders': ['ETag'],
            'MaxAgeSeconds': 3000
        }]
    }
    s3.put_bucket_cors(Bucket=BUCKET_NAME, CORSConfiguration=cors_config)
    print("CORS policy set.")

# 3. Set lifecycle rule for 90-day deletion
def set_lifecycle():
    lifecycle_config = {
        'Rules': [{
            'ID': 'DeleteOldUploads',
            'Prefix': '',
            'Status': 'Enabled',
            'Expiration': {'Days': 90}
        }]
    }
    s3.put_bucket_lifecycle_configuration(Bucket=BUCKET_NAME, LifecycleConfiguration=lifecycle_config)
    print("Lifecycle rule set.")

# 4. Set bucket policy for restricted access
def set_policy():
    # Example: Only allow access from a specific IAM role (customize as needed)
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_APP_ROLE"},
                "Action": "s3:*",
                "Resource": [
                    f"arn:aws:s3:::{BUCKET_NAME}",
                    f"arn:aws:s3:::{BUCKET_NAME}/*"
                ]
            }
        ]
    }
    s3.put_bucket_policy(Bucket=BUCKET_NAME, Policy=json.dumps(policy))
    print("Bucket policy set.")

if __name__ == "__main__":
    create_bucket()
    set_cors()
    set_lifecycle()
    set_policy()
    print("S3 bucket setup complete.")
