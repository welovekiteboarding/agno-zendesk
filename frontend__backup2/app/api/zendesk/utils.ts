import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { zendeskConfig } from './config';

// Initialize S3 client based on configuration
function getS3Client() {
  if (zendeskConfig.useAwsS3) {
    // Use AWS S3
    return new S3Client({
      region: zendeskConfig.awsRegion,
      credentials: {
        accessKeyId: zendeskConfig.awsAccessKeyId,
        secretAccessKey: zendeskConfig.awsSecretAccessKey
      }
    });
  } else {
    // Use Cloudflare R2
    return new S3Client({
      region: 'auto',
      endpoint: zendeskConfig.r2Endpoint,
      credentials: {
        accessKeyId: zendeskConfig.r2AccessKey,
        secretAccessKey: zendeskConfig.r2SecretKey
      }
    });
  }
}

// Generate a presigned URL for file download from storage
export async function getFilePresignedUrl(key: string): Promise<string> {
  try {
    const s3Client = getS3Client();
    
    const command = new GetObjectCommand({
      Bucket: zendeskConfig.useAwsS3 ? zendeskConfig.awsBucketName : zendeskConfig.r2BucketName,
      Key: key
    });
    
    // Generate presigned URL that expires in 15 minutes
    const presignedUrl = await getSignedUrl(s3Client, command, { expiresIn: 900 });
    return presignedUrl;
  } catch (error) {
    console.error('Error generating presigned URL:', error);
    throw error;
  }
}

// Extract file name from S3/R2 key
export function getFileNameFromKey(key: string): string {
  // Get the last part of the path
  const parts = key.split('/');
  return parts[parts.length - 1];
}

// Guess content type from file name
export function guessContentType(fileName: string): string {
  const extension = fileName.split('.').pop()?.toLowerCase();
  
  switch (extension) {
    case 'jpg':
    case 'jpeg':
      return 'image/jpeg';
    case 'png':
      return 'image/png';
    case 'gif':
      return 'image/gif';
    case 'pdf':
      return 'application/pdf';
    case 'doc':
      return 'application/msword';
    case 'docx':
      return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    case 'xls':
      return 'application/vnd.ms-excel';
    case 'xlsx':
      return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
    case 'zip':
      return 'application/zip';
    case 'txt':
      return 'text/plain';
    case 'csv':
      return 'text/csv';
    case 'json':
      return 'application/json';
    case 'xml':
      return 'application/xml';
    case 'mp4':
      return 'video/mp4';
    case 'mov':
      return 'video/quicktime';
    case 'mp3':
      return 'audio/mpeg';
    default:
      return 'application/octet-stream';
  }
}

// Prepare S3/R2 attachments for Zendesk upload
export async function prepareAttachmentsForZendesk(attachmentKeys: string[]): Promise<any[]> {
  const attachments = [];
  
  for (const key of attachmentKeys) {
    // Skip if it's the 'skipped-attachments' placeholder
    if (key === 'skipped-attachments') {
      continue;
    }
    
    try {
      const fileName = getFileNameFromKey(key);
      const contentType = guessContentType(fileName);
      const fileUrl = await getFilePresignedUrl(key);
      
      attachments.push({
        key,
        fileName,
        contentType,
        fileUrl
      });
    } catch (error) {
      console.error(`Error preparing attachment ${key}:`, error);
      // Continue with other attachments even if one fails
    }
  }
  
  return attachments;
}