import os
class OpenAIProvider:
    def __init__(self,model: str|None=None): self.model=model or os.getenv("OPENAI_MODEL","gpt-4.1-mini")
    async def generate_structured(self,system_prompt,user_prompt,response_model):
        from openai import AsyncOpenAI
        client=AsyncOpenAI(); completion=await client.responses.parse(model=self.model,input=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],text_format=response_model)
        if completion.output_parsed is None: raise ValueError("LLM returned no validated result")
        return completion.output_parsed
