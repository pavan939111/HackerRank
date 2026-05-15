import sys
import os
from pathlib import Path
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

base_dir = Path(__file__).resolve().parent.parent
storage_dir = base_dir / "code" / "storage"

def inspect_index():
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    storage_context = StorageContext.from_defaults(persist_dir=str(storage_dir))
    index = load_index_from_storage(storage_context, embed_model=embed_model)
    
    # Get some nodes
    docstore = index.storage_context.docstore
    nodes = list(docstore.docs.values())
    
    print(f"Total nodes: {len(nodes)}")
    
    # Print unique company values
    companies = set()
    for node in nodes:
        companies.add(node.metadata.get("company"))
    
    print(f"Unique companies in index: {companies}")
    
    if nodes:
        print("\nExample Node Metadata:")
        print(nodes[0].metadata)

if __name__ == "__main__":
    inspect_index()
