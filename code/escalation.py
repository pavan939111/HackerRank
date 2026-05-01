import os
from google.genai import types
from client_manager import get_client, KEYS

# FAST PATH: Keywords that indicate immediate high risk
CRITICAL_KEYWORDS = [
    "fraud", "unauthorized", "stolen", "chargeback",
    "hacked", "compromised", "breach",
    "gdpr", "legal", "lawsuit", "sue",
    "outage", "site down", "critical failure"
]

def classify_risk(issue: str) -> bool:
    """
    Hybrid escalation logic:
    1. Fast keyword check for obvious high-risk cases.
    2. LLM reasoning for ambiguous or complex scenarios.
    """
    text = issue.lower()
    
    # Fast path: Obvious critical issues
    if any(word in text for word in CRITICAL_KEYWORDS):
        return True
        
    # Ambiguous path: Use Gemini reasoning
    prompt = f"""Determine if this support ticket requires human escalation.
Human escalation is required for:
- Financial fraud or security breaches
- Legal threats or compliance violations
- Major system outages affecting many users
- Complex issues requiring sensitive human judgment

Return ONLY:
ESCALATE or REPLY

Ticket:
{issue}"""

    num_retries = len(KEYS)
    for attempt in range(num_retries):
        try:
            client = get_client()
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0)
            )
            if response.text and "ESCALATE" in response.text.upper():
                return True
            return False # Definitely a reply case if the model says so
        except Exception:
            if attempt == num_retries - 1:
                return False # Default to reply (safe path) on total failure
            continue
            
    return False
