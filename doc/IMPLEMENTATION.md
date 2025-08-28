## Implementation Details

### Prompting
- Persona prompt built from `persona_config.yaml` with graceful fallbacks in `src/persona.py`.
- Sentiment heuristics drive tone hints; personality slider biases humor/directness.
- Final prompt includes top-k memory lines and working goals.

### Memory Strategy
- Save filter prefers short, factual, or explicitly marked content (e.g., goals, reminders).
- Retrieval scoring = vector relevance (by Chroma) + recency + brevity boost.
- Periodic compaction: summarize last N docs, store summary with tags, keep DB snappy.

### Pinning and Goals
- Pin/unpin via metadata updates; pinned surfaced in analysis tab.
- Simple working-goals ring buffer shown in context when available.

### UI/UX
- Glassmorphism cards for messages; animated gradient background; neon hover on buttons.
- Mobile-friendly: adjusted paddings and chat input sizing; responsive sidebar.

### Configuration Points
- Model: `src/llm_utils.py::MODEL`
- Persona & rules: `src/config/persona_config.yaml`
- Memory store path: `./chroma_db` at project root
- Dependencies: `src/requirements.txt`

Project
├── src/                    #  All Python code & config
│   ├── app.py             #  Main Streamlit app
│   ├── persona.py         #  Persona & sentiment detection
│   ├── memory.py          #  ChromaDB memory management
│   ├── llm_utils.py       #  Ollama integration
│   ├── requirements.txt   #  Python dependencies
│   ├── config/            #  Configuration files
│   │   ├── persona_config.yaml
│   │   ├── Modelfile
│   │   └── Modelfile.backup
│   ├── scripts/           #  Setup & utility scripts
│   │   ├── setup.ps1
│   │   └── verify_chromadb.py
│   └── models/            #  Model files & manifests
├── doc/                   #  All documentation
├── README.md              #  Updated with new paths
└── preferences.json       #  User preferences (stays at root)