import os
import json
from src.embeddings import get_vectorstore

def view_embeddings():
    print("Connecting to Vector Store...")
    vectorstore = get_vectorstore()
    
    # Get the underlying chromadb collection to fetch raw embeddings
    collection = vectorstore._collection
    
    # Retrieve everything (documents, metadatas, embeddings)
    result = collection.get(include=['documents', 'metadatas', 'embeddings'])
    
    documents = result.get('documents', [])
    metadatas = result.get('metadatas', [])
    embeddings = result.get('embeddings', [])
    ids = result.get('ids', [])
    
    print(f"Total chunks found in ChromaDB: {len(documents)}")
    
    if len(documents) == 0:
        print("No embeddings found. Please make sure data has been successfully ingested.")
        return
        
    output_data = []
    
    for i in range(len(documents)):
        emb = embeddings[i]
        # Show only first 5 dimensions for readability in console
        truncated_emb = emb[:5]
        
        print(f"\n--- Chunk {i+1} ---")
        print(f"ID: {ids[i]}")
        print(f"Scheme: {metadatas[i].get('scheme_name', 'Unknown')}")
        print(f"Embedding Length: {len(emb)}")
        print(f"Embedding (first 5 dims): {truncated_emb} ...")
        print(f"Text Preview: {documents[i][:100]}...")
        
        output_data.append({
            "chunk_id": ids[i],
            "scheme_name": metadatas[i].get('scheme_name'),
            "source_url": metadatas[i].get('source_url'),
            "scrape_date": metadatas[i].get('scrape_date'),
            "text": documents[i],
            "embedding_sample_5_dims": truncated_emb,
            "embedding_total_length": len(emb)
        })
        
    output_file = os.path.join("data", "embeddings_view.json")
    os.makedirs("data", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)
        
    print(f"\nDetailed verification data containing text, metadata, and embedding dimensions saved to {output_file}")

if __name__ == "__main__":
    view_embeddings()
