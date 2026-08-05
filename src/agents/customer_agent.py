import json
from src.agents.llm_client import LLMClient

class CustomerAgent:
    """Agent 1: Customer Identity & History Agent using llama-3.1-8b-instant."""
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.llm = LLMClient()

    def process(self, order_id, claimed_customer_id=None):
        order = self.data_loader.get_order(order_id)
        if not order:
            return {"customer_unique_id": None, "related_order_ids": []}, {}

        customer_id = order.get("customer_id", claimed_customer_id)
        cust_info = self.data_loader.get_customer_by_id(customer_id) if customer_id else None
        
        customer_unique_id = cust_info.get("customer_unique_id") if cust_info else None
        related_order_ids = []

        if customer_unique_id:
            all_cust_orders = self.data_loader.get_customer_orders(customer_unique_id)
            related_order_ids = [oid for oid in all_cust_orders if oid != order_id]

        # Call LLM to record Agent reasoning prompt & trace
        system_prompt = "You are CustomerAgent in an E-commerce Multi-Agent system. Your job is to analyze customer history context."
        user_prompt = f"""
        Analyze customer history:
        - Customer ID: {customer_id}
        - Customer Unique ID: {customer_unique_id}
        - Claimed Order ID: {order_id}
        - Related Past Orders Count: {len(related_order_ids)}
        - Related Past Orders: {related_order_ids}

        Return a JSON object with:
        "customer_unique_id": string,
        "related_order_ids": array of strings,
        "agent_notes": string
        """

        llm_response = self.llm.chat_completion(system_prompt, user_prompt)

        result_context = {
            "customer_unique_id": customer_unique_id,
            "related_order_ids": related_order_ids
        }

        trace_log = {
            "agent": "CustomerAgent",
            "model": "llama-3.1-8b-instant",
            "prompt_summary": f"Analyzed customer {customer_unique_id} with {len(related_order_ids)} related orders.",
            "llm_status": llm_response.get("status"),
            "llm_output": llm_response.get("content")
        }

        return result_context, trace_log
