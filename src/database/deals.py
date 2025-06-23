from database.db_connection import supabase
from schemas import DealData

async def update_deal(deal_data: DealData):
    try: 
        print(f"!!!!!update_deal {deal_data}")
        data = {
            "price_usd": deal_data.price_usd,
            "availability": deal_data.availability,
            "discounts": deal_data.discounts,
            "status": deal_data.status,
            "chat_id": deal_data.chat_id
        }
        print("!!!!!update_deal 1")
        deal = await supabase.table("deals").select("*").eq("chat_id", deal_data.chat_id).maybe_single().execute()
        print(f"!!!!!update_deal 2 deal: {deal}")

        response = None
        if not deal:
            print("!!!!!update_deal 3")
            response = await supabase.table("deals").insert(data).execute()
        else:
            print("!!!!!update_deal 4")
            response = await supabase.table("deals").update(data).eq("id", deal.data["id"]).execute()
        print(f"!!!!!update_deal response: {response}")
        return response
    except Exception as e:
        print(f"!!!!!update_deal exception: {repr(e)}")
        raise

async def get_all_deals():
    deals_resp = await supabase.table("deals").select("*").execute()
    return deals_resp.data if deals_resp.data else []
