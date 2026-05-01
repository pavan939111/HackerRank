import csv, sys
from pathlib import Path

OUTPUT_CSV = Path("support_tickets/output.csv")
VALID_STATUS       = {"replied", "escalated"}
VALID_REQUEST_TYPE = {"product_issue", "feature_request", "bug", "invalid"}

def validate():
  if not OUTPUT_CSV.exists():
    print("ERROR: output.csv not found. Run main.py first.")
    sys.exit(1)

  errors = []
  with open(OUTPUT_CSV, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

  for i, row in enumerate(rows, 1):
    if row.get("status","") not in VALID_STATUS:
      errors.append(f"Row {i}: invalid status '{row.get('status')}'")
    if row.get("request_type","") not in VALID_REQUEST_TYPE:
      errors.append(f"Row {i}: invalid request_type '{row.get('request_type')}'")
    if len(row.get("response","")) < 20:
      errors.append(f"Row {i}: response too short")
    if len(row.get("justification","")) < 10:
      errors.append(f"Row {i}: justification too short")
    if row.get("product_area","") == "":
      errors.append(f"Row {i}: product_area is empty")

  if errors:
    print(f"VALIDATION FAILED — {len(errors)} errors:")
    for e in errors: print(f"  {e}")
    sys.exit(1)
  else:
    print(f"VALIDATION PASSED — {len(rows)} rows, all fields valid.")

if __name__ == "__main__":
  validate()
