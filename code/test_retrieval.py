import os
import sys
from pathlib import Path

# Add code dir to path
base_dir = Path(__file__).resolve().parent.parent
code_dir = base_dir / "code"
sys.path.append(str(code_dir))

from retriever import retrieve

def test_retrieval():
    query = "How do I reset my password?"
    company = "HackerRank"
    print(f"Testing retrieval for: '{query}' ({company})")
    try:
        result = retrieve(query, company)
        print("Retrieval successful!")
        print(f"Confidence: {result['confidence']}")
        print(f"Top Score: {result['top_score']}")
        print(f"Number of chunks: {len(result['chunks'])}")
        for i, chunk in enumerate(result['chunks']):
            print(f"[{i}] {chunk['title']} (Score: {chunk['score']:.4f})")
    except Exception as e:
        print(f"Retrieval failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_retrieval()
