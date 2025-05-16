# Mandatory Database Citations for RAG Responses

## Overview

This document outlines the implementation requirements for adding mandatory citation functionality to the Agno-Zendesk RAG system. The goal is to ensure that all information provided in responses is properly attributed to its source database context, improving transparency and reducing hallucinations.

## Functional Requirements

1. **Citation Generation**: Every chunk of context retrieved from the database must be assigned a unique citation identifier (e.g., `[1]`, `[2]`)
2. **Citation Enforcement**: The system must instruct the LLM to reference specific citations for every statement made in the response
3. **Citation Formatting**: Citations should be formatted inline (e.g., `This telescope has a 130mm aperture [2]`)
4. **Relevance Indicators**: Each citation should include information about its relevance to the query
5. **Citation Policy Injection**: A policy statement defining citation usage rules must be included with context

## Implementation Approach

The implementation will follow the pattern shown in the provided example code, adapted for Agno's agent architecture:

### 1. Context Preparation

```python
def prepare_context_with_citations(documents):
    """
    Prepare context with citations for the RAG response.
    
    Args:
        documents: List of document chunks retrieved from vector search
        
    Returns:
        String containing formatted context with citations
    """
    # Early return if no documents provided
    if not documents or len(documents) == 0:
        return ''
    
    # Sort documents by similarity score (highest to lowest)
    sorted_docs = sorted(documents, key=lambda x: x.get('$similarity', 0), reverse=True)
    
    # Filter out low-relevance documents
    relevant_docs = [doc for doc in sorted_docs if doc.get('$similarity', 0) >= 0.9]
    
    if len(relevant_docs) == 0:
        return ''
    
    citations = set()
    
    context_with_citations = []
    for i, doc in enumerate(relevant_docs):
        relevance_score = doc.get('$similarity', 0)
        relevance_indicator = "High" if relevance_score > 0.95 else "Medium" if relevance_score > 0.9 else "Low"
        
        citation_id = f"[{i + 1}]"
        citations.add(citation_id)
        
        context_with_citations.append(f"{citation_id} (Relevance: {relevance_indicator})\n{doc.get('text', '').strip()}\n")
    
    formatted_context = '\n---\n'.join(context_with_citations)
    
    # Append citation policy
    citation_policy = (
        f"\n\nCitation Policy:\n"
        f"- Every statement must reference at least one citation\n"
        f"- Only use citations {', '.join(citations)}\n"
        f"- If information is not found in citations, respond with \"Sorry, I cannot generate a reply given your query "
        f"and the context I retrieved. Please consider providing more information in your requests; i.e. program, "
        f"version, feature, operating system, specific problem, etc.\""
    )
    
    return formatted_context + citation_policy
```

### 2. System Prompt Modifications

We'll modify the system prompts to enforce citation usage:

```python
BASE_PROMPT = """IMPORTANT: You are an AI assistant for Zendesk support.
You ONLY use the provided context to answer questions but aim to be thorough and engaging.

STRICT RULES:
1. ONLY use information explicitly stated in the provided context
2. EVERY statement must include a citation (e.g. [1], [2])
3. If you cannot find relevant information in the context, respond EXACTLY with:
   "Sorry, I cannot generate a reply given your query and the context I retrieved. Please consider providing more information in your requests."
4. Do not make assumptions or inferences beyond what is directly stated
5. Do not mention that you are using context or citations
6. Start every response with "(Based on provided context)"

Context will be provided below this line:
----------------
"""
```

### 3. Hybrid Search Implementation

To improve context quality, we'll implement hybrid search combining vector similarity with keyword matching:

```python
def calculate_keyword_score(text, query):
    """Calculate a keyword-based relevance score."""
    normalized_text = text.lower()
    keywords = query.lower().split()
    
    score = 0
    for keyword in keywords:
        if keyword in normalized_text:
            score += 0.25
    
    return score

async def perform_hybrid_search(collection, embedding, query):
    """
    Perform hybrid search combining vector similarity with keyword matching.
    
    Args:
        collection: AstraDB collection
        embedding: Query embedding vector
        query: Original query text
        
    Returns:
        List of documents with hybrid similarity scores
    """
    # Vector search first
    results = await collection.vector_find(
        vector=embedding,
        limit=10
    )
    
    if not results:
        return []
    
    # Apply hybrid scoring
    hybrid_results = []
    for doc in results:
        vector_score = doc.get('$similarity', 0)
        keyword_score = calculate_keyword_score(doc.get('text', ''), query)
        hybrid_score = vector_score + keyword_score
        
        hybrid_results.append({
            'text': doc.get('text', ''),
            '$similarity': hybrid_score
        })
    
    # Sort and filter by hybrid score
    final_results = sorted(
        hybrid_results, 
        key=lambda x: x.get('$similarity', 0), 
        reverse=True
    )[:5]
    
    # Only keep documents above threshold
    return [doc for doc in final_results if doc.get('$similarity', 0) >= 0.9]
```

### 4. Agent Integration

To integrate with Agno's agent architecture:

```python
async def astra_db_search_with_citations(
    query: str,
    astra_endpoint: str,
    astra_token: str,
    collection_name: str,
    namespace: str = "default",
) -> str:
    """
    Enhanced AstraDB search that includes citations in the returned context.
    
    Args:
        query: The user query to search for
        astra_endpoint: AstraDB API endpoint
        astra_token: AstraDB API token
        collection_name: Collection name to search in
        namespace: Namespace for the collection
        
    Returns:
        Formatted context with citations
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
        
        # Perform hybrid search
        results = await perform_hybrid_search(collection, query_embedding, query)
        
        # Format results with citations
        formatted_context = prepare_context_with_citations(results)
        
        return formatted_context
        
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"
```

## Integration Steps

1. Enhance the existing RAG implementation with citation generation
2. Modify agent instructions to enforce citation usage
3. Update the search functionality to use hybrid search for better context
4. Add citation policies to all system prompts
5. Test the citation accuracy and coverage

## Benefits

1. **Reduced Hallucinations**: By forcing the model to cite specific sources, we reduce the likelihood of making up information
2. **Improved Transparency**: Users can see which parts of the response are backed by specific database content
3. **Better Trust**: Citations create a clear chain of evidence for the information provided
4. **Quality Control**: Citation metrics can be used to evaluate the quality of responses
5. **Debugging Aid**: Makes it easier to trace why certain information was included in responses

## Example Output

A properly cited response will look like:

```
(Based on provided context)

This telescope has a 130mm aperture [2] and comes with two eyepieces: 25mm and 10mm [1]. The mount is an equatorial design that allows for easy tracking of celestial objects [3].

To align the finderscope:
1. First, locate a distant object during daylight hours [2]
2. Center the object in your telescope's eyepiece [2]
3. Use the adjustment screws on the finderscope to align it with the same object [2]

The package includes StarSense technology for automatic alignment [4], which uses a camera to identify star patterns and align the telescope automatically.
```
