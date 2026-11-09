"""Small asynchronous client for Ollama's local chat API."""
from typing import Any

import httpx


class LLMError(RuntimeError):
    """Raised when the local language model cannot answer."""


class OllamaClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: float = 90.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._client = client

    async def chat(self, messages: list[dict[str, str]]) -> str:
        """Send a non-streaming chat request to the local Ollama server."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        try:
            if self._client is not None:
                response = await self._client.post(
                    f"{self.base_url}/api/chat", json=payload
                )
            else:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        f"{self.base_url}/api/chat", json=payload
                    )
            response.raise_for_status()
            data = response.json()
        except httpx.ConnectError as exc:
            raise LLMError(
                "Cannot connect to Ollama. Start Ollama and make sure the local model is installed."
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMError("The local model took too long to respond.") from exc
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:300]
            raise LLMError(f"Ollama returned HTTP {exc.response.status_code}: {detail}") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise LLMError(f"Could not read the Ollama response: {exc}") from exc

        content = data.get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise LLMError("Ollama returned an empty response.")
        return content.strip()
