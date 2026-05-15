# Multi-Domain AI Support Triage Agent
## Hybrid Retrieval + Safety-First Decision Engine

A production-oriented AI agent built to process support tickets across multiple domains (HackerRank, Claude, Visa). The system leverages **Hybrid Retrieval** (BM25 + Semantic Similarity) and **Deterministic Safety Controls** to ensure grounded, high-accuracy responses.

### 🚀 Key Features
- **Hybrid Retrieval**: Combines keyword precision (BM25) with semantic intent (Embeddings) for robust knowledge retrieval.
- **Docling-Inspired Parsing**: Structured document ingestion that preserves hierarchy and metadata.
- **7-Stage Sequential Pipeline**: A modular architecture that separates safety, classification, retrieval, and validation.
- **Hallucination Prevention**: Integrated lexical overlap validation and vague-phrase detection.
- **No Vector DB Complexity**: Efficient in-memory similarity search and local index persistence.

### 🏗️ System Architecture
The system follows a strict sequential flow:
1. **Safety Layer**: Immediate detection of high-risk fraud or system outages.
2. **Classification**: Intent mapping and domain detection via Gemini 1.5 Flash.
3. **Hybrid Retrieval**: Score-fused retrieval across structured documents.
4. **Context Validation**: Safety checks for context quality and relevance.
5. **Generation**: Grounded response synthesis.
6. **Decision Engine**: Final arbitration: Reply vs. Human Escalation.
7. **Output Assembly**: Structured CSV persistence.

### 🛠️ Why Hybrid Retrieval?
Pure BM25 can miss nuanced semantic matches, while pure semantic search can be "fuzzy" and miss specific error codes. Our **Hybrid Engine** ensures:
- **Precision**: Exact terminology match via BM25.
- **Recall**: Semantic intent match via Embedding similarity.
- **Stability**: Deterministic score fusion (Reciprocal Rerank).

### 🛡️ Safety Controls
The system is built on an **Escalation-First** philosophy. If retrieval confidence is low or validation fails, the system automatically escalates to a human agent rather than risking an unverified answer.

---
*Built for HackerRank Orchestrate 2026*