"""
Example script demonstrating how to use AstraDB with Agno for RAG
"""

import os
from agno.agent import Agent
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.text import TextKnowledgeBase
from agno.models.openai import OpenAIChat

from astradb_integration import AstraDb

def main():
    # AstraDB configuration
    ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_ENDPOINT", "your_astra_endpoint")
    ASTRA_DB_TOKEN = os.getenv("ASTRA_TOKEN", "your_astra_token")
    COLLECTION_NAME = "ss_guide"
    
    # Create an OpenAI embedder
    embedder = OpenAIEmbedder(id="text-embedding-3-small")
    
    # Create the AstraDB vector database
    vector_db = AstraDb(
        collection_name=COLLECTION_NAME,
        api_endpoint=ASTRA_DB_API_ENDPOINT,
        token=ASTRA_DB_TOKEN,
        dimensions=1536,
        similarity_metric="cosine",
        embedder=embedder
    )
    
    # Sample text for the knowledge base
    texts = [
        "Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability with the use of significant indentation.",
        "Python is dynamically typed and garbage-collected. It supports multiple programming paradigms, including structured, object-oriented, and functional programming.",
        "Python is often described as a 'batteries included' language due to its comprehensive standard library.",
        "Guido van Rossum began working on Python in the late 1980s as a successor to the ABC programming language and first released it in 1991.",
        "Python 2.0 was released in 2000 and introduced new features such as list comprehensions, garbage collection, and support for Unicode.",
        "Python 3.0, released in 2008, was a major revision that is not completely backward-compatible with earlier versions."
    ]
    
    # Create a knowledge base with the sample text
    knowledge_base = TextKnowledgeBase(
        texts=texts,
        vector_db=vector_db
    )
    
    # Load the knowledge base (this will insert the documents into AstraDB)
    # Comment this line after the first run as the knowledge base is already loaded
    knowledge_base.load()
    
    # Create an agent with the knowledge base
    agent = Agent(
        model=OpenAIChat(id="gpt-4o"),
        knowledge=knowledge_base,
        search_knowledge=True,
        show_tool_calls=True,
        markdown=True
    )
    
    # Test the agent with a query
    agent.print_response("When was Python 3.0 released and what was significant about it?", stream=True)

if __name__ == "__main__":
    main()