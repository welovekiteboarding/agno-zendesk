# Zendesk Integration for Bug Report Form

This documentation describes how the Zendesk integration has been implemented for the bug report form.

## Overview

The integration allows users to submit bug reports directly from our application to Zendesk's ticketing system. It includes:

1. A React component for the bug report form (`BugReportForm.tsx`)
2. API endpoints for creating tickets and handling file uploads
3. Configuration settings via environment variables
4. File attachment functionality

## Components

### Frontend

- **Bug Report Form React Component**  
  Path: `/components/features/BugReportForm.tsx`
  - Implements a form for collecting bug report details
  - Includes file drag & drop upload capability
  - Connects to Zendesk API endpoints for ticket creation

- **Bug Report Page**  
  Path: `/app/bug-report/page.js`
  - Displays the bug report form in a styled container
  - Accessible via navigation links from the main app

### Backend API Endpoints

- **Create Ticket**  
  Path: `/app/api/zendesk/create-ticket/route.ts`
  - Creates a new ticket in Zendesk using the form data
  - Converts form fields to Zendesk ticket format
  - Handles attachment tokens for file uploads

- **Upload Attachment**  
  Path: `/app/api/zendesk/upload-attachment/route.ts`
  - Handles file uploads to Zendesk
  - Returns tokens that can be used when creating tickets

- **Configuration**  
  Path: `/app/api/zendesk/config.ts`
  - Contains settings for connecting to Zendesk API
  - Provides helper functions for authentication and API URLs

## Configuration

The following environment variables are required:

```
ZENDESK_SUBDOMAIN=your-zendesk-subdomain
ZENDESK_API_TOKEN=your-api-token
ZENDESK_EMAIL=your-email@example.com
```

Optional configuration:
```
ZENDESK_DEFAULT_PRIORITY=normal
ZENDESK_DEFAULT_TYPE=problem
ZENDESK_DEFAULT_SOURCE=web
ZENDESK_GROUP_ID=optional-group-id
```

## File Upload Process

The file upload process follows these steps:

1. User selects or drags files into the upload zone
2. Files are validated for size limits (max 50MB per file, 3 files total)
3. Each file is uploaded to Zendesk via the `/api/zendesk/upload-attachment` endpoint
4. Zendesk returns a token for each uploaded file
5. When the form is submitted, these tokens are included with the ticket creation request
6. Files are permanently attached to the created ticket

## Styling

The bug report form uses Tailwind CSS for styling with a dark theme that matches the rest of the application:
- Dark background (`#0b1021`, `#121833`)
- Purple accent colors (`#6d4aff`, `#8c5eff`) for buttons and highlights
- Rounded corners and subtle shadows for depth
- Clear visual feedback for form state (success, error, loading)

## User Flow

1. User clicks on "Bug Report Form" link from the main app
2. User fills out the bug report form and optionally attaches files
3. On submission, the form data and file tokens are sent to Zendesk
4. User receives confirmation with the Zendesk ticket ID
5. Zendesk handles the ticket according to configured workflows

## Static HTML Alternative

There is also a static HTML version of the bug report form available at:
- `/public/zendesk-bug-report.html`

This provides the same functionality using vanilla HTML, CSS, and JavaScript for environments where the React component cannot be used.