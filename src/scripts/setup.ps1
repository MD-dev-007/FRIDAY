Param(
    [switch]$PullModel
)

$ErrorActionPreference = "Stop"

function Write-Section($text) {
    Write-Host "`n=== $text ===" -ForegroundColor Cyan
}

Write-Section "Environment: Create & Activate Virtualenv"
if (-not (Test-Path -Path "venv")) {
    try {
        python -m venv venv
    } catch {
        try {
            py -3 -m venv venv
        } catch {
            Write-Error "Failed to create virtual environment. Ensure Python 3 is installed and in PATH."
            exit 1
        }
    }
}

& .\venv\Scripts\Activate.ps1

Write-Section "Python: Upgrade pip"
python -m pip install --upgrade pip

Write-Section "Python: Install requirements"
if (-not (Test-Path -Path "src\requirements.txt")) {
    Write-Error "requirements.txt not found at src\requirements.txt"
    exit 1
}
pip install -r src\requirements.txt

Write-Section "Validation: Python & Services"
Write-Host "Streamlit version:" -NoNewline; streamlit version

Write-Host "Testing ChromaDB client..." -ForegroundColor Yellow
try {
    python .\src\scripts\verify_chromadb.py
} catch {
    Write-Warning "ChromaDB quick test failed. See error above."
}

# Create ChromaDB directory inside src if it doesn't exist
Write-Host "Creating ChromaDB directory..." -ForegroundColor Yellow
$chromaPath = ".\src\chroma_db"
if (-not (Test-Path -Path $chromaPath)) {
    New-Item -ItemType Directory -Path $chromaPath -Force | Out-Null
    Write-Host "Created ChromaDB directory at $chromaPath" -ForegroundColor Green
} else {
    Write-Host "ChromaDB directory already exists at $chromaPath" -ForegroundColor Green
}

Write-Section "Ollama: CLI Presence"
$ollamaExists = $false
try {
    $null = (Get-Command ollama -ErrorAction Stop)
    $ollamaExists = $true
    Write-Host "Ollama found:" -NoNewline; ollama --version
} catch {
    Write-Warning "Ollama not found. Install from https://ollama.com/download and run once."
}

Write-Section "Ollama: Local Models Configuration"
if (Test-Path -Path "models") {
    $modelsPath = (Resolve-Path ".\models").Path
    Write-Host "Found models at $modelsPath"
    $env:OLLAMA_MODELS = $modelsPath
    Write-Host "Set OLLAMA_MODELS for this session: $env:OLLAMA_MODELS"
} else {
    Write-Host "No local models folder found."
}

if ($ollamaExists) {
    Write-Host "Listing Ollama models (post-config):"
    try { ollama list | Out-String | Write-Host } catch { Write-Warning "Failed to list Ollama models." }

    # Quick check for a locally provided llama3.1 manifest
    $llama31Manifest = Join-Path (Resolve-Path ".").Path "models\manifests\registry.ollama.ai\library\llama3.1\latest"
    if (Test-Path -Path $llama31Manifest) {
        Write-Host "Detected local manifest for llama3.1"
        try { ollama show llama3.1 | Select-Object -First 10 | Out-String | Write-Host } catch { Write-Warning "Could not show llama3.1 details via Ollama." }
    }
}

if ($ollamaExists -and $PullModel) {
    # Skip pulling if a local llama3.1 manifest exists
    $localLlama31 = Test-Path -Path "models/manifests/registry.ollama.ai/library/llama3.1/latest"
    if ($localLlama31) {
        Write-Section "Local llama3.1 detected; skipping remote pull"
    } else {
        Write-Section "Pulling llama3 model"
        try {
            ollama pull llama3
        } catch {
            Write-Warning "Failed to pull llama3. You can try manually: ollama pull llama3"
        }
    }
}

Write-Section "All Set"
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "1) To open Streamlit demo:    streamlit hello"
Write-Host "2) If needed, pull from remote: ollama pull llama3"
Write-Host "3) If local manifest exists:   ollama run llama3.1 \"Hello FRIDAY\""
Write-Host "4) Otherwise use remote name:  ollama run llama3 \"Hello FRIDAY\""
Write-Host "5) To start FRIDAY app later:  python app.py  (will add in Step 2)"
Write-Host "6) Start chat UI: streamlit run app.py"