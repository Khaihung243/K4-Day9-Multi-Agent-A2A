import json
from src.agents.llm_client import LLMClient

class OrderProductAgent:
    """Agent 2: Handles items, sellers, products, prices, and categories using llama-3.1-8b-instant."""
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.llm = LLMClient()

    def process(self, order_id):
        items = self.data_loader.get_items(order_id)
        
        item_ids = []
        product_ids = []
        seller_ids = []
        category_names = []
        
        item_total_brl = 0.0
        freight_total_brl = 0.0

        for item in items:
            item_seq = item.get("order_item_id")
            item_ids.append(f"{order_id}:{item_seq}")
            
            pid = item.get("product_id")
            if pid and pid not in product_ids:
                product_ids.append(pid)

            sid = item.get("seller_id")
            if sid and sid not in seller_ids:
                seller_ids.append(sid)

            try:
                price = float(item.get("price", 0.0))
                freight = float(item.get("freight_value", 0.0))
            except ValueError:
                price = 0.0
                freight = 0.0
                
            item_total_brl += price
            freight_total_brl += freight

            if pid:
                prod = self.data_loader.get_product(pid)
                if prod and prod.get("category_name"):
                    cat = prod.get("category_name")
                    if cat and cat not in category_names:
                        category_names.append(cat)

        item_total_brl = round(item_total_brl, 2)
        freight_total_brl = round(freight_total_brl, 2)

        system_prompt = "You are OrderProductAgent. Return JSON."
        user_prompt = f"Analyze order {order_id} with {len(items)} items and {len(seller_ids)} sellers."
        llm_response = self.llm.chat_completion(system_prompt, user_prompt)

        result_context = {
            "items": items,
            "item_ids": item_ids,
            "product_ids": product_ids,
            "seller_ids": seller_ids,
            "category_names": category_names,
            "item_total_brl": item_total_brl,
            "freight_total_brl": freight_total_brl
        }

        trace_log = {
            "agent": "OrderProductAgent",
            "model": "llama-3.1-8b-instant",
            "prompt_summary": f"Analyzed {len(items)} items, {len(seller_ids)} sellers, {len(category_names)} categories.",
            "llm_status": llm_response.get("status"),
            "llm_output": llm_response.get("content"),
            "llm_error": llm_response.get("error")
        }

        return result_context, trace_log
