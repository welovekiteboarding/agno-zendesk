# File Attachment Implementation Plan for Zendesk Integration

This document outlines the plan for implementing file attachments in our bug report form with Zendesk integration. We'll explore two distinct approaches: direct attachment via the Zendesk API and indirect attachment using AWS S3.

## Current Implementation Status

Our current implementation includes:

1. A frontend React component (`BugReportForm.tsx`) that allows file selection and uploading
2. A backend API endpoint (`/api/zendesk/upload-attachment`) that forwards files to Zendesk
3. A ticket creation endpoint (`/api/zendesk/create-ticket`) with placeholder code for attachments

The current implementation uses the direct Zendesk API approach for uploading files, but there are both 500 errors and the ticket creation endpoint doesn't fully incorporate the attachment tokens yet.

## Approach 1: Direct File Upload to Zendesk API

### How It Works

1. User selects files in the frontend
2. Files are uploaded directly to Zendesk via our API proxy
3. Zendesk returns upload tokens for each file
4. When submitting the form, these tokens are included with the ticket creation request
5. Files are permanently linked to the created ticket

### Implementation Plan

1. **Fix the Upload Attachment Endpoint**:
   - Debug and fix the 500 errors occurring in the current implementation
   - Ensure proper error handling and logging

2. **Update the Ticket Creation Endpoint**:
   - Modify the `/api/zendesk/create-ticket/route.ts` file to include the upload tokens in the ticket creation:

   ```typescript
   // Inside the ticket creation body
   const ticketData = {
     ticket: {
       ...convertFormDataToTicket(formData).ticket,
       comment: {
         body: convertFormDataToTicket(formData).ticket.comment.body,
         uploads: uploadTokens // Add the upload tokens here
       }
     }
   };
   ```

3. **Add Proper Validation**:
   - Validate file types on the frontend before upload
   - Check file sizes against Zendesk's 50MB limit
   - Implement retry logic for failed uploads

### Pros
- Simple implementation with fewer moving parts
- Direct integration with Zendesk's API
- No additional storage costs beyond Zendesk's limits
- No need for additional AWS configuration

### Cons
- Files count against Zendesk storage limits
- No control over file lifecycle beyond Zendesk's policies
- Limited additional processing capabilities for files

## Approach 2: Indirect Upload via AWS S3

### How It Works

1. User selects files in the frontend
2. Files are first uploaded to AWS S3 temporary storage
3. After successful S3 upload, files are then sent to Zendesk from S3
4. Zendesk returns upload tokens for each file
5. When submitting the form, these tokens are included with the ticket creation request
6. Important files can be moved to permanent S3 storage for long-term retention

### Implementation Plan

1. **Create S3 Upload Endpoint**:
   - Implement a new `/api/s3/upload` endpoint for uploading files to S3
   - Configure proper CORS and security settings
   - Generate unique file paths with UUIDs to avoid collisions

   ```typescript
   // Rough implementation of S3 upload
   import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
   import { v4 as uuidv4 } from 'uuid';

   async function handleS3Upload(req: NextRequest) {
     const formData = await req.formData();
     const file = formData.get('file') as File;
     const filename = formData.get('filename') as string || file.name;

     const key = `temp/${uuidv4()}-${filename}`;
     const buffer = await file.arrayBuffer();

     const s3Client = new S3Client({
       region: zendeskConfig.awsRegion,
       credentials: {
         accessKeyId: zendeskConfig.awsAccessKeyId,
         secretAccessKey: zendeskConfig.awsSecretAccessKey
       }
     });

     await s3Client.send(new PutObjectCommand({
       Bucket: zendeskConfig.awsBucketName,
       Key: key,
       Body: buffer,
       ContentType: file.type || 'application/octet-stream'
     }));

     return { success: true, key, bucket: zendeskConfig.awsBucketName };
   }
   ```

2. **Implement Zendesk Upload from S3**:
   - Create a new `/api/zendesk/upload-from-s3` endpoint
   - This will take an S3 key and fetch the file from S3, then upload to Zendesk

   ```typescript
   async function handleUploadFromS3(req: NextRequest) {
     const { key, bucket } = await req.json();
     
     const s3Client = new S3Client({
       region: zendeskConfig.awsRegion,
       credentials: {
         accessKeyId: zendeskConfig.awsAccessKeyId,
         secretAccessKey: zendeskConfig.awsSecretAccessKey
       }
     });
     
     const command = new GetObjectCommand({
       Bucket: bucket,
       Key: key
     });
     
     const s3Response = await s3Client.send(command);
     const fileStream = s3Response.Body;
     const filename = key.split('/').pop();
     
     // Upload to Zendesk
     const zendeskUploadUrl = getZendeskApiUrl(`uploads?filename=${encodeURIComponent(filename)}`);
     
     const uploadResponse = await fetch(zendeskUploadUrl, {
       method: 'POST',
       headers: {
         'Authorization': getZendeskAuthHeader(),
         'Content-Type': s3Response.ContentType || 'application/octet-stream'
       },
       body: fileStream
     });
     
     // Process response similar to direct upload endpoint
     // ...
   }
   ```

3. **Update Frontend Component**:
   - Modify the uploadFileToZendesk function to first upload to S3, then to Zendesk:

   ```typescript
   const uploadFileToZendesk = async (fileId: string, file: File) => {
     try {
       // Upload to S3 first
       const formData = new FormData();
       formData.append('file', file);
       formData.append('filename', file.name);
       
       const s3Response = await fetch('/api/s3/upload', {
         method: 'POST',
         body: formData
       });
       
       if (!s3Response.ok) {
         throw new Error(`S3 upload failed: ${s3Response.status} ${s3Response.statusText}`);
       }
       
       const s3Result = await s3Response.json();
       
       // Now upload from S3 to Zendesk
       const zendeskResponse = await fetch('/api/zendesk/upload-from-s3', {
         method: 'POST',
         headers: {
           'Content-Type': 'application/json'
         },
         body: JSON.stringify({
           key: s3Result.key,
           bucket: s3Result.bucket
         })
       });
       
       // Process Zendesk response and store token as before
       // ...
     } catch (error) {
       console.error('Error uploading file:', error);
       setError(`File upload failed: ${error.message}`);
     }
   };
   ```

4. **Configure S3 Lifecycle Policy**:
   - Set up a lifecycle policy to delete temp files after 24 hours
   - Move important files to permanent storage for long-term retention

### Pros
- Better control over file lifecycle and storage costs
- Option to keep copies of files outside of Zendesk
- Ability to add additional processing like virus scanning, image optimization
- Can potentially reduce Zendesk storage usage costs

### Cons
- More complex implementation with multiple services
- Requires AWS S3 configuration and credentials
- Additional S3 storage costs
- More API requests and potential for additional failure points

## Recommendation

We recommend implementing **Approach 1 (Direct Zendesk API)** first, as it:

1. Is simpler to implement
2. Uses our existing code with minimal changes
3. Requires no additional services or credentials
4. Will work reliably with Zendesk's API

Once the direct approach is working, we can enhance it with the AWS S3 approach if:
- We need better control over file lifecycle
- We need to reduce Zendesk storage costs
- We want to implement additional file processing workflows

## Implementation Timeline

### Phase 1: Fix Direct Zendesk API Upload (1-2 days)
- Debug and fix the 500 errors in the upload-attachment endpoint
- Complete the ticket creation endpoint to properly handle attachments
- Add better error handling and retry logic

### Phase 2: Testing and Validation (1 day)
- Test with various file types and sizes
- Validate end-to-end functionality
- Fix any identified issues

### Phase 3 (Optional): S3 Integration (2-3 days)
- Implement S3 upload endpoints
- Set up temporary and permanent buckets
- Configure lifecycle policies
- Update frontend to use the new flow

## Conclusion

By implementing this plan, we'll have a robust file attachment system for our Zendesk bug report form. Starting with the direct API approach gets us to a working solution quickly, while leaving the door open for more sophisticated implementations in the future.

The most important next step is to fix the existing upload-attachment endpoint to ensure it properly uploads files to Zendesk and returns valid tokens for use in ticket creation.