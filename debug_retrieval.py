import json
from src.embeddings import get_vectorstore

vs = get_vectorstore()
results = vs.similarity_search_with_relevance_scores(
    'What is the expense ratio of HDFC Mid Cap Fund?', k=5
)

output = []
for doc, score in results:
    output.append({
        "score": round(score, 4),
        "scheme": doc.metadata.get('scheme_name', 'Unknown'),
        "text": doc.page_content[:120]
    })

with open("data/debug_scores.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"Total results: {len(results)}")
print(f"Scores: {[round(s, 4) for _, s in results]}")
print("Saved full output to data/debug_scores.json")
