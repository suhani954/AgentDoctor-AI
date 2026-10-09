import json
from typing import Any

import httpx

from app.core.config import get_settings


async def ask_ollama_json(
    *,
    system_prompt: str,
    user_prompt: str,
    fallback: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    settings = get_settings()

    if not settings.llm_reasoning_enabled:
        return fallback, False

    prompt = f"""
{system_prompt}

Return only valid JSON. Do not wrap it in markdown.

User context:
{user_prompt}
"""

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.2,
                        "num_ctx": 2048,
                        "num_predict": 220,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("response", "{}")
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                return {
                    **fallback,
                    "reasoning": (
                        "LLM reasoning was attempted but returned an invalid JSON shape. "
                        f"{fallback.get('reasoning', '')}"
                    ),
                }, False
            return parsed, True
    except Exception as exc:
        fallback = {
            **fallback,
            "reasoning": (
                f"LLM reasoning was attempted but did not complete: {type(exc).__name__}. "
                f"{fallback.get('reasoning', '')}"
            ),
        }
        return fallback, False
