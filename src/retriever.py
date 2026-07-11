from src.embeddings import get_vectorstore
from src.config import RETRIEVAL_TOP_K

EFFECTIVE_THRESHOLD = 0.2
MULTI_FUND_K = 25
MAX_CHUNKS_PER_FUND = 3
CHAR_LIMIT = 10000  # ~2500 tokens


# Keywords that signal the user wants data across all funds
MULTI_FUND_KEYWORDS = [
    "all funds", "all the funds", "every fund", "each fund",
    "all schemes", "list", "compare", "your database"
]

# Keywords that indicate a key-facts query (expense ratio, NAV, AUM etc.)
KEY_FACTS_KEYWORDS = [
    "expense ratio", "nav", "net asset value", "aum", "fund size",
    "minimum sip", "minimum investment", "exit load", "stamp duty",
    "risk rating", "benchmark"
]


def _is_multi_fund_query(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in MULTI_FUND_KEYWORDS)


def _is_key_facts_query(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in KEY_FACTS_KEYWORDS)


def _get_key_facts_chunks(vectorstore, query: str, scheme_filter: str = None):
    """
    For key-facts queries (expense ratio, NAV etc.), also do a direct keyword
    search to ensure the top-of-page summary chunk (which has the actual values)
    is always included even if its embedding score is lower.
    """
    # Build a direct keyword query targeting the summary section
    supplemental_queries = [
        "Expense ratio NAV Fund size AUM Minimum SIP",
        "expense ratio %",
    ]
    bonus_docs = []
    seen = set()

    for sq in supplemental_queries:
        results = vectorstore.similarity_search_with_relevance_scores(sq, k=10)
        for doc, score in results:
            if score < EFFECTIVE_THRESHOLD:
                continue
            if scheme_filter and scheme_filter.lower() not in doc.metadata.get("scheme_name", "").lower():
                continue
            if doc.page_content not in seen:
                seen.add(doc.page_content)
                bonus_docs.append(doc)

    return bonus_docs


def _detect_scheme_from_query(query: str) -> str | None:
    """Try to detect which specific fund the user is asking about."""
    q = query.lower()
    scheme_map = {
        "mid cap": "Mid Cap",
        "silver": "Silver",
        "equity": "Equity",
        "defence": "Defence",
        "gold": "Gold",
    }
    for keyword, scheme in scheme_map.items():
        if keyword in q:
            return scheme
    return None


def retrieve_context(query: str):
    vectorstore = get_vectorstore()

    is_multi = _is_multi_fund_query(query)
    is_key_facts = _is_key_facts_query(query)
    scheme = _detect_scheme_from_query(query)

    k = MULTI_FUND_K if is_multi else RETRIEVAL_TOP_K

    results = vectorstore.similarity_search_with_relevance_scores(query, k=k)

    assembled_docs = []
    seen_content = set()
    fund_chunk_count: dict[str, int] = {}
    total_chars = 0

    # For key-facts queries on a specific fund, inject the summary chunk first
    if is_key_facts and not is_multi:
        bonus = _get_key_facts_chunks(vectorstore, query, scheme_filter=scheme)
        for doc in bonus:
            if doc.page_content not in seen_content:
                if total_chars + len(doc.page_content) <= CHAR_LIMIT:
                    assembled_docs.insert(0, doc)   # prepend so LLM sees it first
                    seen_content.add(doc.page_content)
                    fund = doc.metadata.get("scheme_name", "Unknown")
                    fund_chunk_count[fund] = fund_chunk_count.get(fund, 0) + 1
                    total_chars += len(doc.page_content)

    # Regular similarity-scored results
    for doc, score in results:
        if score < EFFECTIVE_THRESHOLD:
            continue

        content = doc.page_content
        if content in seen_content:
            continue

        fund = doc.metadata.get("scheme_name", "Unknown")

        # For multi-fund queries cap chunks per fund
        if is_multi and fund_chunk_count.get(fund, 0) >= MAX_CHUNKS_PER_FUND:
            continue

        if total_chars + len(content) > CHAR_LIMIT:
            break

        assembled_docs.append(doc)
        seen_content.add(content)
        fund_chunk_count[fund] = fund_chunk_count.get(fund, 0) + 1
        total_chars += len(content)

    return assembled_docs
