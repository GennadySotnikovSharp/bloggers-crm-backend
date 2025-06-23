from src.schemas import MessageIn
from src.services.database import supabase
from typing import Dict, Any, List

async def save_message(message: MessageIn):
    data: Dict[str, Any] = {
        "chat_id": message.chat_id,
        "sender": message.sender,
        "content": message.content,
        "openai_message_id": message.openai_message_id,
        "created_at": message.created_at,
    }
    response = await supabase.table("messages").insert(data).execute()
    return response

async def get_messages_page(chat_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    # Получить сообщения по chat_id, отсортированные от новых к старым, с пагинацией
    # "{'message': 'invalid input syntax for type uuid: \"manager\"', 'code': '22P02', 'hint': None, 'details': None}"
    # print(f"Fetching messages for chat_id: {chat_id}, limit: {limit}, offset: {offset}")
    # asd
    query = (
        supabase.table("messages")
        .select("*")
        .eq("chat_id", chat_id)
        .order("created_at", desc=False)
        .range(offset, offset + limit - 1)
    )
    resp = await query.execute()
    messages: List[Dict[str, Any]] = resp.data if resp.data else []
    # Получить общее количество сообщений в чате
    count_resp = await supabase.table("messages").select("id", count="exact").eq("chat_id", chat_id).execute()
    total_count = count_resp.count if hasattr(count_resp, "count") else len(messages)
    return {
        "messages": messages,
        "total_count": total_count
    }
