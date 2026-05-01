from dotenv import load_dotenv
import os
import json
import time
from google.genai import types
from client_manager import get_client, KEYS

def generate_response(issue: str, subject: str, company: str, chunks: list[dict], classification: dict, no_reliable_context: bool = False, forced_status: str = "replied") -> dict:
    # 2. Generation Constraint (PROMPT LEVEL)
    system_prompt = f"""You are a support agent for {company}. Answer ONLY using the provided context chunks.

DO NOT:
- Use external knowledge
- Assume missing information
- Invent policies, URLs, or phone numbers
- Generalize beyond the provided documentation

IF the answer is not clearly present in the context, you MUST respond EXACTLY:
'I don't have enough information to answer this based on the provided documentation.'

If status is "escalated", write a polite message explaining that you are escalating the issue to a human specialist.
If status is "replied", be direct and helpful based ONLY on context.

Return JSON ONLY:
{{
  "status": "{forced_status}",
  "product_area": "{classification.get('product_area', 'general')}",
  "response": "string - user-facing answer",
  "justification": "string - internal reasoning",
  "request_type": "{classification.get('request_type', 'product_issue')}"
}}
"""

    context_str = ""
    if no_reliable_context:
        # 1. Retrieval Guard (Integration)
        # If we already know context is unreliable, we don't provide any chunks to the model
        context_str = "\n[SYSTEM WARNING: NO RELIABLE CONTEXT FOUND. DO NOT ATTEMPT TO ANSWER THE ISSUE.]\n"
    else:
        for i, c in enumerate(chunks):
            context_str += f"\n[CONTEXT {i+1}]\n{c.get('text', '')}\n"

    prompt = f"""Subject: {subject}
Issue: {issue}
Instruction: You MUST generate a response where status is "{forced_status}".

{context_str}
"""

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
            res_json = json.loads(response.text)
            res_json["status"] = forced_status
            return res_json
        except Exception as e:
            if attempt == num_retries - 1:
                return {
                    "status": forced_status,
                    "product_area": classification.get("product_area", "unknown"),
                    "response": "Error occurred during generation.",
                    "justification": str(e),
                    "request_type": "invalid"
                }
            time.sleep(1)
