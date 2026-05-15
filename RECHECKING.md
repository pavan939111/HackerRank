# System Verification (Hybrid Alignment)

This document outlines how to verify the system matches the **Hybrid Retrieval Architecture**.

### 1. Hybrid Retrieval Check
In `code/retriever.py`, ensure the `retrieve` function utilizes both `BM25Retriever` and `vector_retriever`. The fusion mode should be `reciprocal_rerank` to maintain determinism.

### 2. Structured Ingestion Check
In `code/preprocess.py`, verify the `DoclingProcessor` is used to extract YAML metadata and clean the document hierarchy. Check `code/storage/chunks.json` to ensure chunks are properly stored.

### 3. Safety Thresholds
Check `code/config.py` for retrieval and validation thresholds:
- `MIN_SCORE`: Gating for retrieval confidence.
- `MIN_OVERLAP`: Grounding verification.

### 4. Stage Logging
Run a single ticket through `main.py` and observe the terminal logs. You should see 7 distinct stages:
1. Safety -> 2. Classification -> 3. Retrieval -> 4. Validation -> 5. Generation -> 6. Decision -> 7. Assembly.
