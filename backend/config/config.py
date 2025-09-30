import asyncio
import os
import logging
from pydantic import BaseModel, Field
from models.llm import LLMConfig

class Config(BaseModel):
    host: str = os.getenv("A2A_HOST", "localhost")
    port: int = int(os.getenv("A2A_PORT", 8090))
    num_workers: int = int(os.getenv("A2A_NUM_WORKERS", 4))
    llm_config: LLMConfig = LLMConfig()