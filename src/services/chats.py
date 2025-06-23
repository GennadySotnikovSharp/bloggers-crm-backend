from schemas import MessageIn
from database.chats import create_chat_with_thread, get_or_create_chat
from database.messages import get_messages_page, save_message
from services.llm import create_openai_thread, send_welcome_text_to_thread
import datetime


async def create_welcome_message(chat_id: str, thread_id: str):
    welcome_text = (
        "Hi! I'm Robert from InfluenceCRM 😊 Thanks for connecting. "
        "Could you tell me how much you charge for a brand integration?"
    )
    created_at = datetime.utcnow().isoformat()
    await save_message(
        MessageIn(
            chat_id=chat_id,
            sender="manager",
            content=welcome_text,
            openai_message_id=None,
            created_at=created_at
        )
    )
    # # print(f"Welcome message saved for chat {chat_id}")
    # await manager.send_personal_message(
    #    json.dumps({
    #        "type": "chat_message",
    #        "chat_id": chat_id,
    #        "sender": "manager",
    #        "content": welcome_text,
    #        "created_at": created_at
    #    }),
    #    websocket
    #)
    # print(f"Welcome message sent to websocket for chat {chat_id}")
    await send_welcome_text_to_thread(welcome_text, thread_id)


async def get_or_create_chat_with_thread(blogger_id: str):
    chat = await get_or_create_chat(blogger_id)
    if not chat:
        thread_id = await create_openai_thread()
        parser_thread_id = await create_openai_thread()
        chat = await create_chat_with_thread(blogger_id, thread_id, parser_thread_id)
    # print("get_or_create_chat_with_thread finish")
    return chat

async def send_welcome_message_if_needed(blogger_id):
    # # print(f"Sending welcome message for blogger_id: {blogger_id}")
    if not blogger_id:
        raise ValueError("blogger_id is required to create or get chat")
    print(1)
    chat = await get_or_create_chat_with_thread(blogger_id)
    print(2)
    print("chat = ", chat)
    chat_id = chat["id"]
    print(3)
    thread_id = chat.get("openai_thread_id")
    # # print(f"send_welcome_message_if_needed Fetching existing messages for chat_id: {chat_id}")
    page = await get_messages_page(chat_id, limit=1, offset=0)
    print(4)
    # # print(f"Messages page for chat {chat_id}: {page}")
    if page["total_count"] == 0:
        await create_welcome_message(chat_id, thread_id)
    # # print(f"send_welcome_message_if_needed finish")   