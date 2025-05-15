# Fixing Zendesk Direct Upload Implementation

This document outlines the specific changes needed to fix the current 500 errors in the Zendesk file upload implementation.

## Current Issues

The Zendesk file upload is currently failing with 500 errors. The most likely causes are:

1. Issues with the content type or format of the uploaded file
2. Problems with the Zendesk API credentials or authentication
3. Network or CORS issues when making requests to Zendesk
4. Problems processing the response from Zendesk

## Step 1: Fix Upload Attachment Endpoint

First, let's modify the `/api/zendesk/upload-attachment/route.ts` file to add more robust error handling and logging:

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { zendeskConfig, getZendeskApiUrl, getZendeskAuthHeader, isConfigValid } from '../config';
import { corsMiddleware } from '../../cors';

/**
 * Handler for uploading files to Zendesk
 * Uses multipart/form-data to stream files directly to Zendesk
 */
async function handleUploadAttachment(request: NextRequest) {
  console.log('[DEBUG] Zendesk upload-attachment endpoint called');
  try {
    // Check if Zendesk config is valid
    if (!isConfigValid()) {
      console.log('[DEBUG] Zendesk configuration is incomplete');
      console.log('[DEBUG] Config:', {
        hasSubdomain: Boolean(zendeskConfig.subdomain),
        hasApiToken: Boolean(zendeskConfig.apiToken),
        hasEmail: Boolean(zendeskConfig.email),
        subdomain: zendeskConfig.subdomain,
        email: zendeskConfig.email?.substring(0, 3) + '***'
      });
      return NextResponse.json(
        { error: 'Zendesk configuration is incomplete' },
        { status: 500 }
      );
    }

    // Get file from form data
    const formData = await request.formData();
    const file = formData.get('file') as File;
    const filename = formData.get('filename') as string || file.name;

    if (!file) {
      console.log('[DEBUG] No file found in request');
      return NextResponse.json(
        { error: 'No file found in request' },
        { status: 400 }
      );
    }

    console.log(`[DEBUG] Processing file upload: ${filename}, size: ${file.size}, type: ${file.type}`);

    // Convert File to ArrayBuffer and ensure we have a buffer
    const buffer = await file.arrayBuffer();
    if (!buffer || buffer.byteLength === 0) {
      console.log('[DEBUG] Empty file buffer');
      return NextResponse.json(
        { error: 'Empty file buffer' },
        { status: 400 }
      );
    }

    // Make sure we have a content type
    const contentType = file.type || 'application/octet-stream';
    console.log(`[DEBUG] Using content type: ${contentType}`);

    // Upload to Zendesk
    const zendeskUploadUrl = getZendeskApiUrl(`uploads?filename=${encodeURIComponent(filename)}`);
    console.log('[DEBUG] Uploading to Zendesk URL:', zendeskUploadUrl);

    // Log the authorization header (masked for security)
    const authHeader = getZendeskAuthHeader();
    console.log('[DEBUG] Auth header:', authHeader.substring(0, 15) + '***');

    try {
      const uploadResponse = await fetch(zendeskUploadUrl, {
        method: 'POST',
        headers: {
          'Authorization': authHeader,
          'Content-Type': contentType
        },
        body: buffer
      });

      console.log('[DEBUG] Zendesk response status:', uploadResponse.status);
      console.log('[DEBUG] Zendesk response headers:', Object.fromEntries([...uploadResponse.headers.entries()]));

      if (!uploadResponse.ok) {
        const errorText = await uploadResponse.text();
        console.error('[DEBUG] Zendesk upload error text:', errorText);
        return NextResponse.json(
          { error: `Failed to upload file to Zendesk: ${uploadResponse.statusText}. ${errorText}` },
          { status: uploadResponse.status }
        );
      }

      // Parse the response
      const responseText = await uploadResponse.text();
      console.log('[DEBUG] Zendesk raw response:', responseText);
      
      let result;
      try {
        result = JSON.parse(responseText);
      } catch (parseError) {
        console.error('[DEBUG] Error parsing Zendesk response:', parseError);
        return NextResponse.json(
          { error: 'Invalid response from Zendesk' },
          { status: 500 }
        );
      }

      console.log('[DEBUG] Zendesk upload successful, token:', result.upload?.token);

      // Return the token
      return NextResponse.json({
        success: true,
        token: result.upload?.token,
        attachment: result.upload?.attachment
      });
    } catch (fetchError: any) {
      console.error('[DEBUG] Fetch error during Zendesk upload:', fetchError);
      return NextResponse.json(
        { error: `Network error uploading to Zendesk: ${fetchError.message}` },
        { status: 500 }
      );
    }
  } catch (error: any) {
    console.error('[DEBUG] Error uploading file to Zendesk:', error);
    console.error('[DEBUG] Error stack:', error.stack);
    return NextResponse.json(
      { error: `Failed to upload file: ${error.message}` },
      { status: 500 }
    );
  }
}

// Apply CORS middleware to the handler
export const POST = corsMiddleware(handleUploadAttachment);

// Also handle OPTIONS requests for CORS preflight
export const OPTIONS = corsMiddleware((req) => Promise.resolve(new NextResponse(null, { status: 204 })));
```

## Step 2: Update Create Ticket Endpoint

Now, let's modify the `/api/zendesk/create-ticket/route.ts` file to properly handle the upload tokens:

```typescript
// Inside the handleCreateTicket function, after parsing the request body

// Parse request body
const requestData = await request.json();
console.log('[DEBUG] Zendesk create-ticket request data:', JSON.stringify(requestData));
const { formData, uploadTokens } = requestData;  // Extract uploadTokens

// ... [existing validation code]

// Convert form data to Zendesk ticket format
console.log('[DEBUG] Converting form data to Zendesk ticket format');
const ticketData = {
  ...convertFormDataToTicket(formData),  // Use existing ticket data
};

// Add uploads if we have tokens
if (uploadTokens && uploadTokens.length > 0) {
  console.log('[DEBUG] Adding file attachments to ticket:', uploadTokens);
  // Make sure the ticket object exists
  if (!ticketData.ticket) {
    ticketData.ticket = {};
  }
  
  // Make sure the comment object exists
  if (!ticketData.ticket.comment) {
    ticketData.ticket.comment = { body: '' };
  }
  
  // Add the upload tokens to the comment
  ticketData.ticket.comment.uploads = uploadTokens;
}

console.log('[DEBUG] Final ticket data:', JSON.stringify(ticketData));

// Create the ticket
const zendeskApiUrl = getZendeskApiUrl('tickets');
console.log('[DEBUG] Creating ticket with Zendesk API URL:', zendeskApiUrl);
```

## Step 3: Frontend Changes

We don't need many changes to the frontend component as it's already correctly sending the file and handling the token. However, we can add some better error handling:

```typescript
// In BugReportForm.tsx, update the uploadFileToZendesk function

const uploadFileToZendesk = async (fileId: string, file: File) => {
  try {
    // Update UI to show uploading state
    setFiles(prevFiles => {
      return prevFiles.map(f => {
        if (f.id === fileId) {
          return { ...f, uploading: true, error: null };
        }
        return f;
      });
    });
    
    // Create form data for file upload
    const formData = new FormData();
    formData.append('file', file);
    formData.append('filename', file.name);
    
    // Upload to Zendesk API proxy
    const response = await fetch('/api/zendesk/upload-attachment', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      let errorMessage = `Upload failed: ${response.status} ${response.statusText}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.error || errorMessage;
      } catch (e) {
        // Ignore parse errors, use default message
      }
      
      throw new Error(errorMessage);
    }
    
    const result = await response.json();
    
    if (!result.token) {
      throw new Error('No upload token received from server');
    }
    
    // Store the token
    setFiles(prevFiles => {
      return prevFiles.map(f => {
        if (f.id === fileId) {
          return { 
            ...f, 
            token: result.token,
            uploading: false,
            error: null 
          };
        }
        return f;
      });
    });
    
  } catch (error: any) {
    console.error('Error uploading file:', error);
    
    // Update UI to show error
    setFiles(prevFiles => {
      return prevFiles.map(f => {
        if (f.id === fileId) {
          return { 
            ...f, 
            uploading: false,
            error: error.message || 'Unknown error' 
          };
        }
        return f;
      });
    });
    
    setError(`File upload failed: ${error.message}`);
  }
};
```

## Step 4: Manual Testing Process

After implementing these changes, test the attachment functionality with the following steps:

1. Start the development server: `npm run dev`
2. Open the bug report form
3. Fill in all required fields
4. Add files using drag-and-drop or the file selector
5. Verify that files upload successfully and show the checkmark
6. Submit the form
7. Check that the submission succeeds and shows a success message with ticket ID
8. Verify in Zendesk that the ticket was created with attachments

## Debugging Approach

If issues persist after these changes:

1. Check the server logs for detailed error messages
2. Verify Zendesk API credentials in the `.env.local` file
3. Test the Zendesk API directly using a tool like Postman
4. Examine network requests in the browser's developer tools
5. Try uploading with smaller files or different file types to isolate any type-specific issues

## Security Considerations

- Ensure Zendesk API credentials are properly secured in environment variables
- Validate file types and sizes on both frontend and backend
- Consider adding virus scanning if needed
- Make sure error messages don't expose sensitive information

By implementing these changes, we should be able to fix the current 500 errors and get the file attachment functionality working with the Zendesk API.