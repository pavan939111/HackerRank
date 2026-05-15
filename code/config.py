# Configurable Thresholds for System Constraints
MIN_SCORE = 1.0           # Minimum retrieval score threshold
MIN_OVERLAP = 0.2         # Minimum lexical overlap for response validation
TOP_K = 5                 # Initial retrieval pool size
FINAL_K = 3               # Final chunk count passed to generator

# Escalation & Generation Constants
REFUSAL_PHRASE = "I don't have enough information"
VAGUE_PHRASES = ["maybe", "possibly", "generally", "probably", "i think", "might", "could be"]
ESCALATION_OVERRIDE_MSG = "We are unable to provide a verified answer from available documentation. A human agent will review your request."
