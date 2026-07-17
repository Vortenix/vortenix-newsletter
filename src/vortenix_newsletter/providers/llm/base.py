from typing import Protocol,TypeVar
from pydantic import BaseModel
T=TypeVar("T",bound=BaseModel)
class LLMProvider(Protocol):
    """Generate output validated against a caller-supplied Pydantic model."""

    async def generate_structured(self,system_prompt: str,user_prompt: str,response_model: type[T])->T: ...
