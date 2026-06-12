from functools import lru_cache

from langchain_openai import AzureChatOpenAI

from .config import settings


@lru_cache(maxsize=4)
def get_chat_model(temperature: float = 0.8, max_tokens: int = 1200) -> AzureChatOpenAI:
    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_chat_endpoint,
        api_key=settings.azure_openai_chat_api_key,
        azure_deployment=settings.azure_openai_chat_deployment,
        api_version=settings.azure_openai_chat_api_version,
        temperature=temperature,
        max_tokens=max_tokens,
    )
