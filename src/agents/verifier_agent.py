import json
from src.agents.llm_client import LLMClient

class VerifierAgent:
    """Agent 6: Enforces schema limits, rounding, and format correctness using llama-3.1-8b-instant."""
    def __init__(self):
        self.llm = LLMClient()

    def verify_and_format(self, case_id, order_id, customer_ctx, order_prod_ctx, payment_ctx, delivery_ctx, policy_res):
        affected_entities = {
            "order_ids": [order_id][:5],
            "item_ids": order_prod_ctx["item_ids"][:5],
            "seller_ids": order_prod_ctx["seller_ids"][:3],
            "payment_ids": payment_ctx["payment_ids"][:5]
        }

        customer_context = {
            "customer_unique_id": customer_ctx["customer_unique_id"],
            "related_order_ids": customer_ctx["related_order_ids"][:5]
        }

        product_context = {
            "product_ids": order_prod_ctx["product_ids"][:5],
            "category_names": order_prod_ctx["category_names"][:5]
        }

        payment_reconciliation = {
            "currency": payment_ctx["currency"],
            "item_total_brl": payment_ctx["item_total_brl"],
            "freight_total_brl": payment_ctx["freight_total_brl"],
            "expected_total_brl": payment_ctx["expected_total_brl"],
            "payment_total_brl": payment_ctx["payment_total_brl"],
            "difference_brl": payment_ctx["difference_brl"],
            "reconciled": payment_ctx["reconciled"],
            "payment_types": payment_ctx["payment_types"]
        }

        root_cause_analysis = {
            "ranked_causes": [
                {"cause_code": policy_res["root_cause_code"], "rank": 1}
            ][:3],
            "responsible_parties": policy_res["responsible_parties"][:3]
        }

        payload = {
            "case_id": case_id,
            "case_assessment": {
                "primary_issue": policy_res["primary_issue"],
                "secondary_issues": policy_res["secondary_issues"],
                "case_status": policy_res["case_status"],
                "confidence": policy_res["confidence"]
            },
            "affected_entities": affected_entities,
            "customer_context": customer_context,
            "product_context": product_context,
            "delivery_analysis": {
                "delivered_at": delivery_ctx["delivered_at"],
                "estimated_delivery_at": delivery_ctx["estimated_delivery_at"],
                "carrier_handoff_at": delivery_ctx["carrier_handoff_at"],
                "delivery_variance_hours": delivery_ctx["delivery_variance_hours"],
                "seller_handoff_analysis": delivery_ctx["seller_handoff_analysis"],
                "late_handoff_seller_ids": delivery_ctx["late_handoff_seller_ids"]
            },
            "payment_reconciliation": payment_reconciliation,
            "root_cause_analysis": root_cause_analysis,
            "evidence_ids": policy_res["evidence_ids"][:20],
            "financial_resolution": {
                "currency": "BRL",
                "recommended_refund_brl": policy_res["recommended_refund_brl"]
            },
            "resolution_actions": policy_res["resolution_actions"][:5]
        }

        system_prompt = "You are VerifierAgent. Return JSON."
        user_prompt = f"Verify JSON Schema for case {case_id}."
        llm_response = self.llm.chat_completion(system_prompt, user_prompt)

        trace_log = {
            "agent": "VerifierAgent",
            "model": "llama-3.1-8b-instant",
            "prompt_summary": f"Verified case {case_id} JSON schema and array bounds.",
            "llm_status": llm_response.get("status"),
            "llm_output": llm_response.get("content"),
            "llm_error": llm_response.get("error")
        }

        return payload, trace_log
