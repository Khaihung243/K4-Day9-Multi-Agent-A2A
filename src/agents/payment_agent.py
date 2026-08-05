import json
from src.agents.llm_client import LLMClient

class PaymentAgent:
    """Agent 3: Reconciles payments with item total and freight value using llama-3.1-8b-instant."""
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.llm = LLMClient()

    def process(self, order_id, has_items, item_total_brl, freight_total_brl):
        payments = self.data_loader.get_payments(order_id)
        
        payment_ids = []
        payment_types = []
        payment_total_brl = 0.0

        for p in payments:
            seq = p.get("payment_sequential")
            payment_ids.append(f"{order_id}:{seq}")
            
            ptype = p.get("payment_type")
            if ptype and ptype not in payment_types:
                payment_types.append(ptype)
                
            try:
                val = float(p.get("payment_value", 0.0))
            except ValueError:
                val = 0.0
            payment_total_brl += val

        payment_total_brl = round(payment_total_brl, 2)

        if not has_items:
            expected_total_brl = None
            difference_brl = None
            reconciled = None
        else:
            expected_total_brl = round(item_total_brl + freight_total_brl, 2)
            difference_brl = round(payment_total_brl - expected_total_brl, 2)
            reconciled = abs(difference_brl) <= 0.10

        system_prompt = "You are PaymentAgent. Return JSON."
        user_prompt = f"Reconcile Payments for Order {order_id}: Paid {payment_total_brl}, Expected {expected_total_brl}."
        llm_response = self.llm.chat_completion(system_prompt, user_prompt)

        result_context = {
            "currency": "BRL",
            "item_total_brl": item_total_brl if has_items else None,
            "freight_total_brl": freight_total_brl if has_items else None,
            "expected_total_brl": expected_total_brl,
            "payment_total_brl": payment_total_brl,
            "difference_brl": difference_brl,
            "reconciled": reconciled,
            "payment_types": payment_types,
            "payment_ids": payment_ids,
            "payment_rows": payments
        }

        trace_log = {
            "agent": "PaymentAgent",
            "model": "llama-3.1-8b-instant",
            "prompt_summary": f"Reconciled {len(payments)} payments. Total Paid: {payment_total_brl}, Reconciled: {reconciled}",
            "llm_status": llm_response.get("status"),
            "llm_output": llm_response.get("content"),
            "llm_error": llm_response.get("error")
        }

        return result_context, trace_log
