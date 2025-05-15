import { NextRequest, NextResponse } from 'next/server';
import {
  zendeskConfig,
  isConfigValid,
  getZendeskApiUrl,
  getZendeskAuthHeader
} from '../config';
import { corsMiddleware } from '../../cors';

async function handleCreateTicket(request: NextRequest) {
  console.log('[DEBUG] Zendesk create-ticket endpoint called');
  try {
    // Check if Zendesk config is valid
    console.log('[DEBUG] Checking Zendesk config:', {
      subdomain: zendeskConfig.subdomain,
      email: zendeskConfig.email,
      hasApiToken: Boolean(zendeskConfig.apiToken),
    });
    
    if (!isConfigValid()) {
      console.log('[DEBUG] Zendesk configuration is incomplete');
      return NextResponse.json(
        { error: 'Zendesk configuration is incomplete' },
        { status: 500 }
      );
    }

    // Parse request body
    const requestData = await request.json();
    console.log('[DEBUG] Zendesk create-ticket request data:', JSON.stringify(requestData));
    const { formData, uploadTokens } = requestData;

    // Validate required form fields
    if (!formData) {
      console.log('[DEBUG] Missing formData in request');
      return NextResponse.json(
        { error: 'Missing formData in request' },
        { status: 400 }
      );
    }
    
    console.log('[DEBUG] Validating form fields:', {
      hasReporterName: Boolean(formData.reporterName),
      hasReporterEmail: Boolean(formData.reporterEmail),
      allFields: Object.keys(formData)
    });
    
    if (!formData.reporterName || !formData.reporterEmail) {
      return NextResponse.json(
        { error: 'Required form fields are missing' },
        { status: 400 }
      );
    }
    
    // Validate email format
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(formData.reporterEmail.trim())) {
      console.log('[DEBUG] Invalid email format:', formData.reporterEmail);
      return NextResponse.json(
        { error: 'Invalid email format. Please provide a valid email address.' },
        { status: 400 }
      );
    }

    // Convert form data to Zendesk ticket format
    console.log('[DEBUG] Converting form data to Zendesk ticket format');
    let ticketData = convertFormDataToTicket(formData);
    
    // Add upload tokens to the ticket if they exist
    if (uploadTokens && uploadTokens.length > 0) {
      console.log('[DEBUG] Adding file upload tokens to ticket:', uploadTokens);
      // Make sure the ticket has a comment object
      if (ticketData.ticket && ticketData.ticket.comment) {
        // Add the upload tokens to the comment
        ticketData.ticket.comment.uploads = uploadTokens;
      }
    }
    
    console.log('[DEBUG] Final ticket data:', JSON.stringify(ticketData));

    // Create the ticket
    const zendeskApiUrl = getZendeskApiUrl('tickets');
    console.log('[DEBUG] Creating ticket with Zendesk API URL:', zendeskApiUrl);
    
    const createTicketResponse = await fetch(zendeskApiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': getZendeskAuthHeader()
      },
      body: JSON.stringify(ticketData)
    });

    console.log('[DEBUG] Zendesk create ticket response:', {
      status: createTicketResponse.status,
      statusText: createTicketResponse.statusText,
      headers: Object.fromEntries([...createTicketResponse.headers.entries()])
    });
    
    if (!createTicketResponse.ok) {
      const errorText = await createTicketResponse.text();
      console.error('[DEBUG] Zendesk API error:', errorText);
      
      // Try to parse error response for better error message
      try {
        const errorJson = JSON.parse(errorText);
        console.error('[DEBUG] Parsed Zendesk API error:', JSON.stringify(errorJson, null, 2));
      } catch (e) {
        console.error('[DEBUG] Could not parse error response as JSON');
      }
      
      return NextResponse.json(
        { error: `Failed to create ticket: ${createTicketResponse.statusText}`, details: errorText },
        { status: createTicketResponse.status }
      );
    }

    const ticketResult = await createTicketResponse.json();
    console.log('[DEBUG] Zendesk ticket created successfully:', ticketResult);
    const ticketId = ticketResult.ticket?.id;

    // Log information about the uploaded files if any
    if (uploadTokens && uploadTokens.length > 0 && ticketId) {
      console.log(`[DEBUG] Successfully created ticket ${ticketId} with ${uploadTokens.length} file attachments`);
    }

    // Return success response with ticket ID
    return NextResponse.json({
      success: true,
      ticket_id: ticketId,
      message: 'Bug report successfully submitted to Zendesk'
    });
  } catch (error: any) {
    console.error('[DEBUG] Error creating Zendesk ticket:', error);
    console.error('[DEBUG] Error stack:', error.stack);
    return NextResponse.json(
      { error: `Internal server error: ${error.message}` },
      { status: 500 }
    );
  }
}

// Helper to convert the bug report form data to a Zendesk ticket format
function convertFormDataToTicket(formData: any) {
  // Build description from the bug report details
  const description = `
## Bug Report Details

### Reporter Information
Name: ${formData.reporterName}
Email: ${formData.reporterEmail}

### Device Information
App Version: ${formData.appVersion}
Device/OS: ${formData.deviceOS}

### Bug Description
Steps to Reproduce:
${formData.stepsToReproduce}

Expected Result:
${formData.expectedResult}

Actual Result:
${formData.actualResult}

GDPR Consent: ${formData.gdprConsent ? 'Provided' : 'Not provided'}
`;

  // Create the ticket object
  return {
    ticket: {
      subject: `Bug Report: ${formData.deviceOS} - ${formData.appVersion}`,
      comment: {
        body: description,
        // If there are attachments, they will be added separately
      },
      priority: zendeskConfig.defaultPriority,
      type: zendeskConfig.defaultType,
      source: zendeskConfig.defaultSource,
      // Add tags to categorize the ticket
      tags: ["ss8beta", "bug-report"],
      // Add group ID if configured
      ...(zendeskConfig.groupId && { group_id: parseInt(zendeskConfig.groupId) }),
      // Add reporter as the requester with trimmed email
      requester: {
        name: formData.reporterName.trim(),
        email: formData.reporterEmail.trim()
      },
      // Custom fields could be added here
      custom_fields: [
        // Example custom field, uncomment and customize as needed
        // { id: 123456, value: formData.customValue }
      ]
    }
  };
}

// Map severity from the form to Zendesk priority
function mapSeverityToPriority(severity: string): string {
  switch (severity.toLowerCase()) {
    case 'high':
      return 'high';
    case 'low':
      return 'low';
    default:
      return zendeskConfig.defaultPriority;
  }
}

// Apply CORS middleware to the handler
export const POST = corsMiddleware(handleCreateTicket);

// Also handle OPTIONS requests for CORS preflight
export const OPTIONS = corsMiddleware((req) => Promise.resolve(new NextResponse(null, { status: 204 })));