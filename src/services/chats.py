from schemas import MessageIn
from database.chats import create_chat_with_thread, get_chat
from database.messages import get_messages_page, save_message
from services.llm import create_openai_thread, send_welcome_text_to_thread
from datetime import datetime

welcome_text = (
        "Hi! I'm Robert from InfluenceCRM 😊 Thanks for connecting. "
        "Could you tell me how much you charge for a brand integration?"
)

async def create_welcome_message(chat_id: str, thread_id: str):
    message_in_thread = await send_welcome_text_to_thread(welcome_text, thread_id)
    await save_message(
        MessageIn(
            chat_id=chat_id,
            sender="manager",
            content=welcome_text,
            openai_message_id=message_in_thread.id,
            created_at=datetime.utcnow().isoformat()
        )
    )

async def get_or_create_chat_with_thread(blogger_id: str):
    chat = await get_chat(blogger_id)
    if not chat:
        thread_id = await create_openai_thread()
        parser_thread_id = await create_openai_thread()
        chat = await create_chat_with_thread(blogger_id, thread_id, parser_thread_id)
    return chat

async def send_welcome_message_if_needed(blogger_id):
    if not blogger_id:
        raise ValueError("blogger_id is required to create or get chat")
    chat = await get_or_create_chat_with_thread(blogger_id)
    chat_id = chat["id"]
    thread_id = chat.get("openai_thread_id")
    page = await get_messages_page(chat_id, limit=1, offset=0)
    if page["total_count"] == 0:
        await create_welcome_message(chat_id, thread_id)
