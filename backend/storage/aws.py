import boto3
from botocore.config import Config
from typing import Dict, Any, Optional
import os

class S3Storage:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            config=Config(
                region_name=os.getenv('AWS_REGION', 'us-east-1'),
                signature_version='v4',
                retries={'max_attempts': 3}
            )
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'bug-uploads-prod')

    def generate_presigned_post(
        self,
        file_name: str,
        file_type: str,
        file_size: int,
        expiration: int = 900  # 15 minutes
    ) -> Dict[str, Any]:
        """Generate a presigned POST URL for uploading a file to S3.
        
        Args:
            file_name: Original name of the file
            file_type: MIME type of the file
            file_size: Size of the file in bytes
            expiration: URL expiration time in seconds (default 15 minutes)
            
        Returns:
            Dict containing the URL and fields required for the POST request
        """
        if file_size > 100 * 1024 * 1024:  # 100MB
            raise ValueError("File size exceeds maximum allowed (100MB)")

        # Generate a unique key for the file
        key = f"temp/{file_name}"
        
        # Configure conditions for the upload
        conditions = [
            {"bucket": self.bucket_name},
            ["content-length-range", 0, 100 * 1024 * 1024],  # 0-100MB
            {"Content-Type": file_type}
        ]

        try:
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=key,
                Fields={
                    'Content-Type': file_type
                },
                Conditions=conditions,
                ExpiresIn=expiration
            )
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to generate presigned URL: {str(e)}")

    def move_to_permanent_storage(
        self,
        temp_key: str,
        permanent_key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Move a file from temporary to permanent storage location.
        
        Args:
            temp_key: Key of the file in temporary storage
            permanent_key: Key for the file in permanent storage
            metadata: Optional metadata to attach to the file
            
        Returns:
            The permanent storage URL
        """
        copy_source = {
            'Bucket': self.bucket_name,
            'Key': temp_key
        }
        
        extra_args = {
            'MetadataDirective': 'REPLACE',
            'ACL': 'private'
        }
        if metadata:
            extra_args['Metadata'] = metadata

        try:
            self.s3_client.copy(
                copy_source,
                self.bucket_name,
                permanent_key,
                ExtraArgs=extra_args
            )
            # Delete the temporary file
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=temp_key
            )
            return f"s3://{self.bucket_name}/{permanent_key}"
        except Exception as e:
            raise RuntimeError(f"Failed to move file to permanent storage: {str(e)}")