import { NextRequest, NextResponse } from 'next/server';
import { zendeskConfig, getZendeskApiUrl, getZendeskAuthHeader, isConfigValid } from '../../config';
import { corsMiddleware } from '../../../cors';

// Handler for attaching uploads to a ticket
async function handleAttachUploads(request: NextRequest) {
  console.log('[DEBUG] Zendesk attach-uploads endpoint called');
  try {
    // Check if Zendesk config is valid
    if (!isConfigValid()) {
      console.log('[DEBUG] Zendesk configuration is incomplete');
      return NextResponse.json(
        { error: 'Zendesk configuration is incomplete' },
        { status: 500 }
      );
    }

    // Parse request body
    const requestData = await request.json();
    console.log('[DEBUG] attach-uploads request:', JSON.stringify(requestData));
    const { ticketId, uploadTokens } = requestData;

    // Validate required fields
    if (!ticketId || !uploadTokens || !Array.isArray(uploadTokens) || uploadTokens.length === 0) {
      console.log('[DEBUG] Missing required fields in attach-uploads request');
      return NextResponse.json(
        { error: 'Missing required fields: ticketId and uploadTokens array' },
        { status: 400 }
      );
    }

    // Create the comment data with attachments
    const commentData = {
      ticket: {
        comment: {
          body: 'Attachments for this bug report',
          uploads: uploadTokens
        }
      }
    };

    console.log('[DEBUG] Adding comment with attachments to ticket:', ticketId);
    console.log('[DEBUG] Comment data:', JSON.stringify(commentData));

    // Add comment with attachments to the ticket
    const zendeskApiUrl = getZendeskApiUrl(`tickets/${ticketId}`);
    console.log('[DEBUG] Making request to Zendesk API URL:', zendeskApiUrl);
    
    const response = await fetch(zendeskApiUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': getZendeskAuthHeader()
      },
      body: JSON.stringify(commentData)
    });

    console.log('[DEBUG] Zendesk attach response:', {
      status: response.status,
      statusText: response.statusText
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[DEBUG] Zendesk ticket update error:', errorText);
      return NextResponse.json(
        { error: `Failed to add attachments to ticket: ${response.statusText}` },
        { status: response.status }
      );
    }

    const result = await response.json();
    console.log('[DEBUG] Attachments added successfully:', result);
    
    // Return success response
    return NextResponse.json({
      success: true,
      message: `Successfully added ${uploadTokens.length} attachments to ticket ${ticketId}`
    });
  } catch (error: any) {
    console.error('[DEBUG] Error attaching files to ticket:', error);
    console.error('[DEBUG] Error stack:', error.stack);
    return NextResponse.json(
      { error: `Failed to attach files to ticket: ${error.message}` },
      { status: 500 }
    );
  }
}

// Apply CORS middleware to the handler
export const POST = corsMiddleware(handleAttachUploads);

// Also handle OPTIONS requests for CORS preflight
export const OPTIONS = corsMiddleware((req) => Promise.resolve(new NextResponse(null, { status: 204 })));