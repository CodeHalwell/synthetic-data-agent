from pydantic import BaseModel
import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_mistralai import ChatMistral
from langchain_community import ChatCommunity

class LLMConfig(BaseModel):
    model: ChatOpenAI | ChatAnthropic | ChatMistral | ChatCommunity
    model_name: str
    temperature: float
    max_tokens: int
    streaming: bool

    def generate_text(self, prompt: str) -> str:
        model = self.model(model=self.model_name, temperature=self.temperature, max_tokens=self.max_tokens)
        return model.generate(prompt)
    
class OpenAILLMConfig(LLMConfig):
    model: ChatOpenAI = ChatOpenAI(model=os.getenv("OPENAI_MODEL_NAME", "gpt-5-mini"), temperature=float(os.getenv("TEMPERATURE", 1)), max_tokens=int(os.getenv("MAX_TOKENS", 2048)))

class AnthropicLLMConfig(LLMConfig):
    model: ChatAnthropic = ChatAnthropic(model=os.getenv("ANTHROPIC_MODEL_NAME", "claude-sonnet-4-5"), temperature=float(os.getenv("TEMPERATURE", 1)), max_tokens=int(os.getenv("MAX_TOKENS", 2048)))

class MistralLLMConfig(LLMConfig):
    model: ChatMistral = ChatMistral(model=os.getenv("MISTRAL_MODEL_NAME", "devstral-medium-2507"), temperature=float(os.getenv("TEMPERATURE", 1)), max_tokens=int(os.getenv("MAX_TOKENS", 2048)))