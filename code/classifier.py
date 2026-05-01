from dotenv import load_dotenv
import os
import json
import time
from google.genai import types
from client_manager import get_client, KEYS

def classify(issue: str, subject: str, company: str) -> dict:
    system_prompt = """You are a classification bot. Classify the support ticket based on issue, subject, and company.
Return JSON ONLY with this schema:
{
  "company": "HackerRank" | "Claude" | "Visa" | "None",
  "request_type": "product_issue" | "feature_request" | "bug" | "invalid",
  "should_escalate": true | false,
  "escalation_reason": "string or empty",
  "product_area": "string - best guess domain area"
}

Escalate IF AND ONLY IF:
- Website/platform completely down or inaccessible
- Fraud, stolen card, financial dispute requiring bank action
- Request to change scores, grades, or evaluation outcomes
- Request to modify another user's account without authorization
- Billing dispute with a payment order ID
- Infosec / compliance / legal form requests
- Requests that require human judgment on sensitive personal data

If out-of-scope (celebrity names, general trivia, non-support topics): set request_type="invalid", should_escalate=false.
"""

    prompt = f"Subject: {subject}\nIssue: {issue}\nCompany: {company}\nClassify this ticket."

    num_retries = len(KEYS)
    for attempt in range(num_retries):
        try:
            client = get_client()
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.0,
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            if attempt == num_retries - 1:
                return {
                    "company": company,
                    "request_type": "invalid",
                    "should_escalate": False,
                    "escalation_reason": str(e),
                    "product_area": "unknown"
                }
            time.sleep(0.5)
