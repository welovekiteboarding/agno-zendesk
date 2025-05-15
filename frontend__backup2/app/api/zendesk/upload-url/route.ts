import { NextRequest, NextResponse } from 'next/server';
import { zendeskConfig, getZendeskApiUrl, getZendeskAuthHeader, isConfigValid } from '../config';
import { corsMiddleware } from '../../cors';

// Handler for processing upload URL requests
async function handleUploadUrl(request: NextRequest) {
  console.log('[DEBUG] Zendesk upload-url endpoint called');
  try {
    // Check if Zendesk config is valid
    if (!isConfigValid()) {
      return NextResponse.json(
        { error: 'Zendesk configuration is incomplete' },
        { status: 500 }
      );
    }

    // Parse request body
    const requestBody = await request.json();
    const { fileName, contentType, size } = requestBody;
    console.log('[DEBUG] upload-url request:', JSON.stringify(requestBody));

    // Validate required fields
    if (!fileName) {
      console.log('[DEBUG] Error: Missing fileName in upload-url request');
      return NextResponse.json(
        { error: 'Missing required field: fileName' },
        { status: 400 }
      );
    }

    // Generate a Zendesk upload token
    const zendeskUploadUrl = getZendeskApiUrl(`uploads?filename=${encodeURIComponent(fileName)}`);
    console.log('[DEBUG] Making request to Zendesk upload URL:', zendeskUploadUrl);
    
    const response = await fetch(zendeskUploadUrl, {
      method: 'POST',
      headers: {
        'Authorization': getZendeskAuthHeader(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        content_type: contentType || 'application/octet-stream',
        size: size || 0
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[DEBUG] Zendesk upload URL generation error - Status:', response.status);
      console.error('[DEBUG] Zendesk upload URL generation error - Response:', errorText);
      return NextResponse.json(
        { error: `Failed to generate upload URL: ${response.statusText}` },
        { status: response.status }
      );
    }

    const result = await response.json();
    console.log('[DEBUG] Zendesk upload token generated successfully:', JSON.stringify(result));
    
    // Return the upload token and attachment details
    return NextResponse.json({
      upload: {
        token: result.upload?.token,
        attachment_id: result.upload?.attachment?.id,
        attachment: result.upload?.attachment
      }
    });
  } catch (error: any) {
    console.error('[DEBUG] Error generating Zendesk upload URL:', error);
    console.error('[DEBUG] Error stack:', error.stack);
    return NextResponse.json(
      { error: `Failed to generate upload URL: ${error.message}` },
      { status: 500 }
    );
  }
}

// Apply CORS middleware to the handler
export const POST = corsMiddleware(handleUploadUrl);

// Also handle OPTIONS requests for CORS preflight
export const OPTIONS = corsMiddleware((req) => Promise.resolve(new NextResponse(null, { status: 204 })));