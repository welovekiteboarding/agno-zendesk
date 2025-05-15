import { NextRequest, NextResponse } from 'next/server';
import { getZendeskApiUrl, getZendeskAuthHeader, isConfigValid } from '../config';

// Function to upload an attachment to Zendesk
async function uploadAttachmentToZendesk(fileUrl: string, fileName: string, contentType: string) {
  try {
    // First, download the file from S3/R2
    const fileResponse = await fetch(fileUrl);
    if (!fileResponse.ok) {
      throw new Error(`Failed to fetch file from storage: ${fileResponse.statusText}`);
    }

    // Get the file content as blob
    const fileBlob = await fileResponse.blob();

    // Create a FormData object for the Zendesk API
    const formData = new FormData();
    formData.append('filename', fileName);
    formData.append('file', fileBlob, fileName);

    // Upload to Zendesk API
    const uploadResponse = await fetch(getZendeskApiUrl('uploads?filename=' + encodeURIComponent(fileName)), {
      method: 'POST',
      headers: {
        'Authorization': getZendeskAuthHeader(),
        'Content-Type': 'application/binary'
      },
      body: fileBlob
    });

    if (!uploadResponse.ok) {
      const errorText = await uploadResponse.text();
      console.error('Zendesk upload error:', errorText);
      throw new Error(`Zendesk upload failed: ${uploadResponse.statusText}`);
    }

    // Return the upload result with the token
    const uploadResult = await uploadResponse.json();
    return uploadResult.upload?.token;
  } catch (error: any) {
    console.error('Error uploading attachment to Zendesk:', error);
    throw error;
  }
}

// Function to add attachments to an existing ticket
async function addAttachmentsToTicket(ticketId: string, uploadTokens: string[]) {
  try {
    // Create the comment data with attachments
    const commentData = {
      ticket: {
        comment: {
          body: 'Attachments for this bug report',
          uploads: uploadTokens
        }
      }
    };

    // Add comment with attachments to the ticket
    const updateResponse = await fetch(getZendeskApiUrl(`tickets/${ticketId}`), {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': getZendeskAuthHeader()
      },
      body: JSON.stringify(commentData)
    });

    if (!updateResponse.ok) {
      const errorText = await updateResponse.text();
      console.error('Zendesk ticket update error:', errorText);
      throw new Error(`Failed to add attachments to ticket: ${updateResponse.statusText}`);
    }

    return await updateResponse.json();
  } catch (error: any) {
    console.error('Error adding attachments to ticket:', error);
    throw error;
  }
}

export async function POST(request: NextRequest) {
  try {
    // Check if Zendesk config is valid
    if (!isConfigValid()) {
      return NextResponse.json(
        { error: 'Zendesk configuration is incomplete' },
        { status: 500 }
      );
    }

    // Parse request body
    const requestData = await request.json();
    const { ticketId, attachments } = requestData;

    // Validate required fields
    if (!ticketId || !attachments || !Array.isArray(attachments) || attachments.length === 0) {
      return NextResponse.json(
        { error: 'Missing required fields: ticketId and attachments array' },
        { status: 400 }
      );
    }

    // Upload each attachment to Zendesk
    const uploadTokens = [];
    for (const attachment of attachments) {
      // Skip if it's the 'skipped-attachments' placeholder
      if (attachment.key === 'skipped-attachments') {
        continue;
      }

      // Extract file information
      const { fileUrl, fileName, contentType } = attachment;

      // Upload to Zendesk and get the token
      const token = await uploadAttachmentToZendesk(fileUrl, fileName, contentType);
      if (token) {
        uploadTokens.push(token);
      }
    }

    // If we have upload tokens, add them to the ticket
    let result = { success: true, message: 'No attachments to upload' };
    if (uploadTokens.length > 0) {
      await addAttachmentsToTicket(ticketId, uploadTokens);
      result = {
        success: true,
        message: `Successfully added ${uploadTokens.length} attachments to ticket ${ticketId}`
      };
    }

    // Return success response
    return NextResponse.json(result);
  } catch (error: any) {
    console.error('Error processing attachments:', error);
    return NextResponse.json(
      { error: `Failed to process attachments: ${error.message}` },
      { status: 500 }
    );
  }
}