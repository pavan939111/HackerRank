import os
import json
import re
from rank_bm25 import BM25Okapi
from client_manager import get_client
from google.genai import types

_BM25_INDEX = None
_CHUNKS = None

def load_indices():
    global _BM25_INDEX, _CHUNKS
    if _BM25_INDEX is None:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        data_path = os.path.join(base_dir, "data", "processed_chunks.json")
        
        with open(data_path, "r", encoding="utf-8") as f:
            _CHUNKS = json.load(f)
            
        tokenized_chunks = [chunk.get("text", "").lower().split() for chunk in _CHUNKS]
        _BM25_INDEX = BM25Okapi(tokenized_chunks)

def retrieve(query: str, company: str, top_k: int = 3) -> dict:
    load_indices()
    
    comp = str(company).lower().strip()
    tokenized_query = query.lower().split()
    
    if not tokenized_query:
        return {"chunks": [], "scores": [], "confidence": "low"}
        
    scores = _BM25_INDEX.get_scores(tokenized_query)
    
    # 1. Compute Confidence (based on raw BM25)
    top_scores = sorted(scores, reverse=True)[:5]
    avg_top_score = sum(top_scores) / max(len(top_scores), 1)
    
    MIN_TOP_SCORE = 1.0
    MIN_AVG_SCORE = 0.5
    
    confidence = "high"
    if not top_scores or top_scores[0] < MIN_TOP_SCORE or avg_top_score < MIN_AVG_SCORE:
        confidence = "low"
    
    # 2. Select candidates (Top 10) with company boost
    top_10_idx = sorted(range(len(scores)), key=lambda i: (scores[i], -i), reverse=True)[:10]
    
    candidates = []
    for i in top_10_idx:
        chunk = _CHUNKS[i]
        score = scores[i]
        
        chunk_company = str(chunk.get("company", "")).lower().strip()
        if comp and chunk_company == comp:
            score += 1000.0  # Boost for correct company
            
        candidates.append({
            "chunk": chunk,
            "score": score,
            "index": i
        })
        
    # Sort candidates by boosted score
    candidates.sort(key=lambda x: (x["score"], -x["index"]), reverse=True)
    
    # 3. LLM Re-ranking for semantic accuracy
    # Build prompt for re-ranking
    passages_text = ""
    for idx, c in enumerate(candidates):
        snippet = c["chunk"].get("text", "")[:400]
        passages_text += f"{idx + 1}. [Title: {c['chunk'].get('title', 'N/A')}] {snippet}\n\n"

    rerank_prompt = f"""Given the user query and the following candidate passages, rank the top 3 most relevant passages.
Return ONLY the indices (numbers 1-10) of the best 3 passages, comma-separated.

Query: {query}

Passages:
{passages_text}"""

    final_indices = []
    try:
        client = get_client()
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=rerank_prompt,
            config=types.GenerateContentConfig(temperature=0.0)
        )
        # Extract indices
        nums = re.findall(r'\d+', response.text)
        seen = set()
        for n in nums:
            val = int(n) - 1
            if 0 <= val < len(candidates) and val not in seen:
                final_indices.append(val)
                seen.add(val)
    except Exception:
        # Fallback to BM25 order if re-ranking fails
        pass

    # Ensure we have enough indices by filling from BM25 order
    seen = set(final_indices)
    for i in range(len(candidates)):
        if len(final_indices) >= top_k:
            break
        if i not in seen:
            final_indices.append(i)
            seen.add(i)

    final_results = []
    for i in final_indices[:top_k]:
        chunk = candidates[i]["chunk"]
        final_results.append({
            "text": chunk.get("text", ""),
            "title": chunk.get("title", ""),
            "company": chunk.get("company", "")
        })
        
    return {
        "chunks": final_results,
        "scores": [candidates[i]["score"] for i in final_indices[:top_k]],
        "confidence": confidence
    }
