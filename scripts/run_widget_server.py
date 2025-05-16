#!/usr/bin/env python
"""
Run Widget API Server

This script runs the FastAPI server for the Agno Multi-Agent Widget API.
It's designed for local testing of the backend that will serve the Vercel-hosted widget.
"""

import os
import sys
import logging
import uvicorn
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("widget_server_runner")


def load_environment():
    """Load environment variables from .env file and check required ones."""
    # Load .env file from project root directory
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(env_path)
    logger.info(f"Loaded environment from {env_path}")
    
    # Map AstraDB variables if needed
    if not os.getenv("ASTRA_ENDPOINT") and os.getenv("ASTRA_DB_API_ENDPOINT"):
        os.environ["ASTRA_ENDPOINT"] = os.getenv("ASTRA_DB_API_ENDPOINT")
    
    if not os.getenv("ASTRA_TOKEN") and os.getenv("ASTRA_DB_APPLICATION_TOKEN"):
        os.environ["ASTRA_TOKEN"] = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
    
    # Check required variables
    required_vars = ["ASTRA_ENDPOINT", "ASTRA_TOKEN", "OPENAI_API_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please make sure these are set in your .env file.")
        return False
    
    logger.info("All required environment variables are set")
    return True


if __name__ == "__main__":
    logger.info("Starting Agno Multi-Agent Widget API server")
    
    # Load and check environment variables
    if not load_environment():
        sys.exit(1)
    
    # Run the FastAPI server
    uvicorn.run(
        "agno_zendesk.multi_agent.server.widget_api:app",
        host="0.0.0.0",
        port=8080,  # Changed port to 8080 to avoid conflicts
        reload=True
    )
