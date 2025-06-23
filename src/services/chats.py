from src.services.database import supabase

async def get_or_create_chat(blogger_id: str) -> dict:
    resp = await supabase.table("chats").select("*").eq("blogger_id", blogger_id).maybe_single().execute()
    if resp is not None and resp.data:
        # print(f"Found existing chat for blogger_id {blogger_id}: {resp.data}")
        return resp.data
    return None

async def create_chat_with_thread(blogger_id: str, thread_id: str, parser_thread_id: str) -> dict:
    data = {
        "blogger_id": blogger_id,
        "openai_thread_id": thread_id,
        "parser_thread_id": parser_thread_id,
    }
    insert_resp = await supabase.table("chats").insert(data).execute()
    return insert_resp.data if insert_resp is not None else None

async def set_openai_thread_id(chat_id: str, thread_id: str):
    await supabase.table("chats").update({"openai_thread_id": thread_id}).eq("id", chat_id).execute()

async def set_parser_thread_id(chat_id: str, parser_thread_id: str):
    await supabase.table("chats").update({"parser_thread_id": parser_thread_id}).eq("id", chat_id).execute()

async def get_parser_thread_id(chat_id: str) -> str:
    resp = await supabase.table("chats").select("parser_thread_id").eq("id", chat_id).maybe_single().execute()
    return resp.data.get("parser_thread_id") if resp is not None and resp.data else None
