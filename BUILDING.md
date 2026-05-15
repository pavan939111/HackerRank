# Building the Hybrid Support Triage Agent

Follow these steps to initialize and run the system.

### 1. Environment Setup
Create a `.env` file with your Gemini API Keys:
```env
GEMINI_API_KEY_1=your_key_here
GEMINI_API_KEY_2=your_key_here
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Document Ingestion (Stage 0)
Run the preprocessing pipeline to build the Hybrid Index. This step uses the **Docling Processor** to parse markdown files into structured chunks and generate the embedding matrix.

```bash
python code/preprocess.py
```
Outputs:
- `code/storage/`: Persistent hybrid index.
- `code/storage/chunks.json`: Structured chunk repository.

### 3. Running the Agent
Process the input tickets via the main entry point:

```bash
python code/main.py
```

### 4. Output Verification
Results are saved to `support_tickets/output.csv`. Check the `justification` column to see the internal reasoning for each triage decision.
