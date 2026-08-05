import json
from src.agents.utils import parse_datetime, calc_hours_diff
from src.agents.llm_client import LLMClient

class DeliveryAgent:
    """Agent 4: Evaluates delivery timestamps and seller handoff delays using llama-3.1-8b-instant."""
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.llm = LLMClient()

    def process(self, order_id, items):
        order = self.data_loader.get_order(order_id)
        if not order:
            empty_res = {
                "delivered_at": None,
                "estimated_delivery_at": None,
                "carrier_handoff_at": None,
                "delivery_variance_hours": None,
                "seller_handoff_analysis": [],
                "late_handoff_seller_ids": []
            }
            return empty_res, {"agent": "DeliveryAgent", "prompt_summary": "Order not found"}

        delivered_str = order.get("order_delivered_customer_date")
        estimated_str = order.get("order_estimated_delivery_date")
        carrier_str = order.get("order_delivered_carrier_date")

        dt_delivered = parse_datetime(delivered_str)
        dt_estimated = parse_datetime(estimated_str)
        dt_carrier = parse_datetime(carrier_str)

        delivery_variance_hours = calc_hours_diff(dt_delivered, dt_estimated)

        seller_limits = {}
        for item in items:
            sid = item.get("seller_id")
            limit_str = item.get("shipping_limit_date")
            dt_limit = parse_datetime(limit_str)
            if sid and dt_limit:
                if sid not in seller_limits or dt_limit < seller_limits[sid]["dt"]:
                    seller_limits[sid] = {"dt": dt_limit, "str": limit_str}

        seller_handoff_analysis = []
        late_handoff_seller_ids = []

        for sid, limit_info in seller_limits.items():
            dt_limit = limit_info["dt"]
            limit_str = limit_info["str"]
            
            variance = calc_hours_diff(dt_carrier, dt_limit)
            is_late = (dt_carrier > dt_limit) if (dt_carrier and dt_limit) else False
            
            if is_late:
                late_handoff_seller_ids.append(sid)

            seller_handoff_analysis.append({
                "seller_id": sid,
                "shipping_limit_at": limit_str,
                "handoff_variance_hours": variance,
                "late_handoff": is_late
            })

        # LLM Reasoning Call & Trace
        system_prompt = "You are DeliveryAgent in an E-commerce Multi-Agent system."
        user_prompt = f"""
        Analyze Delivery Timestamps:
        - Delivered At: {delivered_str}
        - Estimated Delivery At: {estimated_str}
        - Carrier Handoff At: {carrier_str}
        - Delivery Variance Hours: {delivery_variance_hours}
        - Late Handoff Seller IDs: {late_handoff_seller_ids}

        Return a JSON summarizing delivery delay assessment.
        """
        llm_response = self.llm.chat_completion(system_prompt, user_prompt)

        result_context = {
            "delivered_at": delivered_str if delivered_str else None,
            "estimated_delivery_at": estimated_str if estimated_str else None,
            "carrier_handoff_at": carrier_str if carrier_str else None,
            "delivery_variance_hours": delivery_variance_hours,
            "seller_handoff_analysis": seller_handoff_analysis,
            "late_handoff_seller_ids": late_handoff_seller_ids
        }

        trace_log = {
            "agent": "DeliveryAgent",
            "model": "llama-3.1-8b-instant",
            "prompt_summary": f"Calculated delivery variance {delivery_variance_hours}h. Late sellers: {late_handoff_seller_ids}",
            "llm_status": llm_response.get("status"),
            "llm_output": llm_response.get("content")
        }

        return result_context, trace_log
