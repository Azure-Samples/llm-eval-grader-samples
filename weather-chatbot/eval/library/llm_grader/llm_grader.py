from src.clients.llm_interface import (
    get_completion,
)
import json
from json.decoder import JSONDecodeError

class LLMgrader:
    def __init__(self, template):
        self.template = template
        self.seed_prompt = template

    def evaluate_conversation(self, conversation, criteria):
        self.seed_prompt = self.template.replace("{criteria}", criteria)
        prompt = self.seed_prompt.replace("{conversation}", conversation)
        llm_input = [{"role": "system", "content": f"{prompt}"}]
        llm_output = get_completion(llm_input, temperature=0)
        return llm_output

    def evaluate_completion(self, conversation, completion, criteria):
        self.seed_prompt = self.template.replace("{criteria}", criteria)
        prompt = self.seed_prompt.replace("{conversation}", conversation).replace(
            "{completion}", completion
        )
        llm_input = [{"role": "system", "content": f"{prompt}"}]
        llm_output = get_completion(llm_input, temperature=0)
        return llm_output

    def validate_llm_output(self, llm_output) -> dict:
        try:
            # With older GPT4 models (0613) that don't support response_format: json_object
            # They can return json in a markdown format that is inside tags:
            # ```json (your json here)```
            # If that is present, remove it before attempting to load the json
            if '```json' in llm_output:
                llm_output = llm_output.replace('```json', '')
                llm_output = llm_output.replace('```', '')

            results = json.loads(llm_output)
        except JSONDecodeError as err:
            print(f'Failed to parse response as json: {llm_output}, {err.msg}')
            return {"score": 0, "explanation": f"Failed to parse response {llm_output} as json",
                    "answer": "Failed to parse response as json"}

        return results

