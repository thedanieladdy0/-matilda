import ollama
from typing import Optional

class MatildaAI:
    def __init__(self, model_name="qwen2.5:3b-instruct"):
        self.model_name = model_name

    def check_connection(self) -> bool:
        try:
            ollama.list()
            return True
        except: return False

    def generate_response(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': prompt}]
            )
            return response['message']['content']
        except: return None
