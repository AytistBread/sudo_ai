from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

from app.config import settings

_client: GigaChat | None = None


class GigaChatNotConfigured(RuntimeError):
    pass


def is_configured() -> bool:
    return settings.gigachat_ready


def get_client() -> GigaChat:
    global _client
    if not settings.gigachat_ready:
        raise GigaChatNotConfigured("GIGACHAT_CREDENTIALS is empty")
    if _client is None:
        _client = GigaChat(
            credentials=settings.gigachat_credentials,
            scope=settings.gigachat_scope,
            model=settings.gigachat_model,
            verify_ssl_certs=settings.gigachat_verify_ssl_certs,
            timeout=90,
        )
    return _client


def chat(system: str, user: str) -> str:
    payload = Chat(
        messages=[
            Messages(role=MessagesRole.SYSTEM, content=system),
            Messages(role=MessagesRole.USER, content=user),
        ]
    )
    response = get_client().chat(payload)
    return response.choices[0].message.content or ""


def embed(texts: list[str]) -> list[list[float]]:
    result = get_client().embeddings(texts)
    return [item.embedding for item in result.data]
