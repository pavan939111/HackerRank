# 🛠 Agent Codebase

This directory contains the core logic for the Support Triage Agent.

## Modules

*   `main.py`: The entry point that orchestrates the batch processing of tickets.
*   `agent.py`: The central decision engine that coordinates retrieval, classification, and generation.
*   `retriever.py`: Implements BM25 retrieval with semantic re-ranking and confidence thresholding.
*   `generator.py`: Generates user-facing responses grounded strictly in retrieved context.
*   `escalation.py`: Hybrid logic (Keywords + LLM) to detect high-risk or sensitive queries.
*   `classifier.py`: Categorizes tickets into product areas and request types.
*   `client_manager.py`: Manages the pool of API keys and handles round-robin rotation for rate-limit resilience.

## 🛡 Failure Mode Handling & Safeguards

The agent is designed to fail safely when it cannot provide a verified answer:

1.  **Retrieval Guard**: If BM25 scores are below the confidence threshold, the agent automatically escalates.
2.  **Context Overlap Check**: A post-generation check ensures the LLM's response actually uses words from the retrieved documentation.
3.  **Refusal Detection**: If the LLM admits it doesn't have enough info, the system overrides the status to `escalated`.
4.  **Company Mismatch**: Ensures documents belong to the identified company before allowing a "replied" status.

## Determinism

To ensure reproducibility:
- **Temperature**: Set to `0.0` for all Gemini calls.
- **Sorting**: BM25 results use a fixed index tie-breaker to ensure consistent top-K results.
- **Fixed Pipeline**: No random sampling or stochastic components in the orchestration logic.
