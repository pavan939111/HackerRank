from dotenv import load_dotenv
import os
import json
import time
from google.genai import types
from client_manager import get_client, KEYS
from config import REFUSAL_PHRASE


    context_str = ""
    if no_reliable_context:
        context_str = f"\n[SYSTEM WARNING: NO RELIABLE CONTEXT FOUND. {REFUSAL_PHRASE}]\n"
    else:
        for i, c in enumerate(chunks):
            context_str += f"\n[CONTEXT {i+1} (Source: {c.get('title', 'Unknown')})]\n{c.get('text', '')}\n"

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
                model="gemini-1.5-flash",
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
                    "response": "Error occurred during generation. Safe fallback triggered.",
                    "justification": str(e),
                    "request_type": "invalid"
                }
            time.sleep(2 ** attempt)
