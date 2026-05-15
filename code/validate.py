import re
from config import MIN_OVERLAP, VAGUE_PHRASES, REFUSAL_PHRASE

def is_context_valid(chunks: list[dict]) -> bool:
    """
    Checks if the retrieved context is sufficient for generating a response.
    """
    if not chunks:
        print("[VALIDATION] Context check failed: No chunks retrieved.")
        return False
        
    # Rules:
    # 1. No empty chunks
    # 2. Sufficient text length (> 100 chars for at least one chunk)
    # 3. All chunks must have content
    has_strong_chunk = False
    for chunk in chunks:
        text = chunk.get("text", "").strip()
        if not text:
            print("[VALIDATION] Context check failed: Found empty chunk.")
            return False
        if len(text) > 100:
            has_strong_chunk = True
            
    if not has_strong_chunk:
        print("[VALIDATION] Context check failed: No chunks with sufficient length (>100 chars).")
        return False
        
    return True

def validate_response(response: str, chunks: list[dict]) -> tuple[bool, str]:
    """
    Validates the generated response for grounding and clarity.
    Returns (is_valid, reason)
    """
    if not response:
        return False, "Empty response"
        
    if REFUSAL_PHRASE.lower() in response.lower():
        return True, "Handled refusal"

    # 1. Check for vague phrases
    found_vague = [p for p in VAGUE_PHRASES if p in response.lower()]
    if found_vague:
        return False, f"Response contains vague language: {found_vague}"

    # 2. Check for lexical overlap (Grounding)
    res_words = set(re.findall(r'\w+', response.lower()))
    ctx_text = " ".join([c.get("text", "") for c in chunks]).lower()
    ctx_words = set(re.findall(r'\w+', ctx_text))
    
    # Filter common stop words
    stop_words = {"the", "a", "an", "and", "or", "to", "of", "in", "is", "at", "it", "with", "for", "on"}
    res_words = res_words - stop_words
    ctx_words = ctx_words - stop_words
    
    if not res_words:
        return True, "No meaningful content to validate"
        
    overlap = res_words.intersection(ctx_words)
    overlap_ratio = len(overlap) / len(res_words) if res_words else 0
    
    if overlap_ratio < MIN_OVERLAP:
        return False, f"Low context overlap ({overlap_ratio:.2f} < {MIN_OVERLAP})"
        
    return True, "Validation successful"
