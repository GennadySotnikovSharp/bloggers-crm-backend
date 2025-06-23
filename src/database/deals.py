from database.db_connection import supabase
from schemas import DealData

async def update_deal(deal_data: DealData):
    data = {
        "price_usd": deal_data.price_usd,
        "availability": deal_data.availability,
        "discounts": deal_data.discounts,
        "status": deal_data.status,
        "chat_id": deal_data.chat_id
    }
    deal = await supabase.table("deals").select("*").eq("chat_id", deal_data.chat_id).maybe_single().execute()

    response = None
    if not deal:
        response = await supabase.table("deals").insert(data).execute()
    else:
        patched_data = {k: v for k, v in data.items() if v is not None}
        response = await supabase.table("deals").update(patched_data).eq("id", deal.data["id"]).execute()
    return response

async def get_all_deals():
    deals_resp = await supabase.table("deals").select("*").execute()
    return deals_resp.data if deals_resp.data else []
