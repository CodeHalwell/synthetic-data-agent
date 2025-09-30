from pydantic import BaseModel
import os

class LLMConfig(BaseModel):
    model_name: str = os.getenv("A2A_MODEL_NAME", "gpt-4o")
    temperature: float = float(os.getenv("A2A_TEMPERATURE", 1))
    max_tokens: int = int(os.getenv("A2A_MAX_TOKENS", 2048))
