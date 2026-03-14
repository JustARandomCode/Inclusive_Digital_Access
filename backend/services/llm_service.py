import httpx
import json
from config import settings
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = "llama2"
        # Shared client — one connection pool for the process lifetime
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=5.0),
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def ensure_model_loaded(self):
        client = await self.get_client()
        try:
            response = await client.get("/api/tags")
            response.raise_for_status()
            models = response.json()
            model_exists = any(
                m["name"].startswith(self.model) for m in models.get("models", [])
            )
            if not model_exists:
                logger.info(f"Pulling {self.model} — this may take several minutes on first run")
                pull = await client.post(
                    "/api/pull",
                    json={"name": self.model},
                    timeout=600.0,
                )
                pull.raise_for_status()
                logger.info(f"Model {self.model} pulled successfully")
        except Exception as e:
            logger.error(f"Failed to ensure model loaded: {e}")
            raise

    async def _generate(self, prompt: str, require_json: bool = False) -> str:
        client = await self.get_client()
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        # Ollama's structured output — constrains the sampler to valid JSON tokens
        if require_json:
            payload["format"] = "json"

        response = await client.post("/api/generate", json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"Ollama returned {response.status_code}")
        return response.json().get("response", "").strip()

    async def extract_form_data(self, text: str, form_type: str) -> Dict[str, Any]:
        prompt = (
            f"Extract structured data from this {form_type} form input.\n"
            f"Input: {text}\n\n"
            "Return a JSON object with these keys only:\n"
            "name, date_of_birth (DD-MM-YYYY), address, phone, additional_info\n"
            "Use null for missing fields. Return only valid JSON."
        )
        try:
            raw = await self._generate(prompt, require_json=True)
            return json.loads(raw)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"LLM extraction failed ({type(e).__name__}), using fallback")
            # Explicit fallback — caller in forms.py can inspect additional_info
            return {
                "name": None,
                "date_of_birth": None,
                "address": None,
                "phone": None,
                "additional_info": text,
                "_extraction_failed": True,
            }

    async def simplify_text(self, text: str, language: str) -> str:
        prompt = (
            f"Rewrite this text in very simple language for someone with limited literacy.\n"
            f"Use short sentences and common everyday words. Language: {language}\n\n"
            f"Text: {text}\n\nSimplified:"
        )
        return await self._generate(prompt)


llm_service = LLMService()
