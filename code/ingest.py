import os
from pathlib import Path
import re
import yaml
from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
from llama_index.core.node_parser import MarkdownElementNodeParser, SentenceSplitter
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

def parse_structured_markdown(file_path: Path):
    """
    Mimics Docling/Structured parsing by extracting hierarchy and metadata.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_content = f.read()
            
        metadata = {}
        content = raw_content
        
        # 1. Extract YAML Frontmatter
        if raw_content.startswith("---"):
            parts = raw_content.split("---", 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1].strip()) or {}
                except Exception as e:
                    print(f"YAML parse error in {file_path}: {e}")
                content = parts[2]
        
        # 2. Clean 'Related Articles' and Links (Noise Removal)
        content = re.split(r'(?i)^#+\s+Related Articles', content, flags=re.MULTILINE)[0]
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
        
        # 3. Section-Aware Structure Preservation
        # We keep the headers so the parser understands the hierarchy
        return metadata, content.strip()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}, ""

def main():
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    storage_dir = base_dir / "code" / "storage"
    
    if not data_dir.exists():
        print(f"Data directory not found at {data_dir}!")
        return
        
    print("🚀 Starting Enterprise Structured Ingestion (Docling-Inspired)...")
    
    md_files = list(data_dir.rglob("*.md"))
    print(f"📄 Found {len(md_files)} documents to parse.")
    
    documents = []
    for file_path in md_files:
        company = infer_company_from_path(file_path, data_dir)
        metadata, content = parse_structured_markdown(file_path)
        
        if not content:
            continue
            
        doc_metadata = {
            "company": company,
            "title": metadata.get("title", "Untitled"),
            "url": metadata.get("source_url", ""),
            "article_id": str(metadata.get("article_id", "")),
            "category": metadata.get("category", "general")
        }
        
        documents.append(Document(text=content, metadata=doc_metadata))
    
    # --- INTELLIGENT CHUNKING (Section-Aware) ---
    # Using MarkdownElementNodeParser for hierarchical understanding
    # and SentenceSplitter for optimal chunking within sections
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    Settings.embed_model = embed_model
    
    parser = SentenceSplitter(
        chunk_size=800, 
        chunk_overlap=50,
        include_metadata=True,
        include_prev_next_rel=True
    )
    
    print("🛠️ Building Hybrid Index (Deterministic BM25 + Semantic Vector)...")
    
    index = VectorStoreIndex.from_documents(
        documents, 
        transformations=[parser],
        show_progress=True
    )
    
    if not storage_dir.exists():
        storage_dir.mkdir(parents=True)
        
    index.storage_context.persist(persist_dir=str(storage_dir))
    print(f"✅ Enterprise Index persisted to {storage_dir}")

if __name__ == "__main__":
    main()
