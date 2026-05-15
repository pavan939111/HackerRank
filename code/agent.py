import re
from escalation import classify_risk
from classifier import classify
from retriever import retrieve
from generator import generate_response
from validate import is_context_valid, validate_response
from config import ESCALATION_OVERRIDE_MSG

def process_ticket(row: dict) -> dict:
    issue = str(row.get("issue", row.get("Issue", "")))
    subject = str(row.get("subject", row.get("Subject", "")))
    company = str(row.get("company", row.get("Company", "")))

    print(f"\n--- 🚀 PROCESSING PIPELINE START [Company: {company}] ---")

    # STAGE 1: Safety Layer (Risk Assessment)
    print("🛡️ [STAGE 1] Safety Filter...")
    fast_risk = classify_risk(f"{subject} {issue}")
    
    # STAGE 2: Classification Layer
    print("🧠 [STAGE 2] Classification...")
    classification = classify(issue, subject, company)
    request_type = classification.get("request_type", "product_issue")
    risk = classification.get("should_escalate", False) or fast_risk
    
    # STAGE 3: Structured Retrieval (Hybrid)
    print("🔍 [STAGE 3] Structured Retrieval...")
    query = f"{subject} {issue}".strip()
    retrieval_data = retrieve(query, company)
    chunks = retrieval_data["chunks"]
    
    # STAGE 4: Context Validation
    print("✅ [STAGE 4] Context Validation...")
    context_is_valid = is_context_valid(chunks)
    no_reliable_context = (retrieval_data["confidence"] == "low" or not context_is_valid)
    
    # STAGE 5: Response Generation (Grounded)
    # Decision Block for Status
    if request_type == "invalid":
        forced_status = "replied"
        escalation_reason = None
    elif not context_is_valid:
        forced_status = "escalated"
        escalation_reason = "Context invalid or insufficient"
    elif retrieval_data["confidence"] == "low":
        forced_status = "escalated"
        escalation_reason = f"Low retrieval confidence (Top Score: {retrieval_data.get('top_score', 0):.2f})"
    elif risk:
        forced_status = "escalated"
        escalation_reason = "High risk ticket detected"
    else:
        forced_status = "replied"
        escalation_reason = None

    print(f"🤖 [STAGE 5] Response Generation (Status: {forced_status})...")
    res = generate_response(issue, subject, company, chunks, classification, no_reliable_context, forced_status)
    
    # STAGE 6: Decision Engine (Post-Generation Check)
    print("⚖️ [STAGE 6] Decision Engine / Validation...")
    llm_response = res.get("response", "")
    if forced_status == "replied":
        is_valid, validation_reason = validate_response(llm_response, chunks)
        if not is_valid:
            print(f"  🚨 Validation Failure: {validation_reason}")
            res["status"] = "escalated"
            res["response"] = ESCALATION_OVERRIDE_MSG
            res["justification"] = f"Escalated due to post-generation validation failure: {validation_reason}"
            return res
        
    # STAGE 7: Output Assembly
    print("📝 [STAGE 7] Output Assembly...")
    final_status = res.get("status", "replied")
    confidence_str = f"Confidence: {retrieval_data['confidence']}"
    
    if request_type == "invalid":
        res["justification"] = "Out of scope issue handled with polite refusal."
    elif final_status == "escalated":
        res["justification"] = f"Escalated: {escalation_reason or 'Internal safety check'}. {confidence_str}."
    else:
        titles = [c.get("title", "Unknown Source") for c in chunks[:2]]
        unique_titles = list(set([t for t in titles if t]))
        source_info = f"Sources: {', '.join(unique_titles)}" if unique_titles else "verified documentation"
        res["justification"] = f"Response based on {source_info}. {confidence_str}."

    print("--- ✅ PIPELINE COMPLETE ---\n")
    return res
