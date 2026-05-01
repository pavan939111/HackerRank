import json
import re
import yaml
from pathlib import Path

def infer_company_from_path(file_path: Path) -> str:
    path_lower = str(file_path).lower()
    if "hackerrank" in path_lower:
        return "hackerrank"
    elif "claude" in path_lower:
        return "claude"
    elif "visa" in path_lower:
        return "visa"
    return "unknown"

def parse_markdown_file(file_path: Path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        metadata = {}
        # Parse YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1].strip()) or {}
                except Exception as e:
                    print(f"YAML parse error in {file_path}: {e}")
                content = parts[2]
                
        # Remove Related Articles section completely
        content = re.split(r'(?i)^#+\s+Related Articles', content, flags=re.MULTILINE)[0]
        
        # Remove Markdown Links but keep text: [text](url) -> text
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
        
        # Remove headings: # Heading -> Heading
        content = re.sub(r'^#+\s+', '', content, flags=re.MULTILINE)
        
        # Clean extra whitespace
        content = re.sub(r'\n{3,}', '\n\n', content).strip()
        
        return metadata, content
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}, ""

def chunk_text(text: str, size: int = 400, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i+size])
        chunks.append(chunk)
        if i + size >= len(words):
            break
        i += size - overlap
    return chunks

def main():
    # Allow running from project root or inside code/
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    
    if not data_dir.exists():
        print(f"Data directory not found at {data_dir}!")
        return
        
    print("Starting preprocessing pipeline...")
    processed_chunks = []
    
    # Recursively load ALL files
    md_files = list(data_dir.rglob("*.md"))
    print(f"Found {len(md_files)} markdown files.")
    
    for file_path in md_files:
        company = infer_company_from_path(file_path)
        metadata, content = parse_markdown_file(file_path)
        
        if not content:
            continue
            
        chunks = chunk_text(content, size=400, overlap=50)
        
        for chunk in chunks:
            processed_chunks.append({
                "text": chunk,
                "company": company,
                "title": metadata.get("title", ""),
                "url": metadata.get("source_url", ""),
                "article_id": str(metadata.get("article_id", ""))
            })
            
    out_file = data_dir / "processed_chunks.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(processed_chunks, f, indent=2)
        
    print(f"Successfully processed {len(processed_chunks)} chunks and saved to {out_file}")

if __name__ == "__main__":
    main()
