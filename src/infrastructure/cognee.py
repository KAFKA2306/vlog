import os

import cognee

from src.infrastructure.settings import settings

llm_model = settings.gemini_model
if not llm_model.startswith("gemini/"):
    llm_model = f"gemini/{llm_model}"

cognee.config.set_llm_provider("gemini")
cognee.config.set_llm_model(llm_model)
cognee.config.set_llm_api_key(settings.gemini_api_key)

cognee.config.set_embedding_provider("gemini")
cognee.config.set_embedding_model("gemini/gemini-embedding-001")
cognee.config.set_embedding_dimensions(768)
cognee.config.set_embedding_api_key(settings.gemini_api_key)

os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
os.environ["GOOGLE_API_KEY"] = settings.gemini_api_key
os.environ["LLM_MODEL"] = llm_model
os.environ["LLM_PROVIDER"] = "gemini"


class CogneeMemory:
    async def add(self, text: str, metadata: dict | None = None) -> None:
        content = text
        if metadata:
            meta_str = "\n".join([f"{k}: {v}" for k, v in metadata.items()])
            content = f"Metadata:\n{meta_str}\n\nContent:\n{text}"
        await cognee.add(content)

    async def cognify(self) -> None:
        await cognee.cognify()

    async def search(self, query: str) -> list[dict]:
        return await cognee.search(query)

    async def remember(self, text: str, metadata: dict | None = None) -> None:
        await self.add(text, metadata)
        await self.cognify()


cognee_memory = CogneeMemory()
