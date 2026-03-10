"""Helper module for interacting with an Ollama model server.

This is a lightweight wrapper around an HTTP endpoint or CLI invocation.
In production you would replace the stub with real code that sends a prompt
and receives text output from an LLM.
"""
import os
import httpx
from functools import lru_cache

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama2")


@lru_cache(maxsize=128)
def generate(text: str) -> str:
    """Send the given text to the Ollama server and return the response.

    Results are cached for identical prompts to minimise network traffic when
    the same narrative is requested multiple times during development.  The
    default server uses the REST API `/v1/completions` as defined by the
    Ollama HTTP API.  If the server is unavailable this function falls
    back to a deterministic echo.
    """
    try:
        payload = {"model": MODEL_NAME, "prompt": text, "max_tokens": 256}
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(f"{OLLAMA_URL}/v1/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        # Ollama returns {'id':..., 'choices':[{'text': ...}]}
        return data.get("choices", [{}])[0].get("text", "")
    except Exception:
        # fallback behaviour
        return f"[narrative placeholder for input: {text}]"
