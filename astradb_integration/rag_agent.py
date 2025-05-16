"""
Example of creating and using an Agno agent with AstraDB RAG
"""

import os
from agno.agent import Agent
from agno.embedder.openai import OpenAIEmbedder
from agno.models.openai import OpenAIChat
from astradb_integration import AstraDb

class RAGAgent:
    """
    RAG-powered agent using AstraDB for vector storage
    """
    
    def __init__(
        self,
        collection_name: str,
        api_endpoint: str,
        token: str,
        namespace: str = "default",
        model_id: str = "gpt-4o",
        embedder_id: str = "text-embedding-3-small",
        dimensions: int = 1536,
        similarity_metric: str = "cosine",
    ):
        """
        Initialize the RAG Agent
        
        Args:
            collection_name: Name of the AstraDB collection to use
            api_endpoint: The AstraDB API endpoint
            token: The AstraDB API token
            namespace: The namespace to use (default: "default")
            model_id: The LLM model ID to use
            embedder_id: The embedding model ID to use
            dimensions: Dimensions of the embedding vectors
            similarity_metric: Similarity metric to use (default: "cosine")
        """
        # Create embedder
        self.embedder = OpenAIEmbedder(id=embedder_id)
        
        # Create AstraDB vector database
        self.vector_db = AstraDb(
            collection_name=collection_name,
            api_endpoint=api_endpoint,
            token=token,
            namespace=namespace,
            embedder=self.embedder,
            dimensions=dimensions,
            similarity_metric=similarity_metric
        )
        
        # Create the agent with RAG capabilities
        self.agent = Agent(
            model=OpenAIChat(id=model_id),
            vector_db=self.vector_db,  # Pass vector_db directly for better integration
            search_knowledge=True,     # Enable RAG functionality
            show_tool_calls=True,      # Show when the agent searches the knowledge base
            markdown=True              # Enable markdown formatting in responses
        )
        
        # Define system prompt focused on bug reporting
        self.agent.set_system_prompt("""
        You are a helpful assistant with access to RAG-powered knowledge about bug reporting procedures.
        
        When discussing bug reports:
        - Provide accurate, helpful information based on your knowledge base
        - Be concise but thorough in your explanations
        - Focus on best practices for bug reporting
        - If asked about the bug reporting form, explain how to use it effectively
        - When the knowledge base doesn't contain specific information, be transparent about it
        
        Your goal is to help users understand how to submit effective bug reports that will lead to faster bug fixes.
        """)
        
    def ask(self, query: str) -> str:
        """
        Ask the agent a question and get a response
        
        Args:
            query: The question to ask
            
        Returns:
            The agent's response
        """
        return self.agent.generate(query)
        
    def chat(self, query: str) -> None:
        """
        Chat with the agent interactively with streaming output
        
        Args:
            query: The question to ask
        """
        self.agent.print_response(query, stream=True)
        
def main():
    # AstraDB configuration
    ASTRA_DB_API_ENDPOINT = "https://afd7d5ff-8e1b-4365-997d-60b742a72976-us-east-2.apps.astra.datastax.com"
    ASTRA_DB_TOKEN = os.getenv("ASTRA_TOKEN", "your_astra_token")
    COLLECTION_NAME = "ss_guide"
    
    # Create the RAG agent
    agent = RAGAgent(
        collection_name=COLLECTION_NAME,
        api_endpoint=ASTRA_DB_API_ENDPOINT,
        token=ASTRA_DB_TOKEN
    )
    
    # Example query
    query = "What should I include in a bug report to make it most helpful?"
    
    # Chat with the agent
    agent.chat(query)
    
if __name__ == "__main__":
    main()