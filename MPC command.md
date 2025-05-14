# MCP Command Reference

This document maintains an ongoing list of all Model Context Protocol (MCP) commands that can be used to activate various services directly from this interface.

## Available MCP Services

### 1. Brave Search

Brave Search allows you to search the web directly from the interface.

**Commands:**
- `/brave-search <query>` - Performs a general web search
- `/brave-search <url>` - Searches for information about a specific URL
- `/brave-local-search <query>` - Searches for local businesses and places

**Examples:**
- `/brave-search python tutorial`
- `/brave-search https://example.com`
- `/brave-local-search coffee shops near me`

### 2. Task Master AI

Task Master is an AI-powered task management system for development projects.

**Commands:**
- `/task-master-ai` - Activates the Task Master AI context server

**Common Task Master Commands:**
- `task-master list` - Lists all tasks with IDs, titles, and status
- `task-master next` - Shows the next task to work on
- `task-master show <id>` - Views details of a specific task
- `task-master expand --id=<id>` - Breaks down a task into subtasks
- `task-master analyze-complexity --research` - Analyzes task complexity with research
- `task-master parse-prd --input=<file>` - Generates tasks from a PRD document
- `task-master set-status --id=<id> --status=<status>` - Updates task status
- `task-master add-dependency --id=<id> --depends-on=<id>` - Adds a dependency
- `task-master remove-dependency --id=<id> --depends-on=<id>` - Removes a dependency

## Adding New MCP Services

As new MCP services become available, they will be added to this document with their activation commands and usage examples.