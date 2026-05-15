import pandas as pd
import os
from pathlib import Path

def validate():
    base_dir = Path(__file__).resolve().parent.parent
    output_path = base_dir / "support_tickets" / "output.csv"
    expected_path = base_dir / "support_tickets" / "sample_support_tickets.csv"
    
    if not output_path.exists():
        print(f"Error: {output_path} not found.")
        return
        
    print(f"--- Validating {output_path.name} ---")
    df_out = pd.read_csv(output_path)
    
    # 1. Schema Validation
    required_cols = ["issue", "subject", "company", "status", "product_area", "response", "justification", "request_type"]
    missing = set(required_cols) - set(df_out.columns)
    if missing:
        print(f"SCHEMA ERROR: Missing columns {missing}")
    else:
        print("SCHEMA: OK")
        
    # 2. Accuracy Validation (against expected results)
    if expected_path.exists():
        print(f"\n--- Comparing against {expected_path.name} ---")
        df_exp = pd.read_csv(expected_path)
        
        # Normalize columns for comparison
        df_out.columns = df_out.columns.str.strip().str.lower()
        df_exp.columns = df_exp.columns.str.strip().str.lower()
        
        # Clean data for better matching
        df_out['subject'] = df_out['subject'].astype(str).str.strip().str.lower()
        df_exp['subject'] = df_exp['subject'].astype(str).str.strip().str.lower()
        df_out['issue'] = df_out['issue'].astype(str).str.strip().str.lower()
        df_exp['issue'] = df_exp['issue'].astype(str).str.strip().str.lower()
        
        total = 0
        correct_status = 0
        correct_type = 0
        correct_area = 0
        
        mismatches = []
        
        for _, row_out in df_out.iterrows():
            # Try to match by subject first, then by issue if subject is empty
            if row_out['subject'] and row_out['subject'] != 'nan':
                match = df_exp[df_exp['subject'] == row_out['subject']]
            else:
                # Match by first 100 chars of issue
                match = df_exp[df_exp['issue'].str.contains(row_out['issue'][:100], na=False, regex=False)]
                
            if not match.empty:
                row_exp = match.iloc[0]
                total += 1
                
                s_match = str(row_out['status']).lower() == str(row_exp['status']).lower()
                t_match = str(row_out['request_type']).lower() == str(row_exp['request_type']).lower()
                a_match = str(row_out['product_area']).lower() == str(row_exp['product_area']).lower()
                
                if s_match: correct_status += 1
                if t_match: correct_type += 1
                if a_match: correct_area += 1
                
                if not (s_match and t_match):
                    mismatches.append({
                        "subject": row_out['subject'],
                        "exp_status": row_exp['status'],
                        "out_status": row_out['status'],
                        "exp_type": row_exp['request_type'],
                        "out_type": row_out['request_type']
                    })
        
        if total > 0:
            print(f"Total Matches Found: {total}")
            print(f"Status Accuracy: {correct_status/total:.2%}")
            print(f"Request Type Accuracy: {correct_type/total:.2%}")
            print(f"Product Area Accuracy: {correct_area/total:.2%}")
            
            if mismatches:
                print("\n--- TOP MISMATCHES ---")
                for m in mismatches[:5]:
                    print(f"Subject: {m['subject']}")
                    print(f"  Expected: {m['exp_status']} | {m['exp_type']}")
                    print(f"  Got:      {m['out_status']} | {m['out_type']}")
        else:
            print("No matching rows found between output and expected CSV for accuracy check.")
    else:
        print(f"Expected results file not found at {expected_path}. Skipping accuracy check.")

if __name__ == "__main__":
    validate()
