from pydantic import BaseModel
from typing import Optional

class MessageIn(BaseModel):
    chat_id: str
    sender: str
    content: str
    openai_message_id: Optional[str] = None
    created_at: Optional[str] = None

class MessageOut(BaseModel):
    id: str
    chat_id: str
    sender: str
    openai_message_id: Optional[str] = None
    content: str
    created_at: str

class DealData(BaseModel):
    chat_id: str
    price_usd: Optional[float] = None
    availability: Optional[str] = None
    discounts: Optional[str] = None
    status: Optional[str] = None
