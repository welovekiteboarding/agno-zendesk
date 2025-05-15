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
    
    if (!file) {
      console.log('[DEBUG] No file found in request');
      return NextResponse.json(
        { error: 'No file found in request' },
        { status: 400 }
      );
    }

    const filename = formData.get('filename') as string || file.name;
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
    console.log('[DEBUG] Using auth header starting with:', authHeader.substring(0, 15) + '***');

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
      console.log('[DEBUG] Zendesk raw response (truncated):', 
        responseText.length > 200 ? responseText.substring(0, 200) + '...' : responseText);
      
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