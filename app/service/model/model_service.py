from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

from app.config.config import settings
from app.log.logger import get_model_logger

logger = get_model_logger()


class ModelService:
    def __init__(self, search_models: list, image_models: list):
        self.search_models = search_models
        self.image_models = image_models
        self.base_url = settings.BASE_URL
        self.filtered_models = settings.FILTERED_MODELS

    def get_gemini_models(self, api_key: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/models?key={api_key}"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                gemini_models = response.json()

                filtered_models_list = []
                for model in gemini_models.get("models", []):
                    model_id = model["name"].split("/")[-1]
                    if model_id not in self.filtered_models:
                        filtered_models_list.append(model)
                    else:
                        logger.info(f"Filtered out model: {model_id}")

                gemini_models["models"] = filtered_models_list
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

            if model_id in self.search_models:
                search_model = openai_model.copy()
                search_model["id"] = f"{model_id}-search"
                openai_format["data"].append(search_model)
            if model_id in self.image_models:
                image_model = openai_model.copy()
                image_model["id"] = f"{model_id}-image"
                openai_format["data"].append(image_model)

        if settings.CREATE_IMAGE_MODEL:
            image_model = openai_model.copy()
            image_model["id"] = f"{settings.CREATE_IMAGE_MODEL}-chat"
            openai_format["data"].append(image_model)
        return openai_format

    def check_model_support(self, model: str) -> bool:
        if not model or not isinstance(model, str):
            return False

        model = model.strip()
        if model.endswith("-search"):
            model = model[:-7]
            return model in self.search_models
        if model.endswith("-image"):
            model = model[:-6]
            return model in self.image_models

        return model not in self.filtered_models
