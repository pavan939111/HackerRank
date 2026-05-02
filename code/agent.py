import re
from escalation import classify_risk
from classifier import classify
from retriever import retrieve
from generator import generate_response

def check_context_overlap(response: str, chunks: list[dict], threshold: float = 0.1) -> bool:
    """
    Ensures the response contains words that actually exist in the retrieved context.
    """
    if not response or not chunks:
        return False
        
    res_words = set(re.findall(r'\w+', response.lower()))
    ctx_text = " ".join([c.get("text", "") for c in chunks]).lower()
    ctx_words = set(re.findall(r'\w+', ctx_text))
    
    stop_words = {"the", "a", "an", "and", "or", "to", "of", "in", "is", "at", "it"}
    res_words = res_words - stop_words
    ctx_words = ctx_words - stop_words
    
    if not res_words: return True 
    
    overlap = res_words.intersection(ctx_words)
    overlap_ratio = len(overlap) / len(res_words)
    
    return overlap_ratio >= threshold

def process_ticket(row: dict) -> dict:
    issue = str(row.get("issue", row.get("Issue", "")))
    subject = str(row.get("subject", row.get("Subject", "")))
    company = str(row.get("company", row.get("Company", "")))

    # 1. Category Classification & Risk Assessment (SINGLE LLM CALL)
    classification = classify(issue, subject, company)
    request_type = classification.get("request_type", "product_issue")
    
    # Fast-path risk override (Keywords only, no API call)
    fast_risk = classify_risk(f"{subject} {issue}")
    
    # Final Risk Status from LLM Classification
    risk = classification.get("should_escalate", False) or fast_risk
    
    # 2. BM25 Retrieval & Confidence Check
    query = f"{subject} {issue}".strip()
    retrieval_data = retrieve(query, company, top_k=3)
    chunks = retrieval_data["chunks"]
    
    # --- LAYER 1: Retrieval Guard ---
    no_reliable_context = (retrieval_data["confidence"] == "low")
    # --------------------------------
    
    # 3. Decision Block: Single Source of Truth
    # Rules:
    # - If invalid request -> reply with polite refusal
    # - If risk detected AND no context -> must escalate
    # - If no reliable context -> must escalate
    # - Otherwise -> reply
    
    if request_type == "invalid":
        forced_status = "replied"
    elif risk and no_reliable_context:
        # Escalated due to high risk and lack of specific documentation
        forced_status = "escalated"
    elif no_reliable_context:
        # Escalated due to lack of specific documentation
        forced_status = "escalated"
    else:
        forced_status = "replied"
        
    # 4. Gemini Output Generation
    res = generate_response(issue, subject, company, chunks, classification, no_reliable_context, forced_status)
    
    # --- LAYER 3: Post-Generation Validation ---
    llm_response = res.get("response", "")
    not_enough_info = ("don't have enough information" in llm_response.lower() or 
                       "not clearly present" in llm_response.lower())
    
    has_overlap = True
    if forced_status == "replied" and not not_enough_info:
        has_overlap = check_context_overlap(llm_response, chunks)
        
    if forced_status == "replied" and (not_enough_info or not has_overlap):
        res["status"] = "escalated"
        res["response"] = "We are unable to provide a verified answer from available documentation. A human agent will review your request."
        if not has_overlap:
            res["justification"] = "Escalated due to low context overlap (potential hallucination detected)."
        else:
            res["justification"] = "Escalated due to insufficient relevant documentation."
    # --------------------------------------------
        
    # 5. Final Justification Construction
    final_status = res.get("status", "replied")
    if res.get("justification") and "Escalated" in res["justification"]:
        pass # Keep specific safeguard reason
    elif request_type == "invalid":
        res["justification"] = "Out of scope issue handled with polite refusal."
    elif final_status == "escalated":
        res["justification"] = "Escalated due to insufficient relevant documentation."
    else:
        titles = [c.get("title", "Unknown Source") for c in chunks[:2]]
        unique_titles = list(set([t for t in titles if t]))
        if unique_titles:
            title_list = " * ".join(unique_titles)
            res["justification"] = f"Response based on documentation: * {title_list}. These directly address the user's issue."
        else:
            res["justification"] = "Response based on relevant documentation that directly addresses the user's issue."

    return res
