from typing import List, Union

import openai
from openai.types import CreateEmbeddingResponse
from app.config.config import settings
from app.log.logger import get_embeddings_logger

logger = get_embeddings_logger()


class EmbeddingService:

    async def create_embedding(
        self, input_text: Union[str, List[str]], model: str, api_key: str
    ) -> CreateEmbeddingResponse:
        """Create embeddings using OpenAI API"""
        try:
            client = openai.OpenAI(api_key=api_key, base_url=settings.BASE_URL)
            response = client.embeddings.create(input=input_text, model=model)
            return response
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}")
            raise
