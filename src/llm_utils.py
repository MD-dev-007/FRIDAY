import requests
import json

# Ollama HTTP API Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1"           # or "llama3.1:Q4_K_M" if you have it locally for speed
KEEP_ALIVE = "1h"            # keep model hot in RAM


def stream_ollama(prompt: str, model: str = MODEL, opts: dict | None = None):
    """Yields tokens as they arrive. Use in Streamlit to display streaming text."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "keep_alive": KEEP_ALIVE,
        "options": {
            "temperature": 0.3,
            "top_p": 0.92,
            "top_k": 40,
            "repeat_penalty": 1.05,
            "num_ctx": 3072,
            "num_predict": 512,
            "stop": ["\nUser:", "\nAssistant:"]
        } | (opts or {})
    }

    try:
        with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=30) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                data = json.loads(line.decode("utf-8"))
                if "response" in data:
                    yield data["response"]
                if data.get("done"):
                    break
    except Exception as e:
        yield f"⚠️ Error: {str(e)}"


def query_ollama(prompt: str, model: str = MODEL):
    """Legacy function for non-streaming responses."""
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": KEEP_ALIVE,
            "options": {
                "temperature": 0.3,
                "top_p": 0.92,
                "top_k": 40,
                "repeat_penalty": 1.05,
                "num_ctx": 3072,
                "num_predict": 512,
                "stop": ["\nUser:", "\nAssistant:"]
            }
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"⚠️ Exception: {e}"


