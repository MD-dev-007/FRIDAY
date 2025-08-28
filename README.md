FRIDAY ULTron local LLM chat with memory and persona

work done
1) models placed under models with blobs and manifests
2) setup script prepared to use local models via OLLAMA_MODELS
3) chromadb verification script created under scripts
4) scripts organized under scripts
5) streamlit chat interface added in app.py with llm_utils.py
6) memory module added in memory.py using chromadb
7) chat app integrated with memory retrieval and storage

prerequisites
1) python 3.10 or newer
2) ollama installed and available in path

directories
models;
scripts
chroma_db auto created on first run

how to run
1) open powershell in repository root
2) run powershell -NoProfile -ExecutionPolicy Bypass -File .\src\scripts\setup.ps1
3) start ollama in a separate terminal using ollama serve
4) list local models using ollama list
5) if llama3.1 exists locally run ollama run llama3.1 Hello FRIDAY
6) if model not present pull with ollama pull llama3 then run ollama run llama3 Hello FRIDAY
7) start chat ui using streamlit run src/app.py

## Documentation
- Overview: see `doc/OVERVIEW.md`
- Technical Stack: see `doc/TECH_STACK.md`
- Architecture: see `doc/ARCHITECTURE.md`
- Implementation Details: see `doc/IMPLEMENTATION.md`
- Installation: see `doc/INSTALLATION.md`
- User Guide: see `doc/USER_GUIDE.md`
- Features: see `doc/FEATURES.md`

configuration
1) change model in src/llm_utils.py by setting MODEL
2) adjust persona and tone in src/config/persona_config.yaml
3) prefer local models by setting OLLAMA_MODELS in src/scripts/setup.ps1 or environment

verification and maintenance
1) verify chromadb state using python src\scripts\verify_chromadb.py
2) clear chroma_db directory if the index becomes corrupted during experimentation


