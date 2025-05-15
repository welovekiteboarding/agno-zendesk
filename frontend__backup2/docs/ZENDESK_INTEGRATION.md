# Zendesk Integration for Bug Report Form

This document explains how to configure and use the Zendesk integration for the static Bug Report Form.

## Overview

The Zendesk integration allows users to submit bug reports directly from the Bug Report Form to your Zendesk support system. When a user submits a bug report, the system will:

1. Create a ticket in Zendesk with all the bug report details
2. Upload any attachments to the Zendesk ticket
3. Show a confirmation page with the Zendesk ticket ID
4. Handle errors gracefully with fallback options

## Configuration

### Environment Variables

To use the Zendesk integration, you need to set the following environment variables:

1. Copy the `.env.example` file to `.env.local`:

```bash
cp .env.example .env.local
```

2. Edit the `.env.local` file with your specific Zendesk and storage credentials:

```
# Zendesk Configuration
ZENDESK_SUBDOMAIN=your-subdomain  # e.g., "yourcompany" from "yourcompany.zendesk.com"
ZENDESK_API_TOKEN=your-api-token  # API token generated in Zendesk Admin
ZENDESK_EMAIL=agent@example.com   # Email of the Zendesk agent account associated with the API token

# Optional Zendesk Settings
ZENDESK_DEFAULT_PRIORITY=normal   # Default ticket priority (urgent, high, normal, low)
ZENDESK_DEFAULT_TYPE=problem      # Default ticket type (problem, incident, question, task)
ZENDESK_DEFAULT_SOURCE=web        # Default ticket source
ZENDESK_GROUP_ID=123456           # Group ID for ticket assignment (optional)

# S3/R2 Configuration for Attachments (already in your environment)
R2_BUCKET_NAME=your-bucket        # S3/R2 bucket name
R2_ACCESS_KEY=your-access-key     # S3/R2 access key 
R2_SECRET_KEY=your-secret-key     # S3/R2 secret key
R2_ENDPOINT=https://example.com   # S3/R2 endpoint URL
```

3. For production deployment, set these environment variables in your hosting platform (Vercel, Netlify, etc.).

### Setting Up Zendesk API Token

To generate a Zendesk API token:

1. Log in to your Zendesk account as an admin
2. Go to Admin > API > Tokens
3. Click "Add API Token"
4. Enter a description (e.g., "Bug Report Form Integration")
5. Copy the generated token and add it to your `.env.local` file

### Enabling/Disabling Zendesk Integration

To enable or disable the Zendesk integration, modify the `USE_ZENDESK` constant in the bug-report.html file:

```javascript
// Set to true to enable Zendesk integration, false to use the original Form Collector integration
const USE_ZENDESK = true; 
```

## How It Works

### Ticket Creation

When a user submits a bug report:

1. The form data is sent to the `/api/zendesk/create-ticket` API endpoint
2. The backend creates a ticket in Zendesk with all the bug details formatted appropriately
3. If attachments are included, they are uploaded to Zendesk and linked to the ticket
4. The user sees a confirmation page with the Zendesk ticket ID and details

### Error Handling

The integration includes robust error handling:

1. If Zendesk is unavailable or returns an error, users are shown a detailed error message
2. Users have the option to retry or use the alternative submission method (original Form Collector)
3. If attachment uploads fail but the ticket is created, a warning is displayed to the user
4. All errors are logged to the console for debugging

## Customization

### Ticket Fields

To customize the Zendesk ticket fields, modify the `convertFormDataToTicket` function in `/app/api/zendesk/create-ticket/route.ts`:

```typescript
// Add custom fields to the ticket
custom_fields: [
  { id: 123456, value: formData.customValue }
]
```

### Confirmation UI

To customize the confirmation UI, modify the success message HTML in the `submitToZendesk` function in `bug-report.html`.

## File Attachments

The file attachment process works as follows:

1. Users select files through the bug report form's file upload interface
2. Files are scanned for viruses using the R2/S3 temporary and permanent storage system
3. When submitting to Zendesk:
   - Each file is uploaded directly to Zendesk (bypassing S3/R2 if desired)
   - Upload tokens are collected for each successful file upload
   - All upload tokens are attached to the Zendesk ticket in a single operation

This allows users to attach screenshots, logs, and other relevant files to their bug reports.

## Security Considerations

- The Zendesk API token and credentials are only stored on the server side
- All Zendesk API requests are proxied through the backend to avoid exposing credentials
- HTTPS is enforced for all API communication
- The API endpoints validate input data before processing

## Troubleshooting

If you encounter issues with the Zendesk integration:

1. Check the browser console for detailed error messages
2. Verify that all environment variables are correctly set
3. Ensure that your Zendesk API token has sufficient permissions
4. Check if the R2/S3 bucket is accessible and properly configured
5. Test the API endpoints directly using a tool like Postman

### Common Issues

#### File Uploads Failing

If file uploads are failing:

1. Check that your Zendesk account has file attachments enabled
2. Verify the file size limits in Zendesk (typically 50MB per file)
3. Check that the content types are supported by Zendesk
4. Look for CORS issues in the browser console

#### Environment Variables Not Working

If your environment variables aren't being recognized:

1. Make sure your `.env.local` file is in the root directory
2. Restart your development server after changing environment variables
3. In production, verify that the environment variables are set in your hosting platform

For persistent issues, disable the Zendesk integration by setting `USE_ZENDESK = false` and use the original Form Collector integration while troubleshooting.