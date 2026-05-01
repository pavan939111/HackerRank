# 🛠 BUILDING.md — Development Log

## 🧱 Development Phases

### Phase 1: Pipeline & Data Normalization
- **Problem**: Inconsistent CSV headers and missing input fields in output.
- **Fix**: Implemented strict lowercase normalization (`df.columns.str.lower()`) and preserved `issue/subject/company` throughout the `agent.py` flow.

### Phase 2: BM25 Transition
- **Decision**: Removed ChromaDB and vector embeddings.
- **Why**: Complexity was too high for a localized hackathon corpus. BM25 provides better determinism and easier local deployment without environment-specific C++ dependencies.

### Phase 3: Hallucination Guards
- **Problem**: Model would "guess" answers when documentation was missing.
- **Fix**: Implemented the **3-Layer Defense** (Retrieval Guard -> Prompt Constraint -> Overlap Check). This moved the system from a "Chatbot" to a "Verified Triage Engine."

### Phase 4: API Key Resilience
- **Problem**: 429 Rate Limits on free tier.
- **Fix**: Developed `client_manager.py` to handle 6-key round-robin rotation, ensuring the agent remains functional during batch processing.

## ⚠️ Key Problems & Iterations

| Problem | Decision | Trade-off |
| :--- | :--- | :--- |
| **Silent Failures** | Added row-level try/except + debug prints | Slightly slower execution, much better auditability. |
| **Cross-Pollination** | Added +1000.0 Company Boost | May occasionally miss a highly relevant chunk from a "general" category. |
| **Vector Accuracy** | Added LLM-based Re-ranking | Replaces vector DB logic with semantic LLM filtering (top 10 candidates). |

## 🚀 Final Summary
The project evolved from a standard RAG template to a **highly deterministic, safety-critical pipeline** optimized for terminal-based evaluation.
