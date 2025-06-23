from typing import Dict, Any, Literal
import openai
from services.assistant_cache import AssistantCache
from services.env import get_env_var
import asyncio

openai_client = openai.AsyncOpenAI(api_key=get_env_var("OPENAI_API_KEY"))
assistant_cache = AssistantCache(openai_client)

def send_welcome_text_to_thread(welcome_text: str, thread_id: str):
    return openai_client.beta.threads.messages.create(
        thread_id=thread_id,
        role="assistant",
        content=welcome_text
    )

async def wait_for_thread_free(thread_id: str, timeout: int = 30, poll_interval: float = 1.0):
    """
    Wait until there is no active run for the thread.
    """
    import time
    start = time.time()
    while True:
        runs = await openai_client.beta.threads.runs.list(thread_id=thread_id, limit=1)
        if not runs.data:
            return
        last_run = runs.data[0]
        status = getattr(last_run, "status", None)
        if status not in ("in_progress", "queued"):
            return
        if time.time() - start > timeout:
            raise TimeoutError(f"Thread {thread_id} still has an active run after {timeout} seconds")
        await asyncio.sleep(poll_interval)

async def wait_for_run_complete(thread_id: str, run_id: str, timeout: int = 60, poll_interval: float = 1.0):
    """
    Wait until the run is completed or failed.
    """
    import time
    start = time.time()
    while True:
        run = await openai_client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        status = getattr(run, "status", None)
        if status in ("completed", "failed", "cancelled", "expired"):
            return run
        if time.time() - start > timeout:
            raise TimeoutError(f"Run {run_id} did not complete after {timeout} seconds")
        await asyncio.sleep(poll_interval)

async def get_latest_assistant_message(thread_id: str) -> str:
    messages = await openai_client.beta.threads.messages.list(thread_id=thread_id, limit=20)
    # Find the latest message with role="assistant"
    for msg in reversed(messages.data):
        if getattr(msg, "role", None) == "assistant":
            content = getattr(msg, "content", None)
            if isinstance(content, str):
                return content
            elif isinstance(content, list) and content:
                for part in content:
                    # Handle both dict and object content blocks
                    if isinstance(part, dict):
                        if part.get("type") == "text" and "text" in part and "value" in part["text"]:
                            return part["text"]["value"]
                    elif hasattr(part, "type") and part.type == "text" and hasattr(part, "text") and hasattr(part.text, "value"):
                        return part.text.value
            return str(content)
    return ""

async def create_openai_thread() -> str:
    thread = await openai_client.beta.threads.create()
    return thread.id

async def create_user_message_in_thread(message: str, thread_id: str) -> Dict[str, Any]:
    """
    Add a user message to the thread and return its instance.
    """
    await wait_for_thread_free(thread_id)
    msg = await openai_client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message
    )
    # Return message id and content
    return {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "created_at": getattr(msg, "created_at", None)
    }

async def process_assistant_response(assistant: Literal["manager", "parser"], thread_id: str) -> Dict[str, Any]:
    """
    Run the assistant on the thread and return the assistant's message instance.
    """
    try:
        assistant_id = await assistant_cache.get_assistant_id(assistant)
        run = await openai_client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        await wait_for_run_complete(thread_id, run.id)
        # print(f"OpenAI run result (process_robert_response): {run}")
        # await wait_for_run_complete(thread_id, run.id)
        # Get latest assistant message
        messages = await openai_client.beta.threads.messages.list(thread_id=thread_id, limit=20)
        for msg in messages.data:
            if getattr(msg, "role", None) == "assistant":
                return {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": getattr(msg, "created_at", None)
                }
        return {}
    except asyncio.TimeoutError:
        # print("OpenAI run call (process_robert_response) timed out")
        raise
    except Exception as e:
        # print(f"Exception during OpenAI run creation (process_robert_response): {e}")
        raise