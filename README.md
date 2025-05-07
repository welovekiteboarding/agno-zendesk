# AGNO Bug-Report LLM System

This project implements an LLM-powered bug report workflow integrated with Zendesk, using the Agno agent framework. Users interact with a chat-based form that collects all required bug report fields, validates them, and uploads attachments. The system verifies/creates the reporter in Zendesk, creates a ticket with all metadata and files, and provides confirmation to the user.

## Features

- LLM-driven chat form for bug report collection
- Strict field validation and follow-up for missing/invalid data
- Zendesk user verification and ticket creation
- File upload via presigned S3/R2 URLs
- Modular agent pipeline (Form-Collector, Email-Verifier, Attachment-Uploader, Ticket-Poster)
- Success/failure logging and analytics

## Directory Structure

```
/agents         # AGNO agent definitions
/api            # API routes and integrations
/components     # UI components
/config         # Configuration files
/utils          # Utility functions
/types          # TypeScript type definitions
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/welovekiteboarding/agno-zendesk.git
cd agno-zendesk
```

### 2. Install dependencies

```bash
npm install
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and fill in the required values:

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 4. Run the development server

```bash
npm run dev
```

### 5. Run tests

```bash
npm test
```

## Environment Variables

See `.env.example` for all required configuration.

## Contributing

Contributions are welcome! Please open issues or pull requests.

## License

MIT
