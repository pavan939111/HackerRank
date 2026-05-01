# 🎨 DESIGN.md — Prompt Engineering Evolution

This document tracks the iterative improvement of the prompts used in the Support Triage Agent, demonstrating the shift from naive generation to strict, grounded reasoning.

---

## 🕒 Version 1: Naive Generation
**Prompt Strategy**: Direct question answering.
```text
Subject: {subject}
Issue: {issue}
Context: {context}

Answer the user's issue based on the context.
```
**Issues Identified**:
- **Hallucination**: The model would invent URLs or phone numbers if they weren't in the context.
- **Tone Inconsistency**: Sometimes too casual, sometimes overly verbose.
- **Output Format**: Frequently returned plain text instead of the required JSON schema, breaking the CSV pipeline.

---

## 📈 Version 2: Grounded & Structured
**Prompt Strategy**: Added negative constraints and JSON schema enforcement.
```text
System: Answer ONLY using the provided context chunks. If the answer is not found, say you don't know. Return JSON ONLY.

Context: {context}
...
```
**Improvements**:
- **Grounding**: Significantly reduced hallucination by explicitly forbidding external knowledge.
- **Reliability**: JSON schema usage made the pipeline more stable.
**Remaining Issues**:
- **Ambiguity**: The model would sometimes "guess" an escalation when a valid answer existed in a lower-ranked chunk.
- **Traceability**: Justifications were generic and didn't explain *which* part of the documentation was used.

---

## 🚀 Version 3: Strict, Deterministic & Traceable (Current)
**Prompt Strategy**: Multi-layered constraints, Evidence-based Justification, and Forced Status.
```text
System: You are a support agent for {company}. 
- Never invent policies or steps.
- Keep response under 200 words.
- Instruction: You MUST generate a response where status is "{forced_status}".

Justification Rule: List document titles used for the answer.
```
**Improvements**:
- **Strict Determinism**: By passing a `forced_status` decided by the `agent.py` logic, we ensure the LLM never conflicts with the system's safety-first decision engine.
- **High Auditability**: The justification field now acts as a "Proof of Context," listing exact document titles (e.g., 'Troubleshooting Login Issues...') which ensures judges can verify the grounding instantly.
- **Failure Resilience**: Prompt now includes specific instructions for "No Reliable Context" scenarios, ensuring the model provides a professional hand-off instead of a broken reply.

---

## 🧠 Conclusion
The prompt evolution reflects a shift from **LLM-as-a-Creator** to **LLM-as-a-Reasoner**. By constraining the model's creative freedom and forcing it to cite its sources, we achieved the high accuracy and explainability required for production support triage.
