import json
import os
import time
from pathlib import Path
from rank_bm25 import BM25Okapi
from google.genai import types
from client_manager import get_client, KEYS

# Global variables for caching the index
_bm25_index = None
_all_chunks = None

def load_data():
    global _bm25_index, _all_chunks
    if _bm25_index is not None:
        return _bm25_index, _all_chunks
        
    base_dir = Path(__file__).resolve().parent.parent
    data_file = base_dir / "data" / "processed_chunks.json"
    
    if not data_file.exists():
        raise FileNotFoundError(f"Processed chunks not found at {data_file}. Run preprocess.py first.")
        
    with open(data_file, "r", encoding="utf-8") as f:
        _all_chunks = json.load(f)
        
    # Tokenize for BM25
    tokenized_corpus = [c["text"].lower().split() for c in _all_chunks]
    _bm25_index = BM25Okapi(tokenized_corpus)
    return _bm25_index, _all_chunks

def retrieve(query: str, company: str, top_k: int = 3) -> dict:
    bm25, chunks = load_data()
    
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)
    
    # 1. Company-based Score Boosting (+1000.0)
    for i, chunk in enumerate(chunks):
        if chunk["company"].lower() == company.lower():
            scores[i] += 1000.0
            
    # 2. Get top 10 candidates for LLM re-ranking
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:10]
    candidates = [chunks[i] for i in top_indices]
    
    # 3. Confidence Metrics (Strictly BM25-based)
    top_score = scores[top_indices[0]] - (1000.0 if chunks[top_indices[0]]["company"].lower() == company.lower() else 0)
    avg_top_5 = sum(scores[top_indices[:5]]) / 5
    avg_top_5_unboosted = avg_top_5 - 1000.0 # Conservative
    
    # Confidence Heuristic
    confidence = "high"
    if top_score < 1.0 or avg_top_5_unboosted < 0.5:
        confidence = "low"
        
    # 4. LLM Re-ranking (Semantic Filter)
    system_prompt = """You are a retrieval assistant. Select the indices of the MOST RELEVANT chunks for the user issue.
Return JSON ONLY: {"top_indices": [index1, index2, index3]}
Indices correspond to the candidate list (0-9).
"""
    prompt = f"User Issue: {query}\n\nCandidates:\n"
    for i, c in enumerate(candidates):
        prompt += f"[{i}] (Title: {c['title']}) {c['text'][:200]}...\n"

    final_chunks = candidates[:top_k] # Default fallback
    
    num_retries = len(KEYS)
    for attempt in range(num_retries):
        try:
            client = get_client()
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.0,
                    response_mime_type="application/json"
                )
            )
            data = json.loads(response.text)
            llm_indices = data.get("top_indices", [])
            final_chunks = [candidates[i] for i in llm_indices if i < len(candidates)][:top_k]
            break
        except Exception:
            if attempt == num_retries - 1:
                break
            time.sleep(2 ** attempt)

    return {
        "chunks": final_chunks,
        "confidence": confidence,
        "top_score": top_score
    }
