"""
Bug Reporting Assistant with AstraDB RAG
"""

import os
import argparse
from document_loader import DocumentLoader
from rag_agent import RAGAgent

# Default AstraDB configuration
DEFAULT_ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_ENDPOINT", "your_astra_endpoint")
DEFAULT_ASTRA_DB_TOKEN = os.getenv("ASTRA_TOKEN", "your_astra_token")
DEFAULT_COLLECTION_NAME = "ss_guide"

def load_sample_data(loader):
    """Load sample bug reporting guidance data"""
    print("Loading sample bug reporting data...")
    
    # Example custom documents about bug reporting
    custom_docs = [
        {
            "content": "SimCur bug reporting provides a direct line to our development team. Reports are prioritized by severity and impact.",
            "metadata": {"category": "bug_reporting", "importance": "high"},
            "name": "Bug Reporting Overview"
        },
        {
            "content": "When submitting a bug report, please include: steps to reproduce, expected result, actual result, and device information.",
            "metadata": {"category": "bug_reporting", "importance": "high"},
            "name": "Bug Report Requirements"
        },
        {
            "content": "Attaching screenshots or videos to your bug report greatly helps our team understand and fix the issue faster.",
            "metadata": {"category": "bug_reporting", "importance": "medium"},
            "name": "Bug Report Attachments"
        },
        {
            "content": "All bug reports are reviewed by our QA team before being assigned to the appropriate developer.",
            "metadata": {"category": "bug_reporting", "importance": "medium"},
            "name": "Bug Report Process"
        },
        {
            "content": "For urgent issues affecting multiple users, our team will prioritize fixes for the next release cycle.",
            "metadata": {"category": "bug_reporting", "importance": "high"},
            "name": "Bug Fix Priority"
        },
        {
            "content": "Bug reports should be concise but thorough. Include only the necessary information to reproduce and understand the issue.",
            "metadata": {"category": "best_practices", "importance": "medium"},
            "name": "Bug Report Conciseness"
        },
        {
            "content": "When describing steps to reproduce, be specific about each action. For example, 'Click the Submit button' rather than 'Submit the form'.",
            "metadata": {"category": "best_practices", "importance": "medium"},
            "name": "Steps Precision"
        },
        {
            "content": "For complex bugs, consider recording a video that shows the issue occurring. This can be more effective than written steps.",
            "metadata": {"category": "best_practices", "importance": "medium"},
            "name": "Video Evidence"
        },
        {
            "content": "If you encounter an error message, include the exact text of the message in your report.",
            "metadata": {"category": "best_practices", "importance": "high"},
            "name": "Error Messages"
        },
        {
            "content": "Before submitting a new bug report, search existing reports to see if your issue has already been reported.",
            "metadata": {"category": "best_practices", "importance": "medium"},
            "name": "Avoid Duplicates"
        },
        {
            "content": "The following information is required for all bug reports: App version, Device/OS, Steps to reproduce, Expected result, and Actual result.",
            "metadata": {"category": "required_fields", "importance": "high"},
            "name": "Required Fields"
        },
        {
            "content": "App version can be found in the Settings > About section of the application.",
            "metadata": {"category": "required_fields", "importance": "medium"},
            "name": "Finding App Version"
        },
        {
            "content": "When reporting Device/OS information, include both the device model and the operating system version (e.g., iPad Pro 11\" M2, iPadOS 17.4).",
            "metadata": {"category": "required_fields", "importance": "medium"},
            "name": "Device OS Info"
        },
        {
            "content": "Steps to reproduce should include at least 3 specific steps that consistently lead to the bug.",
            "metadata": {"category": "required_fields", "importance": "high"},
            "name": "Steps Minimum"
        },
        {
            "content": "Expected result should clearly state what you expected to happen when following the steps to reproduce.",
            "metadata": {"category": "required_fields", "importance": "medium"},
            "name": "Expected Result Guidance"
        },
        {
            "content": "Actual result should describe exactly what happened instead of the expected result.",
            "metadata": {"category": "required_fields", "importance": "medium"},
            "name": "Actual Result Guidance"
        },
        {
            "content": "All file attachments are scanned for viruses before being processed. Maximum file size is 50MB per file and 3 files total.",
            "metadata": {"category": "attachments", "importance": "medium"},
            "name": "Attachment Limits"
        },
        {
            "content": "Supported attachment types include screenshots (PNG, JPG), screen recordings (MP4, GIF), logs, and .skyset files.",
            "metadata": {"category": "attachments", "importance": "medium"},
            "name": "Supported File Types"
        },
        {
            "content": "For performance issues, please attach a .skyset file if possible. This helps our developers reproduce your exact scenario.",
            "metadata": {"category": "attachments", "importance": "high"},
            "name": "Performance Attachments"
        },
        {
            "content": "Your bug reports are used by our development team to identify, reproduce, and fix issues in our software. They are prioritized based on severity and impact.",
            "metadata": {"category": "usage", "importance": "medium"},
            "name": "How Reports Are Used"
        }
    ]
    
    # Load custom documents
    loader.load_custom_documents(custom_docs)
    print("Sample data loaded successfully")
    
def chat_loop(agent):
    """Run an interactive chat loop with the agent"""
    print("\n===== Bug Reporting Assistant =====")
    print("Ask questions about bug reporting or type 'exit' to quit")
    print("===================================\n")
    
    while True:
        query = input("\nYou: ")
        if query.lower() in ['exit', 'quit', 'bye']:
            print("Goodbye!")
            break
            
        print("\nAssistant: ", end="")
        agent.chat(query)
        
def main():
    parser = argparse.ArgumentParser(description="Bug Reporting Assistant with AstraDB RAG")
    parser.add_argument("--load", action="store_true", help="Load sample data into AstraDB")
    parser.add_argument("--endpoint", default=DEFAULT_ASTRA_DB_API_ENDPOINT, help="AstraDB API endpoint")
    parser.add_argument("--token", default=DEFAULT_ASTRA_DB_TOKEN, help="AstraDB API token")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION_NAME, help="AstraDB collection name")
    
    args = parser.parse_args()
    
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is not set")
        print("Please set it with: export OPENAI_API_KEY=your_api_key")
        return
        
    # Load sample data if requested
    if args.load:
        loader = DocumentLoader(
            collection_name=args.collection,
            api_endpoint=args.endpoint,
            token=args.token
        )
        load_sample_data(loader)
        
    # Create and run the RAG agent
    agent = RAGAgent(
        collection_name=args.collection,
        api_endpoint=args.endpoint,
        token=args.token
    )
    
    # Start chat loop
    chat_loop(agent)
    
if __name__ == "__main__":
    main()