"""
Agno Zendesk Backend: Multi-agent system for bug report management

This package contains the backend implementation of the Agno Zendesk
integration, including the Agent Registry, Handoff Protocol, and
individual agent implementations.
"""

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Version
__version__ = '1.0.0'