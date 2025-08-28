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

## App Configuration Screenshots

### Personality Settings
![Personality Configuration](screenshot/personality-setting.jpeg)
*The personality settings panel showing customizable sliders for motivational tone, comedy level, and directness. Users can fine-tune FRIDAY's personality to match their preferred communication style and team dynamics.*

### Customization Options
- **🎭 Motivational Slider**: Adjust how encouraging and motivational FRIDAY should be
- **😄 Comedy Slider**: Control the level of humor and casual tone
- **🎯 Directness Slider**: Set how straightforward and professional the responses should be
- **💾 Save Preferences**: All settings are automatically saved and persist across sessions

