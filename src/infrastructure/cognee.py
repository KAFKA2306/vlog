import os
import cognee
from src.infrastructure.settings import settings
from typing import List

# --- Cognee 1.0 Configuration ---

# 1. LLM Provider (Google Gemini)
# Using "gemini" as the provider string confirmed from Cognee source code
cognee.config.set_llm_provider("gemini")

# 2. LLM Model: gemini-3.1-flash-lite-preview
# LiteLLM expects prefixes for non-OpenAI models
llm_model = settings.gemini_model
if not llm_model.startswith("gemini/"):
    llm_model = f"gemini/{llm_model}"
cognee.config.set_llm_model(llm_model)
cognee.config.set_llm_api_key(settings.gemini_api_key)

# 3. Embedding Model: gemini-embedding-001 (Successor to deprecated 004)
cognee.config.set_embedding_provider("gemini")
cognee.config.set_embedding_model("gemini/gemini-embedding-001")
cognee.config.set_embedding_api_key(settings.gemini_api_key)

# 4. Optional: Extra config for Gemini 3.1 features (if supported by Cognee/LiteLLM)
# cognee.config.set_llm_config({"thinking_level": "medium"}) 

# 5. Environment Variables for LiteLLM
os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
os.environ["GOOGLE_API_KEY"] = settings.gemini_api_key
os.environ["LLM_MODEL"] = llm_model
os.environ["LLM_PROVIDER"] = "gemini"

class CogneeMemory:
    async def add(self, text: str, metadata: dict = None):
        """Add text to the knowledge engine buffer."""
        content = text
        if metadata:
            meta_str = "\n".join([f"{k}: {v}" for k, v in metadata.items()])
            content = f"Metadata:\n{meta_str}\n\nContent:\n{text}"
        
        await cognee.add(content)

    async def cognify(self):
        """Process the added data into the knowledge graph and vector store."""
        # Note: Cognify might take some time as it extracts graph entities
        await cognee.cognify()

    async def search(self, query: str) -> List[dict]:
        """Search the knowledge graph."""
        return await cognee.search(query)

    async def remember(self, text: str, metadata: dict = None):
        """High-level operation: add then cognify."""
        await self.add(text, metadata)
        await self.cognify()

cognee_memory = CogneeMemory()
