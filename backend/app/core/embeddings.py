from functools import lru_cache

from langchain_openai import AzureOpenAIEmbeddings

from .config import settings


@lru_cache(maxsize=1)
def get_embeddings() -> AzureOpenAIEmbeddings:
    return AzureOpenAIEmbeddings(
        azure_endpoint=settings.azure_openai_embedding_endpoint,
        api_key=settings.azure_openai_embedding_api_key,
        azure_deployment=settings.azure_openai_embedding_deployment,
        api_version=settings.azure_openai_embedding_api_version,
    )


async def embed_query(text: str) -> list[float]:
    return await get_embeddings().aembed_query(text)


async def embed_documents(texts: list[str]) -> list[list[float]]:
    return await get_embeddings().aembed_documents(texts)
