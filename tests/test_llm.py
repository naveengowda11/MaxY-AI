import httpx
import pytest

from core.llm import LLMError, OllamaClient


@pytest.mark.asyncio
async def test_ollama_client_returns_assistant_content():
    def handler(request):
        return httpx.Response(
            200,
            json={"message": {"role": "assistant", "content": "Local answer"}},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        llm = OllamaClient(
            base_url="http://ollama.test",
            model="test-model",
            client=client,
        )
        answer = await llm.chat([{"role": "user", "content": "Hi"}])

    assert answer == "Local answer"


@pytest.mark.asyncio
async def test_ollama_client_rejects_empty_response():
    def handler(request):
        return httpx.Response(200, json={"message": {"content": "  "}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        llm = OllamaClient("http://ollama.test", "test-model", client=client)
        with pytest.raises(LLMError, match="empty response"):
            await llm.chat([{"role": "user", "content": "Hi"}])
