import requests
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.core.logger import get_model_logger
from app.core.config import settings

logger = get_model_logger()

class ModelService:
    def __init__(self, model_search: list, model_image: list):
        self.model_search = model_search
        self.model_image = model_image
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def get_gemini_models(self, api_key: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/models?key={api_key}"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                gemini_models = response.json()
                return gemini_models
            else:
                logger.error(f"Error: {response.status_code}")
                logger.error(response.text)
                return None
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

    def get_gemini_openai_models(self, api_key: str) -> Optional[Dict[str, Any]]:
        try:
            gemini_models = self.get_gemini_models(api_key)
            return self.convert_to_openai_models_format(gemini_models)
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

    def convert_to_openai_models_format(
            self, gemini_models: Dict[str, Any]
    ) -> Dict[str, Any]:
        openai_format = {"object": "list", "data": [], "success": True}

        for model in gemini_models.get("models", []):
            model_id = model["name"].split("/")[-1]
            openai_model = {
                "id": model_id,
                "object": "model",
                "created": int(datetime.now(timezone.utc).timestamp()),
                "owned_by": "google",
                "permission": [],
                "root": model["name"],
                "parent": None,
            }
            openai_format["data"].append(openai_model)

            if model_id in self.model_search:
                search_model = openai_model.copy()
                search_model["id"] = f"{model_id}-search"
                openai_format["data"].append(search_model)
            if model_id in self.model_image:
                image_model = openai_model.copy()
                image_model["id"] = f"{model_id}-image"
                openai_format["data"].append(image_model)

        if settings.CREATE_IMAGE_MODEL:
            image_model = openai_model.copy()
            image_model["id"] = f"{settings.CREATE_IMAGE_MODEL}-chat"
            openai_format["data"].append(image_model)
        return openai_format
