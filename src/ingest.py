import os
import datetime
import hashlib
import unicodedata
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.config import GROWW_SCHEME_URLS
from src.scraper import scrape_url
from src.embeddings import get_vectorstore


def generate_chunk_id(url, chunk_index):
    return hashlib.md5(f"{url}_{chunk_index}".encode()).hexdigest()


def get_scheme_name_from_url(url):
    return url.split('/')[-1].replace('-', ' ').title()


def sanitize_text(text: str) -> str:
    """Replace non-ASCII / problematic unicode chars with safe equivalents."""
    # Replace common unicode chars that cause encoding issues
    replacements = {
        '\u20b9': 'INR ',   # ₹ Rupee sign
        '\u2013': '-',      # En dash
        '\u2014': '-',      # Em dash
        '\u2018': "'",      # Left single quote
        '\u2019': "'",      # Right single quote
        '\u201c': '"',      # Left double quote
        '\u201d': '"',      # Right double quote
        '\u2022': '*',      # Bullet
        '\u00a0': ' ',      # Non-breaking space
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    # Normalize any remaining unicode to closest ASCII
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')


def process_and_ingest():
    vectorstore = get_vectorstore()

    # Wipe existing collection so re-runs don't duplicate data
    try:
        vectorstore._collection.delete(
            where={"scheme_name": {"$ne": "__nonexistent__"}}
        )
        print("Cleared existing vectorstore entries.")
    except Exception as e:
        print(f"Note: Could not clear collection (may be empty): {e}")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=50,
        length_function=len,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    all_documents = []

    print("Starting data ingestion process...")
    for url in GROWW_SCHEME_URLS:
        print(f"\nScraping {url}...")
        text_content = scrape_url(url)
        if not text_content:
            print(f"Failed to scrape content for {url}. Skipping.")
            continue

        # Sanitize text before chunking to avoid unicode issues downstream
        text_content = sanitize_text(text_content)

        print(f"Chunking content for {url}...")
        chunks = text_splitter.split_text(text_content)

        scheme_name = get_scheme_name_from_url(url)
        scrape_date = datetime.datetime.now().strftime("%Y-%m-%d")

        for i, chunk in enumerate(chunks):
            metadata = {
                "chunk_id": generate_chunk_id(url, i),
                "scheme_name": scheme_name,
                "source_url": url,
                "scrape_date": scrape_date
            }
            doc = Document(page_content=chunk, metadata=metadata)
            all_documents.append(doc)

    print(f"\nTotal chunks created: {len(all_documents)}")

    if all_documents:
        print("Saving embeddings to ChromaDB...")
        vectorstore.add_documents(documents=all_documents)
        vectorstore.persist() if hasattr(vectorstore, 'persist') else None
        print("Vector store successfully updated and persisted!")
    else:
        print("No documents to ingest.")


if __name__ == "__main__":
    process_and_ingest()
