# AstraDB Integration for Agno RAG

This package provides integration between DataStax AstraDB and Agno for building RAG (Retrieval Augmented Generation) applications.

## Features

- Seamless integration with Agno's agent framework
- Vector search using AstraDB's vector capabilities
- Support for various document types (text, PDF, CSV, websites)
- Custom document loading utilities
- Easy-to-use RAG agent implementation

## Requirements

- Python 3.8+
- Agno
- AstraDB account with API credentials
- OpenAI API key (for embeddings and LLM)

## Installation

```bash
pip install astrapy cassio
```

## Configuration

You need to set up the following environment variables:

```bash
export OPENAI_API_KEY="your_openai_api_key"
```

## Usage

### Initialize AstraDB Vector Database

```python
from astradb_integration import AstraDb
from agno.embedder.openai import OpenAIEmbedder

# Create embedder
embedder = OpenAIEmbedder(id="text-embedding-3-small")

# Create AstraDB vector database
vector_db = AstraDb(
    collection_name="your_collection_name",
    api_endpoint="your_astra_db_endpoint",
    token="your_astra_db_token",
    embedder=embedder,
    dimensions=1536,
    similarity_metric="cosine"
)
```

### Load Documents

```python
from document_loader import DocumentLoader

# Create document loader
loader = DocumentLoader(
    collection_name="your_collection_name",
    api_endpoint="your_astra_db_endpoint",
    token="your_astra_db_token"
)

# Load text files
loader.load_text_files("path/to/text/files")

# Load PDF files
loader.load_pdf_files("path/to/pdf/files")

# Load custom documents
custom_docs = [
    {
        "content": "Document content here",
        "metadata": {"key": "value"},
        "name": "Document name"
    }
]
loader.load_custom_documents(custom_docs)
```

### Create a RAG Agent

```python
from rag_agent import RAGAgent

# Create RAG agent
agent = RAGAgent(
    collection_name="your_collection_name",
    api_endpoint="your_astra_db_endpoint",
    token="your_astra_db_token"
)

# Ask a question
response = agent.ask("What should I include in a bug report?")
print(response)

# Or chat interactively
agent.chat("What should I include in a bug report?")
```

## Example Scripts

1. `example.py` - Basic example of using AstraDB with Agno
2. `load_documents.py` - Example of loading documents into AstraDB
3. `rag_agent.py` - Example of creating a RAG agent

## Integration with Bug Reporting System

This integration is designed to enhance the bug reporting system by providing relevant information to users as they fill out bug reports. The RAG capabilities allow the system to:

1. Provide guidance on how to write effective bug reports
2. Suggest relevant information to include based on the type of bug
3. Answer questions about the bug reporting process
4. Assist users in troubleshooting common issues

## Notes

- The default embedding model is OpenAI's text-embedding-3-small, but you can use any compatible embedding model.
- The default LLM model is OpenAI's gpt-4o, but you can use any compatible LLM model.
- AstraDB requires an API endpoint and token, which you can obtain from your DataStax AstraDB dashboard.
- This implementation leverages Agno's agent framework for seamless integration with other components.

## License

[MIT License](LICENSE)