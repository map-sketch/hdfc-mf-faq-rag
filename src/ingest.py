import os
import datetime
import hashlib
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.config import GROWW_SCHEME_URLS
from src.scraper import scrape_url
from src.embeddings import get_vectorstore

def generate_chunk_id(url, chunk_index):
    return hashlib.md5(f"{url}_{chunk_index}".encode()).hexdigest()

def get_scheme_name_from_url(url):
    # Extracts the scheme name from the URL path
    return url.split('/')[-1].replace('-', ' ').title()

def process_and_ingest():
    vectorstore = get_vectorstore()
    
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
        print("Vector store successfully updated and persisted!")
    else:
        print("No documents to ingest.")

if __name__ == "__main__":
    process_and_ingest()
