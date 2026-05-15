import os
import json
import time
from pathlib import Path
from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

from config import TOP_K, FINAL_K, MIN_SCORE

# Architecture Constraint: No LLM for retrieval fusion
Settings.llm = None

# Global variable for index cache
_index = None

def load_index():
    global _index
    if _index is not None:
        return _index
        
    base_dir = Path(__file__).resolve().parent.parent
    storage_dir = base_dir / "code" / "storage"
    
    if not storage_dir.exists():
        raise FileNotFoundError(f"Storage directory not found at {storage_dir}. Run preprocess.py first.")
        
    # Use local embedding model for semantic retrieval
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    Settings.embed_model = embed_model
    
    storage_context = StorageContext.from_defaults(persist_dir=str(storage_dir))
    _index = load_index_from_storage(storage_context)
    return _index

def retrieve(query: str, company: str, top_k: int = TOP_K) -> dict:
    """
    HYBRID RETRIEVAL ENGINE (BM25 + Semantic Similarity)
    Implements Score Fusion with Deterministic Safety Controls.
    """
    index = load_index()
    
    # 1. Company-Aware Metadata Filtering
    filters = MetadataFilters(filters=[
        ExactMatchFilter(key="company", value=company.lower())
    ])
    
    # 2. Hybrid Components
    # BM25 (Keyword Precision)
    bm25_retriever = BM25Retriever.from_defaults(
        index=index, 
        similarity_top_k=top_k,
        filters=filters
    )
    
    # Vector (Semantic Intent - Semantic Similarity)
    vector_retriever = index.as_retriever(
        similarity_top_k=top_k,
        filters=filters
    )
    
    # 3. Hybrid Score Fusion (Reciprocal Rerank)
    # Using 1 query to maintain determinism
    retriever = QueryFusionRetriever(
        [bm25_retriever, vector_retriever],
        similarity_top_k=top_k,
        num_queries=1,
        mode="reciprocal_rerank",
        use_async=False
    )
    
    nodes_with_scores = retriever.retrieve(query)
    
    # 4. Confidence Gating & Logging
    print(f"\n⚡ [HYBRID RETRIEVAL] Query: '{query}' | Target: {company}")
    final_chunks = []
    
    for node_with_score in nodes_with_scores:
        score = node_with_score.score
        
        # Deterministic Safety Check
        if score < MIN_SCORE:
            print(f"  ❌ Filtered (Low Rank): {node_with_score.node.metadata.get('title')} [{score:.4f}]")
            continue
            
        node = node_with_score.node
        final_chunks.append({
            "text": node.get_content(),
            "company": node.metadata.get("company", ""),
            "title": node.metadata.get("title", "Untitled"),
            "url": node.metadata.get("url", ""),
            "score": score
        })
        print(f"  ✅ Accepted: {node.metadata.get('title')} [Score: {score:.4f}]")
    
    # Limit to Top K
    final_chunks = final_chunks[:FINAL_K]
    
    # 5. Hybrid Confidence Calculation
    top_score = nodes_with_scores[0].score if nodes_with_scores else 0.0
    confidence = "high" if final_chunks and top_score >= MIN_SCORE else "low"
    
    return {
        "chunks": final_chunks,
        "confidence": confidence,
        "top_score": top_score,
        "method": "hybrid_reciprocal_rerank"
    }
