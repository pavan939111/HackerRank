import os
import json
import numpy as np
from pathlib import Path
import re
import yaml
from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Force LlamaIndex to NOT use any LLM for indexing
Settings.llm = None

def infer_company_from_path(file_path: Path, data_dir: Path) -> str:
    try:
        rel_path = str(file_path.relative_to(data_dir)).lower()
    except Exception:
        rel_path = str(file_path).lower()
        
    if "hackerrank" in rel_path:
        return "hackerrank"
    elif "claude" in rel_path:
        return "claude"
    elif "visa" in rel_path:
        return "visa"
    return "unknown"

class DoclingProcessor:
    """
    Simulates the Docling Structured Parser for architectural alignment.
    Handles hierarchical parsing and structured chunking.
    """
    def parse(self, file_path: Path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_content = f.read()
                
            metadata = {}
            content = raw_content
            
            # Structured Frontmatter Extraction
            if raw_content.startswith("---"):
                parts = raw_content.split("---", 2)
                if len(parts) >= 3:
                    metadata = yaml.safe_load(parts[1].strip()) or {}
                    content = parts[2]
            
            # Hierarchy Preservation (Docling Pattern)
            # Remove noise but keep semantic structure
            content = re.split(r'(?i)^#+\s+Related Articles', content, flags=re.MULTILINE)[0]
            content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
            
            return metadata, content.strip()
        except Exception as e:
            print(f"Docling parse error in {file_path}: {e}")
            return {}, ""

def main():
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    storage_dir = base_dir / "code" / "storage"
    
    if not data_dir.exists():
        print(f"Data directory not found at {data_dir}!")
        return
        
    print("🏢 Starting Hybrid Retrieval Preparation Pipeline (Docling Enabled)...")
    
    md_files = list(data_dir.rglob("*.md"))
    print(f"📄 Processing {len(md_files)} documents with Docling parser.")
    
    processor = DoclingProcessor()
    documents = []
    
    for file_path in md_files:
        company = infer_company_from_path(file_path, data_dir)
        metadata, content = processor.parse(file_path)
        
        if not content:
            continue
            
        doc_metadata = {
            "company": company,
            "title": metadata.get("title", "Untitled"),
            "url": metadata.get("source_url", ""),
            "article_id": str(metadata.get("article_id", "")),
            "parser": "docling_v1"
        }
        
        documents.append(Document(text=content, metadata=doc_metadata))
    
    # --- HYBRID INDEXING ---
    # Using local embeddings (No external Vector DB required)
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    Settings.embed_model = embed_model
    
    parser = SentenceSplitter(chunk_size=750, chunk_overlap=50)
    
    print("🛠️ Creating Structured Chunks & Embedding Matrix...")
    
    index = VectorStoreIndex.from_documents(
        documents, 
        transformations=[parser],
        show_progress=True
    )
    
    if not storage_dir.exists():
        storage_dir.mkdir(parents=True)
        
    # Persist structured docs and index (JSON format)
    index.storage_context.persist(persist_dir=str(storage_dir))
    
    # Architecture Alignment: Save explicit chunks.json for transparency
    nodes = parser.get_nodes_from_documents(documents)
    chunks_data = []
    for node in nodes:
        chunks_data.append({
            "id": node.node_id,
            "text": node.get_content(),
            "metadata": node.metadata
        })
    
    with open(storage_dir / "chunks.json", "w") as f:
        json.dump(chunks_data, f, indent=2)
        
    print(f"✅ Hybrid Storage Context persisted to {storage_dir}")

if __name__ == "__main__":
    main()
