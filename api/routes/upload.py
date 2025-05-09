from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
from pydantic import BaseModel, Field, constr
from backend.storage.aws import S3Storage
import mimetypes

router = APIRouter()
s3 = S3Storage()

class PresignedUrlRequest(BaseModel):
    filename: constr(min_length=1, max_length=255)
    fileType: constr(min_length=1, max_length=100)
    fileSize: int = Field(..., gt=0, le=100*1024*1024)  # Max 100MB

@router.post("/presign")
async def generate_presigned_url(request: PresignedUrlRequest) -> Dict[str, Any]:
    """Generate a presigned URL for file upload.
    
    Args:
        request: Contains filename, fileType, and fileSize
        
    Returns:
        Dict containing presigned URL and required fields for POST request
    """
    # Validate mime type
    if not mimetypes.guess_extension(request.fileType):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type"
        )
    
    try:
        presigned_data = s3.generate_presigned_post(
            file_name=request.filename,
            file_type=request.fileType,
            file_size=request.fileSize
        )
        return presigned_data
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate presigned URL"
        )