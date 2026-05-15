import sys
import os
from pathlib import Path

# Add code directory to path
base_dir = Path(__file__).resolve().parent.parent
code_dir = base_dir / "code"
sys.path.insert(0, str(code_dir))

from agent import process_ticket

def test_single_ticket():
    ticket = {
        "issue": "I lost access to my Claude team workspace after changing my email.",
        "subject": "Workspace Access Issue",
        "company": "Claude"
    }
    
    print("Testing single ticket...")
    try:
        result = process_ticket(ticket)
        print("\n--- RESULT ---")
        print(f"Status: {result.get('status')}")
        print(f"Type: {result.get('request_type')}")
        print(f"Response: {result.get('response')[:200]}...")
        print(f"Justification: {result.get('justification')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_single_ticket()
