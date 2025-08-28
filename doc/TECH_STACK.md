## Technical Stack

### Runtime and Framework
- **Python** (3.10+)
- **Streamlit** — UI and app runtime (`https://streamlit.io`)

### LLM & Inference
- **Ollama** — local LLM server (`https://ollama.com`)
- Default model: `llama3.1` (configurable in `src/llm_utils.py`)

### Memory & Embeddings
- **ChromaDB** — persistent vector store (`https://www.trychroma.com`)
- **sentence-transformers** — `all-MiniLM-L6-v2` (`https://www.sbert.net`)

### Supporting Libraries
- **requests** — HTTP to Ollama
- **PyYAML** — persona configuration

### Project Scripts
- `src/scripts/verify_chromadb.py` — state/health verification
- `src/scripts/setup.ps1` — environment setup and local model configuration

