# AstraDB RAG Integration with Agno Agent: Complete Implementation Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Core AstraDB Integration](#core-astradb-integration)
   - [Connecting to AstraDB](#connecting-to-astradb)
   - [Embedding Generation](#embedding-generation)
   - [Vector Search Implementation](#vector-search-implementation)
5. [Simple Retrieval Test](#simple-retrieval-test)
6. [Agent Integration](#agent-integration)
7. [Complete Implementation Examples](#complete-implementation-examples)
   - [Standalone RAG Implementation](#standalone-rag-implementation)
   - [Agno Agent Integration](#agno-agent-integration)
8. [Troubleshooting and Best Practices](#troubleshooting-and-best-practices)
9. [Conclusion](#conclusion)

## Introduction

This document provides a comprehensive guide for integrating AstraDB's vector search capabilities with the Agno agent framework to implement Retrieval Augmented Generation (RAG). The implementation described here ensures read-only access to existing database collections, focusing exclusively on retrieval operations.

Retrieval Augmented Generation enhances a language model's responses by retrieving relevant documents from a knowledge base before generating a response. This approach improves accuracy and allows the model to access domain-specific information that may not be in its training data.

## Prerequisites

Before implementing AstraDB RAG with an Agno agent, ensure you have the following:

1. **AstraDB Account and Database**
   - Active AstraDB account and database instance
   - An existing collection with document data (we use `ss_guide` in examples)
   - API endpoint and token with read access permissions

2. **Required Python Packages**
   - astrapy: For AstraDB connection and operations
   - openai: For generating embeddings
   - python-dotenv: For managing environment variables
   - agno: The Agno agent framework

3. **API Keys**
   - OpenAI API key (for embedding generation)
   - AstraDB API token

## Environment Setup

Create a `.env` file in your project root with the following variables:

```
# AstraDB Configuration
ASTRA_ENDPOINT=https://your-astra-id.apps.astra.datastax.com
ASTRA_TOKEN=AstraCS:your-token-here
ASTRA_COLLECTION=ss_guide
ASTRA_NAMESPACE=default

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-key
```

Environment loading code:

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Access configuration
ASTRA_ENDPOINT = os.getenv("ASTRA_ENDPOINT")
ASTRA_TOKEN = os.getenv("ASTRA_TOKEN")
ASTRA_COLLECTION = os.getenv("ASTRA_COLLECTION")
ASTRA_NAMESPACE = os.getenv("ASTRA_NAMESPACE", "default")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

## Core AstraDB Integration

### Connecting to AstraDB

The following code establishes a connection to AstraDB and accesses a collection:

```python
from astrapy.db import AstraDB

def connect_to_astradb(endpoint, token, collection_name, namespace="default"):
    """
    Establish a connection to AstraDB and return the collection.
    
    Args:
        endpoint: AstraDB API endpoint
        token: AstraDB API token
        collection_name: Name of the collection to access
        namespace: Namespace for the collection (default: "default")
        
    Returns:
        AstraDB collection object
    """
    try:
        # Initialize the AstraDB client
        db = AstraDB(
            token=token,
            api_endpoint=endpoint
        )
        
        # Access the collection
        collection = db.collection(collection_name, namespace)
        
        print(f"Successfully connected to collection '{collection_name}'")
        return collection
    
    except Exception as e:
        print(f"Error connecting to AstraDB: {str(e)}")
        return None
```

### Embedding Generation

Vector search requires converting text queries into embeddings. This implementation uses OpenAI's embedding models:

```python
import openai

async def generate_embedding(text, model="text-embedding-3-small"):
    """
    Generate an embedding vector for the given text using OpenAI.
    
    Args:
        text: Text to generate embedding for
        model: OpenAI embedding model to use
        
    Returns:
        List of floating point values representing the embedding
    """
    try:
        client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = await client.embeddings.create(
            input=text,
            model=model
        )
        return response.data[0].embedding
    
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        return None
```

### Vector Search Implementation

The following code implements vector search against an AstraDB collection:

```python
async def vector_search(collection, query_embedding, limit=5):
    """
    Perform a vector similarity search in AstraDB.
    
    Args:
        collection: AstraDB collection object
        query_embedding: Embedding vector for the query
        limit: Maximum number of results to return
        
    Returns:
        List of matching documents with similarity scores
    """
    try:
        # Perform vector search
        results = collection.vector_find(
            vector=query_embedding,
            limit=limit
        )
        
        return list(results)
    
    except Exception as e:
        print(f"Error performing vector search: {str(e)}")
        return []
```

## Simple Retrieval Test

Before integrating with an Agno agent, it's important to test the basic retrieval functionality. Here's a complete test script:

```python
import os
import asyncio
import json
from dotenv import load_dotenv
import openai
from astrapy.db import AstraDB

# Load environment variables
load_dotenv()

# Configuration
ASTRA_ENDPOINT = os.getenv("ASTRA_ENDPOINT")
ASTRA_TOKEN = os.getenv("ASTRA_TOKEN")
ASTRA_COLLECTION = os.getenv("ASTRA_COLLECTION")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


async def generate_embedding(text, model="text-embedding-3-small"):
    """Generate embedding for the given text"""
    client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
    response = await client.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding


async def test_astra_retrieval():
    """Test retrieval from AstraDB"""
    # Connect to AstraDB
    print(f"Connecting to AstraDB at {ASTRA_ENDPOINT}")
    db = AstraDB(
        token=ASTRA_TOKEN,
        api_endpoint=ASTRA_ENDPOINT
    )
    
    # Access collection
    collection = db.collection(ASTRA_COLLECTION)
    print(f"Connected to collection: {ASTRA_COLLECTION}")
    
    # Test query
    query = "How do I report a bug?"
    print(f"Testing query: '{query}'")
    
    # Generate embedding
    query_embedding = await generate_embedding(query)
    print(f"Generated embedding with {len(query_embedding)} dimensions")
    
    # Perform vector search
    results = collection.vector_find(
        vector=query_embedding,
        limit=5
    )
    
    # Process results
    result_list = list(results)
    print(f"Found {len(result_list)} matching documents")
    
    # Display results
    for i, doc in enumerate(result_list, 1):
        doc_id = doc.get('_id', f"Document {i}")
        similarity = doc.get('$similarity', 0.0)
        text = doc.get('text', '')[:100] + "..." if len(doc.get('text', '')) > 100 else doc.get('text', '')
        
        print(f"\nResult #{i} (ID: {doc_id}, Similarity: {similarity:.4f})")
        print(f"Text snippet: {text}")


if __name__ == "__main__":
    asyncio.run(test_astra_retrieval())
```

## Agent Integration

Integrating with the Agno agent framework requires creating a tool function that performs the RAG operations and returns formatted results. This section explains how to implement this integration.

### Creating the RAG Tool Function

```python
from agno.tool import tool

@tool(
    name="astra_search",
    description="Search for information in the AstraDB knowledge base",
    instructions="Use this tool to retrieve information relevant to the user's query"
)
async def astra_db_search(
    query: str,
    astra_endpoint: str,
    astra_token: str,
    collection_name: str,
    namespace: str = "default",
) -> str:
    """
    Search the AstraDB knowledge base for relevant information.
    
    Args:
        query: The user query to search for
        astra_endpoint: AstraDB API endpoint
        astra_token: AstraDB API token
        collection_name: Collection name to search in
        namespace: Namespace for the collection
        
    Returns:
        Formatted string with search results
    """
    try:
        # Generate embedding for the query
        client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = await client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )
        query_embedding = response.data[0].embedding
        
        # Connect to AstraDB
        db = AstraDB(
            token=astra_token,
            api_endpoint=astra_endpoint
        )
        
        # Get the collection
        collection = db.collection(collection_name, namespace)
        
        # Perform vector search
        results = collection.vector_find(
            vector=query_embedding,
            limit=5
        )
        
        # Check if we got any results
        result_list = list(results)
        if not result_list:
            return "No relevant information found in the knowledge base."
        
        # Format results as a string
        formatted_results = "### Relevant Information from Knowledge Base\n\n"
        
        for i, doc in enumerate(result_list, 1):
            # Extract content and metadata
            content = doc.get('text', '')
            doc_id = doc.get('_id', f"Document {i}")
            similarity = doc.get('$similarity', 0.0)
            
            formatted_results += f"**Source #{i}** (Relevance: {similarity:.4f})\n"
            formatted_results += f"{content}\n\n"
        
        return formatted_results
        
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"
```

### Adding the Tool to an Agno Agent

```python
from agno.agent import Agent
from agno.models.anthropic import Claude

def create_zendesk_rag_agent():
    """
    Create an Agno agent with AstraDB RAG capabilities.
    
    Returns:
        An Agno agent with RAG capabilities
    """
    # Create the agent with the search tool
    agent = Agent(
        name="Zendesk Support Assistant",
        model=Claude(id="claude-3-7-sonnet-latest"),
        instructions=[
            "You are a helpful support assistant for Zendesk.",
            "Answer user questions about bug reporting, feature requests, and technical support.",
            "You have access to a knowledge base of support articles that you can search.",
            "When asked questions about specific features or procedures, always search the knowledge base first.",
            "If the knowledge base provides relevant information, prioritize that over your general knowledge.",
            "Be concise, friendly, and helpful in your responses."
        ],
        tools=[astra_db_search],
        show_tool_calls=True,
        markdown=True
    )
    
    return agent
```

## Complete Implementation Examples

### Standalone RAG Implementation

Below is a complete implementation of the standalone RAG functionality:

```python
"""
Simplified AstraDB RAG Implementation

This module provides a simplified implementation of AstraDB RAG functionality
that works with the existing codebase structure and only performs
retrieval operations (no database modifications).
"""

import os
import sys
import json
import asyncio
from dotenv import load_dotenv

# For OpenAI embedding generation
import openai

# For AstraDB connection
from astrapy.db import AstraDB

# Load environment variables
load_dotenv()

# Configuration from environment
ASTRA_ENDPOINT = os.getenv("ASTRA_ENDPOINT")
ASTRA_TOKEN = os.getenv("ASTRA_TOKEN")
ASTRA_COLLECTION = os.getenv("ASTRA_COLLECTION")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configure OpenAI
openai.api_key = OPENAI_API_KEY


async def generate_embedding(text: str) -> list[float]:
    """
    Generate an embedding for the given text using OpenAI.
    
    Args:
        text: The text to generate an embedding for
        
    Returns:
        The embedding as a list of floats
    """
    client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
    response = await client.embeddings.create(
        input=text, 
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


async def search_astradb(query: str, limit: int = 5) -> list[dict]:
    """
    Search AstraDB for relevant documents based on the query.
    This is a READ-ONLY operation that doesn't modify the database.
    
    Args:
        query: The search query
        limit: Number of results to return
        
    Returns:
        List of matching documents with similarity scores
    """
    # Get AstraDB configuration
    if not all([ASTRA_ENDPOINT, ASTRA_TOKEN, ASTRA_COLLECTION, OPENAI_API_KEY]):
        print("Error: Missing required environment variables.")
        return []
    
    try:
        # Generate embedding for the query
        print(f"Generating embedding for query: '{query}'")
        query_embedding = await generate_embedding(query)
        
        # Connect to AstraDB
        print("Connecting to AstraDB...")
        db = AstraDB(
            token=ASTRA_TOKEN,
            api_endpoint=ASTRA_ENDPOINT
        )
        
        # Get the collection
        collection = db.collection(ASTRA_COLLECTION)
        
        # Perform vector search (READ-ONLY)
        print("Performing vector search...")
        results = collection.vector_find(
            vector=query_embedding,
            limit=limit
        )
        
        return list(results)
        
    except Exception as e:
        print(f"Error during AstraDB search: {str(e)}")
        return []


def format_results(results: list[dict]) -> str:
    """
    Format search results into a readable string.
    
    Args:
        results: List of document results from AstraDB
        
    Returns:
        Formatted results as a string
    """
    if not results:
        return "No relevant information found in the knowledge base."
    
    formatted_text = "### Relevant Information from Knowledge Base\n\n"
    
    for i, doc in enumerate(results, 1):
        # Extract content and metadata
        content = doc.get('text', '')
        doc_id = doc.get('_id', f"Document {i}")
        similarity = doc.get('$similarity', 0.0)
        
        formatted_text += f"**Source #{i}** (Relevance: {similarity:.4f})\n"
        formatted_text += f"{content}\n\n"
    
    return formatted_text


async def main():
    """Run a simple test of the RAG search functionality"""
    # Get query from command line or use default
    query = sys.argv[1] if len(sys.argv) > 1 else "How do I report a bug?"
    
    print(f"\n🔍 Testing RAG search with query: '{query}'")
    
    # Perform the search
    results = await search_astradb(query)
    
    # Format and display results
    formatted_results = format_results(results)
    print("\n🔎 Search Results:")
    print(formatted_results)
    
    # Print document IDs and similarity scores
    print("\n📊 Document Statistics:")
    for i, doc in enumerate(results, 1):
        doc_id = doc.get('_id', 'unknown')
        similarity = doc.get('$similarity', 0.0)
        print(f"  Document #{i}: ID={doc_id}, Similarity={similarity:.4f}")


if __name__ == "__main__":
    # Run the test
    asyncio.run(main())
```

### Agno Agent Integration

Here is a complete implementation of the Agno agent integration:

```python
"""
AstraDB RAG Integration with Agno Zendesk Agent

This module provides the integration between the Agno Zendesk agent
and AstraDB for Retrieval Augmented Generation (RAG).

Following the structure from the Agno cookbook, this is a READ-ONLY
implementation that only performs retrieval operations.
"""

import os
import json
from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tool import tool

# For OpenAI embedding generation
import openai

# For the AstraDB connection
from astrapy.db import AstraDB

# Load environment variables
load_dotenv()

# Configuration from environment
ASTRA_ENDPOINT = os.getenv("ASTRA_ENDPOINT")
ASTRA_TOKEN = os.getenv("ASTRA_TOKEN")
ASTRA_COLLECTION = os.getenv("ASTRA_COLLECTION")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@tool(
    name="astra_search",
    description="Search for information in the AstraDB knowledge base",
    instructions="Use this tool to retrieve information relevant to the user's query"
)
async def astra_db_search(
    query: str,
) -> str:
    """
    Search the AstraDB knowledge base for relevant information.
    
    Args:
        query: The user query to search for
        
    Returns:
        Formatted string with search results
    """
    try:
        # Generate embedding for the query
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        response = await client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )
        query_embedding = response.data[0].embedding
        
        # Connect to AstraDB
        db = AstraDB(
            token=ASTRA_TOKEN,
            api_endpoint=ASTRA_ENDPOINT
        )
        
        # Get the collection
        collection = db.collection(ASTRA_COLLECTION)
        
        # Perform vector search
        results = collection.vector_find(
            vector=query_embedding,
            limit=5
        )
        
        # Check if we got any results
        result_list = list(results)
        if not result_list:
            return "No relevant information found in the knowledge base."
        
        # Format results as a string
        formatted_results = "### Relevant Information from Knowledge Base\n\n"
        
        for i, doc in enumerate(result_list, 1):
            # Extract content and metadata
            content = doc.get('text', '')
            doc_id = doc.get('_id', f"Document {i}")
            similarity = doc.get('$similarity', 0.0)
            
            formatted_results += f"**Source #{i}** (Relevance: {similarity:.4f})\n"
            formatted_results += f"{content}\n\n"
        
        return formatted_results
        
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"


def create_zendesk_rag_agent():
    """
    Create an Agno agent with AstraDB RAG capabilities.
    
    Returns:
        An Agno agent with RAG capabilities
    """
    # Create the agent with the search tool
    agent = Agent(
        name="Zendesk Support Assistant",
        model=Claude(id="claude-3-7-sonnet-latest"),
        instructions=[
            "You are a helpful support assistant for Zendesk.",
            "Answer user questions about bug reporting, feature requests, and technical support.",
            "You have access to a knowledge base of support articles that you can search.",
            "When asked questions about specific features or procedures, always search the knowledge base first.",
            "If the knowledge base provides relevant information, prioritize that over your general knowledge.",
            "Be concise, friendly, and helpful in your responses."
        ],
        tools=[astra_db_search],
        show_tool_calls=True,
        markdown=True
    )
    
    return agent


if __name__ == "__main__":
    import asyncio
    import sys
    
    async def test_rag_agent():
        """Test the RAG agent with a sample query"""
        agent = create_zendesk_rag_agent()
        
        # Get query from command line or use default
        query = sys.argv[1] if len(sys.argv) > 1 else "How do I report a bug?"
        
        print(f"\n🔍 Testing RAG agent with query: '{query}'")
        response = await agent.chat(query)
        print(f"\n🤖 Response:\n{response.content}")
    
    # Run the test
    asyncio.run(test_rag_agent())
```

## Troubleshooting and Best Practices

### Common Issues and Solutions

1. **Vector Size Mismatch**
   - **Issue**: Embedding vectors must match the expected dimension size in AstraDB.
   - **Solution**: Always use consistent embedding models. The OpenAI `text-embedding-3-small` model produces 1536-dimensional embeddings.

2. **API Key and Token Management**
   - **Issue**: Exposed API keys in code.
   - **Solution**: Always use environment variables or secure vaults for API keys and tokens.

3. **Error Handling**
   - **Issue**: Unhandled exceptions in asynchronous code.
   - **Solution**: Implement proper try/except blocks around network calls and async operations.

### Best Practices

1. **Read-Only Operations**
   - Always implement RAG with read-only access to protect existing data.
   - Create separate test collections for experimenting with write operations.

2. **Optimizing Retrieval**
   - Adjust the number of documents returned based on the use case.
   - Consider implementing reranking for better result quality.

3. **Efficient Resource Usage**
   - Cache embeddings for common queries to reduce API costs.
   - Implement connection pooling for AstraDB to avoid connection overhead.

4. **Monitoring and Logging**
   - Add proper logging to track RAG performance.
   - Monitor similarity scores to evaluate result quality.

## Conclusion

This guide has provided a comprehensive approach to implementing AstraDB RAG with the Agno agent framework. The implementation ensures:

1. **Read-Only Access**: All operations are retrieval-only, preserving existing data.
2. **Modularity**: Components are separated for easy testing and maintenance.
3. **Configurability**: Environment variables allow flexible deployment.

By following this guide, you can create a robust RAG solution that enhances your Agno agent with domain-specific knowledge from AstraDB.
