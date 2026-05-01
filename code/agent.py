import re
from escalation import classify_risk
from classifier import classify
from retriever import retrieve
from generator import generate_response

def check_context_overlap(response: str, chunks: list[dict], threshold: float = 0.1) -> bool:
    """
    4. Context Overlap Check (Safeguard)
    Ensures the response contains words that actually exist in the retrieved context.
    """
    if not response or not chunks:
        return False
        
    # Simple word-based overlap
    res_words = set(re.findall(r'\w+', response.lower()))
    ctx_text = " ".join([c.get("text", "") for c in chunks]).lower()
    ctx_words = set(re.findall(r'\w+', ctx_text))
    
    # Filter out common stop words to focus on meaningful content
    stop_words = {"the", "a", "an", "and", "or", "to", "of", "in", "is", "at", "it"}
    res_words = res_words - stop_words
    ctx_words = ctx_words - stop_words
    
    if not res_words: return True # Empty response handled elsewhere
    
    overlap = res_words.intersection(ctx_words)
    overlap_ratio = len(overlap) / len(res_words)
    
    return overlap_ratio >= threshold

def process_ticket(row: dict) -> dict:
    issue = str(row.get("Issue", row.get("issue", "")))
    subject = str(row.get("Subject", row.get("subject", "")))
    company = str(row.get("Company", row.get("company", "")))

    # 1. High-risk Escalation check
    risk = classify_risk(f"{subject} {issue}")
    
    # 2. Category Classification
    classification = classify(issue, subject, company)
    
    # 3. BM25 Retrieval & Confidence Check
    query = f"{subject} {issue}".strip()
    retrieval_data = retrieve(query, company, top_k=3)
    chunks = retrieval_data["chunks"]
    
    # --- LAYER 1: Retrieval Guard ---
    no_reliable_context = (retrieval_data["confidence"] == "low")
    # --------------------------------
    
    # 4. Decision Block: Combine Risk + Context Availability
    request_type = classification.get("request_type", "product_issue")
    
    if request_type == "invalid":
        forced_status = "replied"
    elif risk and no_reliable_context:
        forced_status = "escalated"
    elif no_reliable_context:
        forced_status = "escalated"
    else:
        forced_status = "replied"
        
    # 5. Gemini Output Generation (LAYER 2: Generation Constraint inside prompt)
    res = generate_response(issue, subject, company, chunks, classification, no_reliable_context, forced_status)
    
    # --- LAYER 3: Post-Generation Validation ---
    llm_response = res.get("response", "")
    
    # Check A: Missing Information detection
    not_enough_info = ("don't have enough information" in llm_response.lower() or 
                       "not clearly present" in llm_response.lower())
    
    # Check B: Context Overlap (Hallucination Detection)
    # Only check overlap for replies. If overlap is too low, it's likely a hallucination.
    has_overlap = True
    if forced_status == "replied" and not not_enough_info:
        has_overlap = check_context_overlap(llm_response, chunks)
        
    if forced_status == "replied" and (not_enough_info or not has_overlap):
        # Override to safe escalation
        res["status"] = "escalated"
        res["response"] = "We are unable to provide a verified answer from available documentation. A human agent will review your request."
        if not has_overlap:
            res["justification"] = "Escalated due to low context overlap (potential hallucination detected)."
        else:
            res["justification"] = "Escalated due to insufficient relevant documentation."
    # --------------------------------------------
        
    # 6. Final Justification Template Construction
    final_status = res.get("status", "replied")
    if res.get("justification") and "Escalated" in res["justification"]:
        # Keep the specific safeguard justification
        pass
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
