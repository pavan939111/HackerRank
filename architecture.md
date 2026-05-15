# Technical Architecture: Hybrid Support Triage System

## Philosophy
The system is built on **Hybrid Retrieval with Deterministic Safety Controls**. It uses semantic similarity for better "recall" (understanding intent) and BM25 for "precision" (matching specific terms).

## Sequential Pipeline Flow
1. **Safety Layer (`escalation.py`)**: Keyword-based risk detection.
2. **Classification Layer (`classifier.py`)**: Intent and domain area detection using Gemini 1.5 Flash.
3. **Hybrid Retrieval Layer (`retriever.py`)**:
    - BM25 Score + Embedding Similarity.
    - Reciprocal Rerank Score Fusion.
    - Result: `Confidence: High/Low`.
4. **Context Validation (`validate.py`)**: Checks for grounding and vague language.
5. **Response Generation (`generator.py`)**: Grounded generation with strict context constraints.
6. **Decision Engine (`agent.py`)**: Final arbitration on escalation vs response.
7. **Output Assembly (`main.py`)**: CSV persistence.

## Document Preparation Pipeline
- **Docling Parser**: Hierarchical parsing.
- **Intelligent Chunking**: Section-aware partitioning.
- **Local Indexing**: Persistent storage in JSON/Matrix format (No external DB).

## Safety & Grounding
Safety is not a feature; it is the foundation. Every response is validated using **Lexical Overlap** against the retrieved source. If the grounding ratio is below the threshold, the system triggers an automatic escalation override.
