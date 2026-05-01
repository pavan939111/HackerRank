import os
import sys
import time
import pandas as pd

# Set up paths for modular imports
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
code_dir = os.path.join(base_dir, "code")
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from agent import process_ticket

def main():
    # 🔍 PHASE A — EXECUTION & DATA FLOW CHECK
    
    # 1. Load correct file
    csv_path = os.path.join(base_dir, "support_tickets", "support_tickets.csv")
    if not os.path.exists(csv_path):
        print(f"Error: Could not find input CSV at {csv_path}")
        sys.exit(1)
        
    df = pd.read_csv(csv_path)
    
    # 2. Normalize columns: strip whitespace and lowercase
    df.columns = df.columns.str.strip().str.lower()
    
    # 3. Assert required columns exist
    required_cols = {"issue", "subject", "company"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"Error: Missing required columns: {missing}")
        sys.exit(1)
        
    total_rows = len(df)
    print(f"Total rows to process: {total_rows}")
    
    # 4. Sanity Check: Print first 2 rows
    print("\n--- SANITY CHECK (First 2 rows) ---")
    print(df.head(2))
    print("----------------------------------\n")
    
    results = []
    
    # 5. Loop correctness: No slicing, no early returns
    for idx, row in df.iterrows():
        current_count = idx + 1
        print(f"[{current_count}/{total_rows}] Processing ticket...")
        
        # 6. Row-level try/except to ensure pipeline continues on single row failure
        try:
            # Extract fields safely
            issue = str(row.get("issue", "")).replace("nan", "")
            subject = str(row.get("subject", "")).replace("nan", "")
            company = str(row.get("company", "")).replace("nan", "")
            
            # Convert row to dict for agent
            row_dict = row.to_dict()
            
            # Process through agent
            out = process_ticket(row_dict)
            
            # 7. Results accumulation: Ensure ALL fields are included and preserved
            results.append({
                "issue": issue,
                "subject": subject,
                "company": company,
                "status": out.get("status", "replied"),
                "product_area": out.get("product_area", "general"),
                "response": out.get("response", ""),
                "justification": out.get("justification", ""),
                "request_type": out.get("request_type", "product_issue")
            })
                
        except Exception as e:
            print(f"  FAILED row {current_count}: {str(e)}")
            # Safe fallback result to maintain row count parity
            results.append({
                "issue": str(row.get("issue", "")),
                "subject": str(row.get("subject", "")),
                "company": str(row.get("company", "")),
                "status": "escalated",
                "product_area": "unknown",
                "response": "An unexpected error occurred during processing.",
                "justification": f"System Error: {str(e)}",
                "request_type": "invalid"
            })
        
        # Respect rate limits to mitigate quota issues
        time.sleep(3.0)
        
    # 8. Final integrity check: Assert length parity
    if len(results) != total_rows:
        print(f"Warning: Result count ({len(results)}) does not match input count ({total_rows})!")
    
    # 9. Output writing: Enforce column order and save
    out_df = pd.DataFrame(results)
    column_order = [
        "issue", "subject", "company", "status", 
        "product_area", "response", "justification", "request_type"
    ]
    out_df = out_df[column_order]
    
    out_csv = os.path.join(base_dir, "support_tickets", "output.csv")
    out_df.to_csv(out_csv, index=False)
    
    print(f"\nDone. {len(out_df)} rows written to {out_csv}")

if __name__ == "__main__":
    main()
