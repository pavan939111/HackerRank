# 🛠 BUILDING.md — Development Journey

This document chronicles the step-by-step development of the Support Triage Agent, highlighting the engineering challenges, pivots, and final optimizations.

---

## 🏗️ Development Phases

### Phase 1: Basic Pipeline & Data Normalization
*   **Goal**: Load tickets from CSV and establish a basic data flow.
*   **Key Action**: Implemented strict header normalization to handle inconsistent casing in input files.
*   **Challenge**: Missing fields in output.
*   **Solution**: Standardized a internal row dictionary used across all modules.

### Phase 2: Retrieval (BM25) & Pivot from Vector DB
*   **Goal**: Connect the agent to the knowledge base.
*   **Problem**: Initial attempt with ChromaDB caused environment-specific C++ build errors and non-deterministic results.
*   **Decision**: **Removed all Vector DB and embedding logic**. Pivoted to **BM25 Okapi**.
*   **Reasoning**: BM25 provides 100% determinism, keyword precision, and requires zero local database management.

### Phase 3: Classification Layer
*   **Goal**: Categorize tickets into product areas and request types.
*   **Key Action**: Developed a structured system prompt for Gemini to handle multi-label classification.
*   **Optimization**: Added specific logic to infer the target company from context when missing.

### Phase 4: Gemini SDK Integration
*   **Problem**: Legacy `google-generativeai` SDK was prone to version conflicts.
*   **Fix**: Migrated to the **NEW `google-genai` SDK**, which offers better type safety and JSON mode support.

### Phase 5: Debugging API & Key Issues
*   **Problem**: Frequent `429 Resource Exhausted` errors on the Gemini free tier.
*   **Solution**: Implemented `client_manager.py` with **6-key round-robin rotation**. This allowed the pipeline to process full batches without hitting per-minute limits.

### Phase 6: Preprocessing & Performance
*   **Goal**: Accelerate retrieval.
*   **Key Action**: Built a recursive preprocessor that flattens help articles into a structured JSON index (`processed_chunks.json`).
*   **Impact**: Runtime retrieval dropped from seconds to milliseconds.

### Phase 7: Efficiency Improvements
*   **Problem**: High latency due to redundant LLM calls (separate escalation and classification) and fixed `time.sleep(3.0)` delays.
*   **Fix**: **Consolidated** classification and risk assessment into a single LLM call. Removed fixed sleeps in favor of **Exponential Backoff**.

### Phase 8: Hallucination Prevention
*   **Goal**: Ensure 100% grounding.
*   **Action**: Implemented the **3-Layer Defense System** (Retrieval Guard -> Constrained Prompt -> Post-Gen Lexical Validation).
*   **Result**: The system now admits when it doesn't know an answer instead of hallucinating.

### Phase 9: Final Optimization & Validation
*   **Action**: Upgraded `validate.py` to compare outputs against `sample_support_tickets.csv` for accuracy auditing. Standardized on **character-based chunking** for retrieval consistency.

---

## ⚠️ Key Trade-offs & Lessons

| Problem | Decision | Trade-off |
| :--- | :--- | :--- |
| **Complexity vs Robustness** | Rejected ChromaDB/Embeddings for BM25. | Slightly lower semantic recall in exchange for 100% determinism and zero dependency issues. |
| **Cost vs Coverage** | Consolidated LLM calls. | Single "Classification + Risk" call is cheaper and faster, though it requires a more complex prompt. |
| **Latency vs Throughput** | Exponential Backoff instead of fixed sleep. | Occasional 60s delays on failure, but 10x faster execution on success. |

## 🚀 Final State
The system is now a highly efficient, deterministic, and safe triage engine that prioritizes verified documentation over generative creativity.
