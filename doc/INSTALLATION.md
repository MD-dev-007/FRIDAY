## Installation

### Prerequisites
- Windows with PowerShell
- Python 3.10+
- Ollama installed and in PATH

### Project Structure
- **Code**: `src/` folder contains all application files
- **Memory**: `src/chroma_db/` stores chat history and embeddings
- **Models**: `models/` folder for local Ollama models

### Steps
1) Open PowerShell in repo root
```powershell
cd D:\AI\ULTron
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```
2) In another terminal, start Ollama
```powershell
ollama serve
```
3) Verify or pull a model
```powershell
ollama list
ollama pull llama3
```
4) Start the UI
```powershell
.\venv\Scripts\activate
cd src
streamlit run app.py
```
Optional port:
```powershell
cd src
streamlit run app.py --server.port 8501
```

