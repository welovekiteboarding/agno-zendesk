# AstraDB RAG Integration Guide

This guide explains how to integrate AstraDB as a knowledge source for your Agno agent to enable Retrieval Augmented Generation (RAG).

## Overview

The `astra_rag_agent.py` file provides a simple integration between your existing Agno agent and AstraDB for RAG capabilities. This allows your agent to search an AstraDB vector database for relevant information when responding to user queries.

## Prerequisites

1. An AstraDB account and database with a vector-enabled collection
2. Your AstraDB API endpoint and token
3. An existing Agno agent

## Installation

1. Install required dependencies:

```bash
pip install cassandra-driver openai agno
```

2. Place the `astra_rag_agent.py` file in your project.

## Quick Start

```python
from agno.agent import Agent
from agno.models.anthropic import AnthropicChat
from astra_rag_agent import add_astra_rag_to_agent

# Create your Agno agent
agent = Agent(
    name="Support Agent",
    model=AnthropicChat(id="claude-3-opus-20240229"),
    instructions="You are a helpful support agent."
)

# Add AstraDB RAG capabilities
agent = add_astra_rag_to_agent(
    agent=agent,
    astra_endpoint="https://your-astra-id.apps.astra.datastax.com",
    astra_token="AstraCS:your-token",
    collection_name="your_collection",
    namespace="default"  # Optional, defaults to "default"
)

# Now your agent can use AstraDB for RAG
response = agent.chat("What can you tell me about bug reporting?")
print(response)
```

## Integrating with the Zendesk Support Page

You can integrate this RAG-enabled agent with your Zendesk support page by:

1. Import the agent in your backend API route that handles agent requests:

```python
from astra_rag_agent import add_astra_rag_to_agent

# In your API route handler
def handle_agent_request(request):
    # Create agent
    agent = create_agent()  # Your function to create the base agent
    
    # Add AstraDB RAG capabilities
    agent = add_astra_rag_to_agent(
        agent=agent,
        astra_endpoint=os.environ.get("ASTRA_ENDPOINT"),
        astra_token=os.environ.get("ASTRA_TOKEN"),
        collection_name=os.environ.get("ASTRA_COLLECTION"),
    )
    
    # Get query from request
    query = request.data.get('query')
    
    # Generate response
    response = agent.chat(query)
    
    return response
```

2. Make sure your frontend sends the user's query to this endpoint and displays the response.

## AstraDB Setup

1. Log in to your AstraDB account at https://astra.datastax.com/
2. Create a database with vector search enabled
3. Create a collection for your documents with the following schema:

```javascript
{
  "name": "string",      // Document name or title
  "content": "string",   // Document content
  "metadata": "object",  // Optional metadata
  "vector": "vector"     // Vector embedding
}
```

4. Generate embeddings for your documents using the same embedder as in the tool (default: OpenAI's text-embedding-3-small)
5. Insert your documents into the collection

## Environment Variables

To avoid hardcoding credentials, use environment variables:

```python
import os

agent = add_astra_rag_to_agent(
    agent=agent,
    astra_endpoint=os.environ.get("ASTRA_ENDPOINT"),
    astra_token=os.environ.get("ASTRA_TOKEN"),
    collection_name=os.environ.get("ASTRA_COLLECTION"),
)
```

## Customization

### Custom Embedder

You can use a custom embedder instead of the default OpenAI one:

```python
from agno.embedder.cohere import CohereEmbedder

embedder = CohereEmbedder(id="embed-english-v3.0")

agent = add_astra_rag_to_agent(
    agent=agent,
    astra_endpoint="https://your-astra-id.apps.astra.datastax.com",
    astra_token="AstraCS:your-token",
    collection_name="your_collection",
    embedder=embedder
)
```

### Custom Instructions

You can add more instructions to the agent after adding the AstraDB tool:

```python
agent = add_astra_rag_to_agent(...)

agent.add_instruction(
    "When answering questions about our bug reporting system, always include links to relevant documentation."
)
```

## Troubleshooting

### Connection Issues

If you have issues connecting to AstraDB, check:

1. Your AstraDB token and endpoint are correct
2. Your network allows connections to AstraDB
3. Your AstraDB database is active and running

### Query Issues

If vector search is not returning expected results:

1. Verify your collection schema includes a vector field
2. Check that documents are properly embedded
3. Test with simpler queries to verify connectivity

## Example: Loading Documents into AstraDB

Here's a simple example of loading documents into AstraDB:

```python
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from openai import OpenAI

def load_documents_to_astradb(
    documents,
    astra_endpoint,
    astra_token,
    collection_name,
    namespace="default"
):
    # Parse AstraDB token
    token_parts = astra_token.split(':')
    client_id = token_parts[1]
    client_secret = token_parts[2]
    
    # Set up auth provider
    auth_provider = PlainTextAuthProvider(client_id, client_secret)
    
    # Extract database ID from endpoint
    endpoint_parts = astra_endpoint.split('/')
    host_parts = endpoint_parts[2].split('-')
    database_id = '-'.join(host_parts[0:5])
    
    # Connect to AstraDB
    contact_points = [f"{database_id}-us-east-2.db.astra.datastax.com"]
    cluster = Cluster(
        contact_points=contact_points,
        port=29042,
        auth_provider=auth_provider,
        ssl=True,
        protocol_version=4
    )
    session = cluster.connect(namespace)
    
    # Create OpenAI client for embeddings
    openai_client = OpenAI()
    
    # Insert documents
    for doc in documents:
        # Generate embedding
        response = openai_client.embeddings.create(
            input=doc["content"],
            model="text-embedding-3-small"
        )
        vector = response.data[0].embedding
        
        # Format vector for CQL
        vector_str = str(vector).replace('[', '{').replace(']', '}')
        
        # Prepare metadata
        metadata = doc.get("metadata", {})
        
        # Insert document
        query = f"""
        INSERT INTO {collection_name} (
            name, content, metadata, vector
        ) VALUES (%s, %s, %s, %s)
        """
        session.execute(
            query, 
            (doc["name"], doc["content"], metadata, vector)
        )
    
    # Clean up
    session.shutdown()
    cluster.shutdown()
```

## Resources

- [AstraDB Documentation](https://docs.datastax.com/en/astra-db/)
- [Agno Documentation](https://docs.agno.ai/)
- [Cassandra Driver Documentation](https://docs.datastax.com/en/developer/python-driver/latest/)