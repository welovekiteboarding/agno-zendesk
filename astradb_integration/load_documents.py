"""
Script to load documents into AstraDB for RAG
"""

import os
import sys
from document_loader import DocumentLoader

def main():
    # AstraDB configuration
    ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_ENDPOINT", "your_astra_endpoint")
    ASTRA_DB_TOKEN = os.getenv("ASTRA_TOKEN", "your_astra_token")
    COLLECTION_NAME = "ss_guide"
    
    # Create document loader
    loader = DocumentLoader(
        collection_name=COLLECTION_NAME,
        api_endpoint=ASTRA_DB_API_ENDPOINT,
        token=ASTRA_DB_TOKEN
    )
    
    # Example custom documents (modify as needed)
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
        }
    ]
    
    # Load custom documents
    loader.load_custom_documents(custom_docs)
    
    # If you have text files to load
    # text_directory = "path/to/text/files"
    # loader.load_text_files(text_directory)
    
    # If you have PDF files to load
    # pdf_directory = "path/to/pdf/files"
    # loader.load_pdf_files(pdf_directory)
    
    # If you have CSV files to load
    # csv_directory = "path/to/csv/files"
    # loader.load_csv_files(csv_directory)
    
    # If you have websites to load
    # website_urls = ["https://example.com", "https://example.org"]
    # loader.load_websites(website_urls)
    
    # If you have a JSON file to load
    # json_file = "path/to/data.json"
    # loader.load_json(json_file, text_field="content", metadata_fields=["category", "tags"])
    
    print("Document loading complete")

if __name__ == "__main__":
    main()