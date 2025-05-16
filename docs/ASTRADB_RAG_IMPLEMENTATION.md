# AstraDB RAG Implementation Documentation

This document provides comprehensive details on the implementation of Retrieval Augmented Generation (RAG) using AstraDB with the Agno agent for the Zendesk integration.

## Table of Contents

1. [Files Created](#files-created)
2. [Configuration](#configuration)
3. [Implementation Details](#implementation-details)
4. [Integration Points](#integration-points)
5. [Data Loading](#data-loading)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

## Files Created

### Core Implementation
- `/Users/welovekiteboarding/Development/agno-zendesk/astra_rag_agent.py`: Main implementation of the AstraDB RAG integration
- `/Users/welovekiteboarding/Development/agno-zendesk/docs/ASTRADB_RAG_INTEGRATION.md`: User-facing documentation
- `/Users/welovekiteboarding/Development/agno-zendesk/docs/ASTRADB_RAG_IMPLEMENTATION.md`: This implementation documentation

### Example Scripts
- `/Users/welovekiteboarding/Development/agno-zendesk/examples/astra_rag_example.py`: Example usage with environment variables
- `/Users/welovekiteboarding/Development/agno-zendesk/examples/astra_rag_example_with_dotenv.py`: Example usage with .env.local
- `/Users/welovekiteboarding/Development/agno-zendesk/examples/load_documents_to_astradb.py`: Document loader using environment variables
- `/Users/welovekiteboarding/Development/agno-zendesk/examples/load_documents_to_astradb_with_dotenv.py`: Document loader using .env.local

### Test Data
- `/Users/welovekiteboarding/Development/agno-zendesk/test_docs/bug_reporting.md`: Test document
- `/Users/welovekiteboarding/Development/agno-zendesk/test_docs/feature_requests.md`: Test document
- `/Users/welovekiteboarding/Development/agno-zendesk/test_docs/support_faq.md`: Test document

## Configuration

### Environment Variables
Added to `/Users/welovekiteboarding/Development/agno-zendesk/frontend__backup2/.env.local`:

```
# AstraDB Configuration
ASTRA_ENDPOINT="https://afd7d5ff-8e1b-4365-997d-60b742a72976-us-east-2.apps.astra.datastax.com"
ASTRA_TOKEN="your_astra_token"
ASTRA_COLLECTION="ss_guide"
ASTRA_NAMESPACE="default"
```

### Dependencies
Required Python packages:
- `cassandra-driver`: For connecting to AstraDB
- `openai`: For generating embeddings
- `agno`: The Agno agent framework
- `python-dotenv`: For loading environment variables from .env files

## Implementation Details

### `astra_rag_agent.py`

The implementation has two main components:

1. **`astra_db_search` Tool Function**
   - Decorated with `@tool` to be usable by Agno agents
   - Takes a query and AstraDB connection parameters
   - Generates embeddings for the query using OpenAI
   - Connects to AstraDB using the Cassandra driver
   - Performs vector similarity search
   - Formats and returns the results

```python
@tool(
    name="astra_search",
    description="Search for information in the database to help answer the question.",
    instructions="""
    Use this tool to search for information in the knowledge base that might help 
    answer questions about bug reporting and other support topics.
    """
)
async def astra_db_search(
    query: str,
    astra_endpoint: str,
    astra_token: str,
    collection_name: str,
    namespace: str = "default",
) -> str:
    """
    Search AstraDB for relevant information.
    
    Args:
        query: The query to search for
        astra_endpoint: AstraDB API endpoint
        astra_token: AstraDB API token
        collection_name: Name of collection to search
        namespace: Namespace of collection
        
    Returns:
        The search results as a string
    """
    # Implementation details...
```

2. **`add_astra_rag_to_agent` Helper Function**
   - Takes an existing Agno agent and AstraDB parameters
   - Adds the `astra_db_search` tool to the agent
   - Stores the AstraDB configuration in the agent's context
   - Adds instructions for using the knowledge base
   - Returns the enhanced agent

```python
def add_astra_rag_to_agent(
    agent: Agent,
    astra_endpoint: str,
    astra_token: str,
    collection_name: str,
    namespace: str = "default",
    embedder: Optional[Embedder] = None,
) -> Agent:
    """
    Add AstraDB RAG capabilities to an existing Agno agent
    
    Args:
        agent: Existing Agno agent
        astra_endpoint: AstraDB API endpoint
        astra_token: AstraDB API token
        collection_name: Name of collection to search
        namespace: Namespace of collection
        embedder: Embedder to use for query embedding
        
    Returns:
        The same agent with RAG capabilities added
    """
    # Implementation details...
```

### AstraDB Connection

The connection to AstraDB is established using these steps:

1. **Parse AstraDB Token**
   ```python
   token_parts = astra_token.split(':')
   client_id = token_parts[1]
   client_secret = token_parts[2]
   ```

2. **Extract Database ID**
   ```python
   endpoint_parts = astra_endpoint.split('/')
   host_parts = endpoint_parts[2].split('-')
   database_id = '-'.join(host_parts[0:5])
   ```

3. **Create Cassandra Cluster**
   ```python
   auth_provider = PlainTextAuthProvider(client_id, client_secret)
   contact_points = [f"{database_id}-us-east-2.db.astra.datastax.com"]
   port = 29042
   
   cluster = Cluster(
       contact_points=contact_points,
       port=port,
       auth_provider=auth_provider,
       protocol_version=4
   )
   ```

4. **Connect to Namespace**
   ```python
   session = await asyncio.to_thread(cluster.connect, namespace)
   ```

### Vector Search

The vector search is implemented as follows:

1. **Generate Embedding**
   ```python
   embedder = OpenAIEmbedder(id="text-embedding-3-small")
   vector = await embedder.async_get_embedding(query)
   ```

2. **Format Vector for CQL**
   ```python
   vector_str = str(vector).replace('[', '{').replace(']', '}')
   ```

3. **Execute Vector Search**
   ```python
   query_cql = f"""
       SELECT content, name, metadata 
       FROM {collection_name} 
       ORDER BY vector ANN OF {vector_str} LIMIT 5
   """
   
   results = await asyncio.to_thread(session.execute, query_cql)
   ```

4. **Format Results**
   ```python
   formatted_results = "Here is the relevant information from the knowledge base:\n\n"
   
   for i, row in enumerate(result_list, 1):
       content = getattr(row, 'content', "No content available")
       source = getattr(row, 'name', f"Document {i}")
       metadata = getattr(row, 'metadata', {})
       
       formatted_results += f"--- Source: {source} ---\n{content}\n\n"
       
       if metadata:
           formatted_results += "Metadata:\n"
           # Format metadata...
   ```

## Integration Points

### Integration with Agno Agent in Zendesk Interface

The integration should be added to:
- **File**: `/Users/welovekiteboarding/Development/agno-zendesk/frontend__backup2/components/features/AgnoChatUI.tsx`

Add the following imports:
```typescript
import { addAstraRagToAgent } from '../../utils/astraRagAgent';
```

Modify the agent initialization:
```typescript
// After creating the agent
addAstraRagToAgent(
  agent,
  process.env.ASTRA_ENDPOINT as string,
  process.env.ASTRA_TOKEN as string,
  process.env.ASTRA_COLLECTION as string,
  process.env.ASTRA_NAMESPACE || 'default'
);
```

### Backend API Route Integration

For the backend API route that handles chat requests:
- **File**: `/Users/welovekiteboarding/Development/agno-zendesk/frontend__backup2/app/api/zendesk/create-ticket/route.ts`

Add the AstraDB RAG to the agent before processing the query:
```typescript
// Import at the top
import { addAstraRagToAgent } from '../../../../utils/astraRagAgent';

// In the handler function
const agent = new Agent({
  // Existing configuration
});

// Add RAG capabilities
addAstraRagToAgent(
  agent,
  process.env.ASTRA_ENDPOINT as string,
  process.env.ASTRA_TOKEN as string,
  process.env.ASTRA_COLLECTION as string,
  process.env.ASTRA_NAMESPACE || 'default'
);

// Continue with existing logic
```

### TypeScript Utility Implementation

Create a new utility file to provide the TypeScript wrapper:
- **File**: `/Users/welovekiteboarding/Development/agno-zendesk/frontend__backup2/utils/astraRagAgent.ts`

With this implementation:
```typescript
import { Agent } from 'agno';

/**
 * Adds AstraDB RAG capabilities to an existing Agno agent
 */
export function addAstraRagToAgent(
  agent: Agent,
  astraEndpoint: string,
  astraToken: string,
  collectionName: string,
  namespace: string = 'default'
): Agent {
  // Implementation details - either call the Python implementation
  // or implement directly in TypeScript
  
  // Return the enhanced agent
  return agent;
}
```

## Data Loading

### Document Schema

The AstraDB collection uses this schema:

```cql
CREATE TABLE IF NOT EXISTS default.ss_guide (
    id UUID PRIMARY KEY,
    name TEXT,
    content TEXT,
    metadata TEXT,
    vector VECTOR<FLOAT, 1536>
)
WITH cosmosdb_vector_indexes = {'vectors': {'vector': {'dimensions': 1536, 'metric': 'cosine'}}};
```

Key fields:
- `id`: UUID primary key
- `name`: Document name or title
- `content`: The document content
- `metadata`: JSON string with additional document metadata
- `vector`: 1536-dimensional vector for text-embedding-3-small embeddings

### Loading Document Procedure

The detailed procedure for loading documents:

1. **Read Document Files**
   - Load text or markdown files from a directory
   - Extract content, filename, and metadata

2. **Generate Embeddings**
   - Use OpenAI's text-embedding-3-small model
   - Generate 1536-dimensional embedding vectors

3. **Format Data for AstraDB**
   - Format vectors for Cassandra CQL
   - Convert metadata to JSON string

4. **Insert into AstraDB**
   - Use the Cassandra driver to execute CQL insert statements
   - Add documents with embeddings to the collection

Implementation in `load_documents_to_astradb_with_dotenv.py`:

```python
# Key functions for document loading:

async def generate_embedding(client, text: str) -> List[float]:
    """Generate embedding for text using OpenAI API."""
    # Implementation...

async def load_documents(
    docs_directory: str,
    astra_endpoint: str,
    astra_token: str,
    collection_name: str,
    namespace: str = "default"
) -> None:
    """Load documents from a directory into AstraDB."""
    # Implementation...
```

## Testing

### How to Test

To test the AstraDB RAG integration:

1. **Set Up Environment**
   - Ensure `.env.local` has the correct AstraDB credentials
   - Install required dependencies:
     ```bash
     pip install cassandra-driver openai agno python-dotenv
     ```

2. **Load Test Documents**
   - Run the document loader:
     ```bash
     cd /Users/welovekiteboarding/Development/agno-zendesk
     python examples/load_documents_to_astradb_with_dotenv.py test_docs
     ```

3. **Test RAG Agent**
   - Run the example script:
     ```bash
     python examples/astra_rag_example_with_dotenv.py
     ```
   - Ask questions related to the loaded documents

4. **Test Integration**
   - After implementing the integration points, test the full Zendesk interface
   - Ask questions that should trigger knowledge base lookups

### Common Issues

1. **SSL Parameter Issue**
   - Error: `TypeError: Cluster.__init__() got an unexpected keyword argument 'ssl'`
   - Fix: Remove the `ssl=True` parameter in the Cluster constructor

2. **Vector Format Error**
   - Error: Invalid vector format in CQL query
   - Fix: Ensure vector is properly formatted with `str(vector).replace('[', '{').replace(']', '}')`

3. **Connection Issues**
   - Error: Can't connect to AstraDB
   - Fix: Check endpoint format, token validity, and SSL settings

## Troubleshooting

### Error: Invalid AstraDB Token Format

If you encounter this error:
```
Invalid AstraDB token format. Expected format: AstraCS:<client_id>:<client_secret>
```

The token must follow the format `AstraCS:<client_id>:<client_secret>`. Check your `.env.local` file and ensure the token is correctly formatted.

### Error: Can't Connect to AstraDB

If connection issues occur:
1. Verify the database ID is correctly extracted from the endpoint
2. Ensure the port is set to 29042
3. Remove any SSL options that might be causing issues
4. Check the network connection and firewall settings

### Error: Invalid Vector Format

If you see vector formatting errors:
1. Ensure the OpenAI embeddings are correctly formatted for CQL
2. The format should be `{0.1, 0.2, ...}` not `[0.1, 0.2, ...]`
3. Check the format conversion: `str(vector).replace('[', '{').replace(']', '}')`

### Error: Table Not Found

If the collection doesn't exist:
1. Create it manually with the correct schema
2. Check the namespace and collection name match your environment variables
3. Ensure the vector dimension is set to 1536 for text-embedding-3-small