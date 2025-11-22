"""LLM utilities (Groq-only).

- build_prompt: arma un prompt con sistema + contexto + pregunta
- call_groq: invoca Groq (OpenAI compatible) con reintentos y backoff
- call_llm: alias que siempre usa Groq
"""

import os
from typing import Optional

import httpx
import time
import random
from dotenv import load_dotenv

# Carga .env con override para que las variables del archivo tengan prioridad
load_dotenv(override=True)


def build_prompt(user_query: str, context: str) -> str:
    system = (
        "Eres un asistente conciso. Responde SOLO usando la información del CONTEXTO. "
        "Si no está en el contexto, di que no lo sabes."
    )
    return (
        f"[SISTEMA]\n{system}\n\n"
        f"[CONTEXTO]\n{context}\n\n"
        f"[PREGUNTA]\n{user_query}\n\n"
        f"[INSTRUCCIONES]\nResponde en español."
    )


def call_groq(prompt: str, model: Optional[str] = None) -> str:
    """Llama a Groq (API estilo OpenAI) si hay GROQ_API_KEY. Modelos rápidos: llama-3.1-8b-instant, mixtral-8x7b-instruct.
    Docs: https://console.groq.com/ """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "[Sin GROQ_API_KEY]"
    try:
        m = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": m,
            "messages": [
                {"role": "system", "content": "Responde en español usando solo el contexto proporcionado."},
                {"role": "user", "content": prompt},
            ],
            "temperature": float(os.getenv("GROQ_TEMPERATURE", "0.2")),
            "max_tokens": int(os.getenv("GROQ_MAX_TOKENS", "512")),
        }

        max_retries = max(0, int(os.getenv("GROQ_MAX_RETRIES", "3")))
        backoff_base = max(0.1, float(os.getenv("GROQ_BACKOFF_BASE", "0.5")))  # seconds

        attempt = 0
        last_err = None
        with httpx.Client(timeout=30) as client:
            while attempt <= max_retries:
                try:
                    r = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    r.raise_for_status()
                    data = r.json()
                    return data["choices"][0]["message"]["content"]
                except httpx.HTTPStatusError as e:
                    status = e.response.status_code if e.response is not None else None
                    # Handle rate limit (429) and transient 5xx with retry
                    if status in (429, 500, 502, 503, 504) and attempt < max_retries:
                        delay = backoff_base * (2 ** attempt) + random.uniform(0, 0.25)
                        # Respect Retry-After if present (seconds)
                        if e.response is not None:
                            ra = e.response.headers.get("Retry-After")
                            try:
                                if ra:
                                    delay = max(delay, float(ra))
                            except Exception:
                                pass
                        time.sleep(delay)
                        attempt += 1
                        last_err = e
                        continue
                    # Non-retryable or retries exhausted
                    try:
                        err_json = e.response.json() if e.response is not None else None
                    except Exception:
                        err_json = None
                    msg = err_json.get("error", {}).get("message") if isinstance(err_json, dict) else None
                    return f"[Error Groq] HTTP {status}: {msg or str(e)}"
                except Exception as e:
                    # Network or other client error; retry a couple times
                    if attempt < max_retries:
                        delay = backoff_base * (2 ** attempt) + random.uniform(0, 0.25)
                        time.sleep(delay)
                        attempt += 1
                        last_err = e
                        continue
                    return f"[Error Groq] {e}"
        return f"[Error Groq] {last_err or 'desconocido'}"
    except Exception as e:
        return f"[Error Groq] {e}"


def call_llm(prompt: str) -> str:
    """Único backend: Groq."""
    return call_groq(prompt)
