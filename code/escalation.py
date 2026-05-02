import re

def classify_risk(text: str) -> bool:
    """
    Keyword-based fast detection for high-risk topics.
    This is used as a first-pass filter before deeper classification.
    """
    if not text:
        return False
        
    text = text.lower()
    
    # High-risk keywords
    risk_keywords = [
        # Security / Access
        "hacked", "stolen", "compromised", "breach", "security vulnerability",
        "unauthorized access", "identity theft",
        # Financial / Legal
        "fraud", "legal", "lawsuit", "police", "court", "arbitration",
        "chargeback", "dispute a charge", "scam",
        # Urgent System Issues
        "outage", "system down", "completely broken", "major bug", "emergency",
        "urgent", "asap", "restoring access",
        # Dangerous content
        "delete all files", "rm -rf", "exploit"
    ]
    
    for kw in risk_keywords:
        if kw in text:
            return True
            
    return False
