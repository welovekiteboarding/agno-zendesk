# HOW TO USE TASK MASTER MCP IN WINDSURF

This document provides a complete guide to using the Task Master MCP (Management Command Protocol) integration in Windsurf. Everything you need to know is documented here - no need to search online again.

## Table of Contents

1. [Setup and Requirements](#setup-and-requirements)
2. [Core Commands Reference](#core-commands-reference)
3. [Complete Workflow Guide](#complete-workflow-guide)
4. [Specific Use Cases](#specific-use-cases)
5. [Troubleshooting](#troubleshooting)

---

## Setup and Requirements

### Prerequisites

- Windsurf with MCP integration enabled
- Task Master MCP module loaded (you'll see it in the MCP panel with "taskmaster-ai" listing)

### First-Time Setup

If running Task Master for the first time in a project:

```bash
# Initialize Task Master in your project
task-master initialize-project --projectRoot="$(pwd)"

# Check if initialization was successful
ls -la tasks/ # Should see a tasks directory created
```

### Environment Variables

Task Master requires certain environment variables to run properly:

- `ANTHROPIC_API_KEY`: Required for AI task generation (Claude)
- `MODEL`: Optional, defaults to claude-3-7-sonnet
- `MAX_TOKENS`: Optional, defaults to 4000
- `TEMPERATURE`: Optional, defaults to 0.7
- `PERPLEXITY_API_KEY`: Optional, for research capabilities
- `PROJECT_NAME`: Optional, default is "Task Master"

Set these by adding them to your project's environment setup.

---

## Core Commands Reference

### Getting Help

Always available to check command options:

```bash
# Get general help with all commands
task-master help

# Get help for a specific command
task-master help parse-prd
task-master help add-task
```

### Creating Tasks from a PRD

```bash
# Basic usage - WILL OVERWRITE existing tasks
task-master parse-prd --input=scripts/prd.txt

# Specify number of tasks to generate
task-master parse-prd --input=scripts/prd.txt --tasks=15
```

### Adding Tasks Without Overwriting

```bash
# Add a single task
task-master add-task --prompt="Implement feature X" --priority="medium"

# Add a task with dependencies
task-master add-task --prompt="Implement feature X" --dependencies="1,2,3" --priority="high"
```

### Listing and Managing Tasks

```bash
# List all tasks
task-master list

# List tasks with a specific status
task-master list --status=pending
task-master list --status=done

# Show detailed info for a task
task-master show 5

# Update task status
task-master set-status --id=5 --status=in-progress
task-master set-status --id=5 --status=done
```

### Managing Dependencies

```bash
# Add a dependency
task-master add-dependency --id=5 --dependsOn=3

# Remove a dependency
task-master remove-dependency --id=5 --dependsOn=3

# Fix dependency issues
task-master fix-dependencies
```

### Working with Subtasks

```bash
# Expand a task into subtasks
task-master expand --id=5

# Expand with more subtasks
task-master expand --id=5 --num=7

# Clear subtasks
task-master clear-subtasks --id=5
```

### Task Analysis

```bash
# Analyze task complexity
task-master analyze-complexity

# View complexity report
task-master complexity-report
```

### Updating Tasks

```bash
# Update a single task
task-master update-task --id=5 --prompt="New information about task 5"

# Update multiple tasks
task-master update --from=5 --prompt="New context for all tasks from #5 onward"
```

---

## Complete Workflow Guide

### Initial Project Setup

1. Initialize Task Master:

   ```bash
   task-master initialize-project --projectRoot="$(pwd)"
   ```

2. Create a PRD in `scripts/prd.txt` with your product requirements

3. Generate initial tasks:

   ```bash
   task-master parse-prd --input=scripts/prd.txt
   ```

4. Generate individual task files:
   ```bash
   task-master generate
   ```

### Working on Tasks

1. Find the next task to work on:

   ```bash
   task-master next
   ```

2. Mark the task as in-progress:

   ```bash
   task-master set-status --id=<task_id> --status=in-progress
   ```

3. For complex tasks, break them down:

   ```bash
   task-master expand --id=<task_id> --num=5
   ```

4. When complete, mark as done:
   ```bash
   task-master set-status --id=<task_id> --status=done
   ```

### Updating Project Requirements

1. Update your PRD with new requirements

2. You have two options:

   - **Option A**: Add new tasks without affecting existing ones:
     ```bash
     task-master add-task --prompt="Implement new feature from updated PRD" --priority="medium"
     ```
   - **Option B**: Overwrite all tasks (CAUTION - destroys progress):

     ```bash
     # First backup existing tasks
     cp -r tasks tasks_backup

     # Then generate new tasks
     task-master parse-prd --input=scripts/prd.txt
     ```

3. Update existing tasks with new context:
   ```bash
   task-master update --from=5 --prompt="PRD has been updated with new requirements"
   ```

---

## Specific Use Cases

### Adding a New Feature Without Disturbing Progress

```bash
# Backup tasks first (always a good practice)
cp -r tasks tasks_backup

# Add new task for the feature
task-master add-task --prompt="Implement feature X as described in section Y of the PRD" --priority="medium" --dependencies="3,5"
```

### Reworking a Task

```bash
# Update the task with new information
task-master update-task --id=5 --prompt="The feature needs to be reworked because of X"

# Remove old subtasks if they exist
task-master clear-subtasks --id=5

# Generate new subtasks
task-master expand --id=5 --num=5
```

### Finding Blocked Tasks

```bash
# List all tasks with their dependencies
task-master list

# Look for tasks with dependencies that aren't complete
# The output will show "Tasks blocked by dependencies" in the dashboard
```

### Optimizing Task Dependencies

```bash
# Validate dependencies to find issues
task-master validate-dependencies

# Fix issues automatically
task-master fix-dependencies
```

---

## Troubleshooting

### Task Master Commands Not Working

1. Check MCP integration is running:

   - Look for "taskmaster-ai" in the MCP panel
   - Ensure it shows the correct number of tools

2. Verify Task Master installation:

   ```bash
   # Should return the Task Master ASCII art and help menu
   task-master help
   ```

3. If issue persists:
   - Look for errors in the terminal output
   - Check that your environment variables are set correctly

### Tasks Not Being Generated Properly

1. Verify your PRD format is easily parsable:

   - Clear section headers
   - Well-structured content
   - Explicit feature descriptions

2. Try specifying the number of tasks:

   ```bash
   task-master parse-prd --input=scripts/prd.txt --tasks=15
   ```

3. If AI generation is struggling, try breaking your request into multiple tasks:
   ```bash
   task-master add-task --prompt="Implement feature X" --priority="high"
   task-master add-task --prompt="Implement feature Y" --priority="medium"
   ```

### Lost Task Progress

If you accidentally overwrote tasks:

1. Check for backups:

   ```bash
   ls -la *tasks_backup*
   ```

2. Restore from backup:

   ```bash
   cp -r tasks_backup/* tasks/
   ```

3. Regenerate task files:
   ```bash
   task-master generate
   ```

### Dependency Errors

If tasks show invalid dependencies:

1. List all tasks to identify issues:

   ```bash
   task-master list
   ```

2. Fix automatically:

   ```bash
   task-master fix-dependencies
   ```

3. Or manually remove problematic dependencies:
   ```bash
   task-master remove-dependency --id=5 --dependsOn=999
   ```

---

## Best Practices

1. **Always backup tasks before major operations**:

   ```bash
   cp -r tasks tasks_backup_$(date +%Y%m%d_%H%M%S)
   ```

2. **Add tasks incrementally** rather than regenerating all tasks:

   ```bash
   task-master add-task --prompt="New feature" --priority="medium"
   ```

3. **Use clear, specific prompts** when generating tasks with AI:

   ```bash
   # Good
   task-master add-task --prompt="Implement user authentication with Google OAuth as described in section 3.2 of the PRD" --priority="high"

   # Bad
   task-master add-task --prompt="Do auth stuff" --priority="high"
   ```

4. **Keep your PRD updated and well-structured** for better task generation

5. **Set realistic dependencies** to avoid dependency chains that block progress

6. **Use the task expansion feature** for complex tasks rather than creating many small tasks

7. **Regularly update task statuses** to keep the project dashboard accurate
