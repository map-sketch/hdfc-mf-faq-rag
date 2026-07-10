from src.embeddings import get_vectorstore
from src.config import RETRIEVAL_TOP_K

# Lower threshold to 0.2 — ChromaDB relevance scores for scraped web content 
# typically range 0.3–0.6; the original 0.7 was filtering everything out.
EFFECTIVE_THRESHOLD = 0.2

def retrieve_context(query: str):
    vectorstore = get_vectorstore()

    results = vectorstore.similarity_search_with_relevance_scores(
        query, k=RETRIEVAL_TOP_K
    )

    assembled_docs = []
    seen_content = set()
    total_chars = 0
    CHAR_LIMIT = 8000  # ~2000 tokens

    for doc, score in results:
        if score >= EFFECTIVE_THRESHOLD:
            if doc.page_content not in seen_content:
                if total_chars + len(doc.page_content) <= CHAR_LIMIT:
                    assembled_docs.append(doc)
                    seen_content.add(doc.page_content)
                    total_chars += len(doc.page_content)
                else:
                    break

    return assembled_docs
