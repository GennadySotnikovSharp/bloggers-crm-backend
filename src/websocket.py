from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
from src.services.users import get_user_by_jwt
from src.services.saved_messages import save_message, get_messages_page
from src.llm import create_openai_thread, create_user_message_in_thread, process_assistant_response, send_welcome_text_to_thread
from src.schemas import MessageIn, DealData
from src.services.deals import update_deal, get_all_deals
from src.services.chats import get_or_create_chat, create_chat_with_thread
import json
from datetime import datetime
import re


router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[Dict[str, Any]] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append({"ws": websocket, "user_id": None, "role": None, "chat_id": None})

    def disconnect(self, websocket: WebSocket):
        self.active_connections = [conn for conn in self.active_connections if conn["ws"] != websocket]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        # print(f"!!! Sending personal message to websocket: {message}")
        await websocket.send_text(message)

    async def send_to_all_marketers(self, message: str):
        for conn in self.active_connections:
            if conn["role"] == "marketer":
                await conn["ws"].send_text(message)

    def get_user_id(self, websocket: WebSocket):
        for conn in self.active_connections:
            if conn["ws"] == websocket:
                return conn["user_id"]
        return None

manager = ConnectionManager()

async def init_user_connection(websocket: WebSocket, first_data: str):
    try:
        first_json = json.loads(first_data)
    except Exception:
        raise ValueError("Failed to parse initial data as JSON")
    # print(f"Received initial data: {first_json}")
    token = first_json.get("access_token")
    if not token:
        raise ValueError("JWT is required")
    user = await get_user_by_jwt(token)
    if not user:
        raise ValueError("User not found in auth.users")
    role = user.user_metadata["role"]
    for conn in manager.active_connections:
        if conn["ws"] == websocket:
            conn["user_id"] = user.id
            conn["role"] = role
            break
    if role == "blogger":
        await send_welcome_message_if_needed(user.id)

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
    chat = await get_or_create_chat_with_thread(blogger_id)
    chat_id = chat["id"]
    thread_id = chat.get("openai_thread_id")
    # # print(f"send_welcome_message_if_needed Fetching existing messages for chat_id: {chat_id}")
    page = await get_messages_page(chat_id, limit=1, offset=0)
    # # print(f"Messages page for chat {chat_id}: {page}")
    if page["total_count"] == 0:
        await create_welcome_message(chat_id, thread_id)
    # # print(f"send_welcome_message_if_needed finish")   

async def process_parser_and_update_deal(content: str, chat_id: str, thread_id: str):
    print(f'process_parser_and_update_deal content: {content} chat_id: {chat_id} thread_id: {thread_id}')
    # 1. Add user message to thread
    await create_user_message_in_thread(content, thread_id)
    # 2. Get parser assistant response
    parser_response = await process_assistant_response("parser", thread_id)
    print(f"process_parser_and_update_deal. Parser response: {parser_response}")
    # 3. Try to extract and parse fields from parser_response["content"]
    parsed_fields = None
    if parser_response and parser_response.get("content"):
        
        # Try to extract text from the content (OpenAI API returns a list of content blocks)
        content_blocks = parser_response["content"]
        print(f"process_parser_and_update_deal. content_blocks: {content_blocks}")
        if isinstance(content_blocks, list) and content_blocks:
            # Try to get the text value from the first block
            block = content_blocks[0]
            # OpenAI API: block.text.value or block["text"]["value"]
            value = None
            if hasattr(block, "text") and hasattr(block.text, "value"):
                value = block.text.value
            elif isinstance(block, dict) and "text" in block and "value" in block["text"]:
                value = block["text"]["value"]
            else:
                value = str(block)
            try:
                cleaned = value.strip().removeprefix("```json").removesuffix("```").strip()
                print('cleaned = ', cleaned)
                parsed_fields = json.loads(cleaned)
            except Exception:
                parsed_fields = None
    print("!!!!process_parser_and_update_deal parsed_fields = ", parsed_fields)
    if parsed_fields:
        deal_data = DealData(
            chat_id=chat_id,
            price_usd=parsed_fields.get("price_usd"),
            availability=parsed_fields.get("availability"),
            discounts=parsed_fields.get("discounts"),
            status=parsed_fields.get("status")
        )
        await update_deal(deal_data)
        await manager.send_to_all_marketers(json.dumps({"deal_update": parsed_fields, "chat_id": chat_id}))

async def save_and_send_message(message_in: MessageIn, websocket: WebSocket):
    await save_message(message_in)
    await websocket.send_text(json.dumps({
        "type": "chat_message",
        "chat_id": message_in.chat_id,
        "sender": message_in.sender,
        "content": message_in.content,
        "created_at": message_in.created_at,
        "openai_message_id": message_in.openai_message_id
    }))

async def handle_chat_message(websocket: WebSocket, data_json: dict):
    
    content = data_json.get("content")
    user_id = manager.get_user_id(websocket)
    chat = await get_or_create_chat(user_id)
    thread_id = chat.get("openai_thread_id")
    parser_thread_id = chat.get("parser_thread_id")
    user_message_in_thread = await create_user_message_in_thread(content, thread_id)
    
    message_in_from_user = MessageIn(
        chat_id=chat["id"],
        sender="user",
        content=content,
        openai_message_id=user_message_in_thread.get("openai_message_id"),
        created_at=datetime.utcnow().isoformat()
    )
    await save_and_send_message(message_in_from_user, websocket)
    
    await process_parser_and_update_deal(content, chat["id"], parser_thread_id)
    if not chat:
        await manager.send_personal_message(json.dumps({"error": "Chat not found"}), websocket)
        return
    assistant_response = await process_assistant_response("manager", thread_id)
    content = assistant_response.get("content")[0]
    # print(f"Assistant response content: {content}")
    # print(f"Assistant response value: ", content.text.value)
    message_in_from_llm = MessageIn(
        chat_id=chat["id"],
        sender="manager",
        content=content.text.value,
        openai_message_id=assistant_response.get("id"),
        created_at=datetime.utcnow().isoformat()
    )
    await save_and_send_message(message_in_from_llm, websocket)
    # print(f"finish handle_chat_message")


async def handle_get_deals(websocket: WebSocket):
    deals = await get_all_deals()
    await manager.send_personal_message(json.dumps({"type": "deals_list", "deals": deals}), websocket)

async def handle_get_existing_messages(websocket: WebSocket, data_json: dict):
    user_id = manager.get_user_id(websocket)
    # print(f"!!!handle_get_existing_messages data_json: {data_json} user_id: {user_id}")
    if not user_id:
        raise ValueError("User not authenticated")
    chat = await get_or_create_chat(user_id)
    # print(f"!!!handle_get_existing_messages Found chat {chat}")

    limit = data_json.get("limit", 20)
    offset = data_json.get("offset", 0)
    # print(f"!!!handle_get_existing_messages Fetching existing messages for chat_id: {chat['id']}, limit: {limit}, offset: {offset}")
    page = await get_messages_page(chat["id"], limit=limit, offset=offset)
    # print(f"!!!handle_get_existing_messages Messages page for chat {chat['id']}: {page}")
    await manager.send_personal_message(json.dumps({
        "type": "messages_page",
        "messages": page["messages"],
        "total_count": page["total_count"],
        "limit": limit,
        "offset": offset,
        "chat_id": chat["id"]
    }), websocket)
    # print(f"!!!finish handle_get_existing_messages")

async def handle_incoming_message(websocket: WebSocket, data: str):
    data_json = json.loads(data)
    msg_type = data_json.get("type")
    if msg_type == "chat_message":
        await handle_chat_message(websocket, data_json)
    elif msg_type == "get_deals":
        await handle_get_deals(websocket)
    elif msg_type == "get_existing_messages":
        await handle_get_existing_messages(websocket, data_json)
    else:
        await manager.send_personal_message(json.dumps({"error": "Unknown message type"}), websocket)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        try:
            # Read and process the first message for authentication
            first_data = await websocket.receive_text()
            await init_user_connection(websocket, first_data)
            # Now process all subsequent messages
            while True:
                data = await websocket.receive_text()
                await handle_incoming_message(websocket, data)
        except WebSocketDisconnect:
            # Client disconnected, just break out
            pass
        except Exception as e:
            try:
                data = await websocket.receive_text()
                data_json = json.loads(data)
                msg_type = data_json.get("type")
                await websocket.send_text(json.dumps({"type": msg_type + "_error", "error": str(e)}))
                await websocket.close()
            except Exception:
                # Ignore errors if socket is already closed
                pass
    finally:
        manager.disconnect(websocket)
