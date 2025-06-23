import os
from typing import Dict, Any, Optional, List
import openai

def get_prompt_from_file(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "../../assistants", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

PresaleAssistants = {
    "manager": {
        "temperature": 0.9,
        "model": "gpt-4o",
        "assistant_version": "2.0",
        "assistant_name": "Manager Assistant",
        "getAssistantInstruction": lambda: get_prompt_from_file("manager.txt"),
    },
    "parser": {
        "temperature": 0.9,
        "model": "gpt-4o",
        "assistant_version": "2.0",
        "assistant_name": "Parser Assistant",
        "getAssistantInstruction": lambda: get_prompt_from_file("parser.txt"),
    },
}

class AssistantCache:
    def __init__(self, openai_client: openai.OpenAI):
        self.cache: List[Dict[str, str]] = []
        self.openai_client = openai_client

    async def get_assistant_id(self, assistant_name: str) -> str:
        try:
            config = PresaleAssistants[assistant_name]
            model = config["model"]
            temperature = config["temperature"]
            get_instruction = config["getAssistantInstruction"]
            assistant_version = config["assistant_version"]
            assistant_name_str = config["assistant_name"]

            cached = next((a for a in self.cache if a["name"] == assistant_name_str and a["version"] == assistant_version), None)
            if cached:
                return cached["id"]
            latest_assistant = await find_latest_assistant_by_type(self.openai_client, assistant_name_str, assistant_version)
            if not latest_assistant:
                latest_assistant = await create_assistant_with_metadata(
                    self.openai_client,
                    f"{assistant_name_str} v{assistant_version}",
                    get_instruction(),
                    temperature,
                    model,
                    {
                        "type": assistant_name_str,
                        "version": assistant_version
                    }
                )
            self.cache.append({
                "id": latest_assistant.id,
                "name": assistant_name_str,
                "version": assistant_version
            })
            return latest_assistant.id
        except KeyError:
            raise ValueError(f"Assistant {assistant_name} not found in configuration")

async def list_assistants(openai_client: openai.OpenAI, limit: int = 20, order: str = "desc") -> List[Any]:
    response = await openai_client.beta.assistants.list(order=order, limit=limit)
    return response.data

async def find_latest_assistant_by_type(openai_client: openai.OpenAI, type_: str, version: Optional[str] = None) -> Optional[Any]:
    assistants = await list_assistants(openai_client)
    filtered = [
        a for a in assistants
        if (a.metadata.get("type") == type_ and (version is None or a.metadata.get("version") == version))
    ]
    if not filtered:
        return None
    return max(filtered, key=lambda a: float(a.metadata.get("version", "0")))

async def create_assistant_with_metadata(
    openai_client: openai.OpenAI,
    name: str,
    instructions: str,
    temperature: float,
    model: str,
    metadata: Dict[str, str]
) -> Any:
    assistant = await openai_client.beta.assistants.create(
        instructions=instructions,
        name=name,
        model=model,
        temperature=temperature,
        metadata=metadata
    )
    
    return assistant
