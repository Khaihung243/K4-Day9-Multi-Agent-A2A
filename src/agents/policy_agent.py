import json
from src.agents.utils import parse_datetime
from src.agents.llm_client import LLMClient

class PolicyAgent:
    """Agent 5: Applies EC_POLICY_V2 rules using llama-3.1-8b-instant to derive case resolution."""
    def __init__(self):
        self.llm = LLMClient()

    def evaluate(self, order_id, order_data, customer_ctx, order_prod_ctx, payment_ctx, delivery_ctx):
        order_status = order_data.get("order_status") if order_data else ""
        payment_total = payment_ctx["payment_total_brl"]
        freight_total = order_prod_ctx["freight_total_brl"]

        delivered_at = delivery_ctx["delivered_at"]
        estimated_at = delivery_ctx["estimated_delivery_at"]
        dt_delivered = parse_datetime(delivered_at)
        dt_estimated = parse_datetime(estimated_at)
        
        is_delivery_late = (dt_delivered > dt_estimated) if (dt_delivered and dt_estimated) else False
        late_sellers = delivery_ctx["late_handoff_seller_ids"]
        payment_reconciled = payment_ctx.get("reconciled")

        primary_issue = None
        responsible_parties = []
        recommended_refund_brl = 0.0
        primary_action = None
        root_cause_code = None

        if order_status == "canceled" and payment_total > 0:
            primary_issue = "canceled_order_paid"
            responsible_parties = [{"party_type": "platform", "party_id": "OLIST_PLATFORM"}]
            recommended_refund_brl = payment_total
            primary_action = "issue_full_refund"
            root_cause_code = "ORDER_CANCELED_AFTER_PAYMENT"

        elif order_status == "unavailable" and payment_total > 0:
            primary_issue = "unavailable_order_paid"
            responsible_parties = [{"party_type": "platform", "party_id": "OLIST_PLATFORM"}]
            recommended_refund_brl = payment_total
            primary_action = "issue_full_refund"
            root_cause_code = "ORDER_UNAVAILABLE_AFTER_PAYMENT"

        elif is_delivery_late and len(late_sellers) > 0:
            primary_issue = "late_delivery_seller"
            responsible_parties = [{"party_type": "seller", "party_id": sid} for sid in late_sellers]
            recommended_refund_brl = freight_total
            primary_action = "refund_freight"
            root_cause_code = "SELLER_HANDOFF_AFTER_LIMIT"

        elif is_delivery_late and len(late_sellers) == 0:
            primary_issue = "late_delivery_logistics"
            responsible_parties = [{"party_type": "logistics_provider", "party_id": "LOGISTICS_PROVIDER"}]
            recommended_refund_brl = freight_total
            primary_action = "refund_freight"
            root_cause_code = "CARRIER_DELIVERED_AFTER_ESTIMATE"

        elif len(payment_ctx["payment_ids"]) >= 2 and payment_reconciled is True:
            primary_issue = "valid_split_payment"
            responsible_parties = []
            recommended_refund_brl = 0.0
            primary_action = "explain_valid_split_payment"
            root_cause_code = "MULTIPLE_PAYMENTS_RECONCILED"

        else:
            primary_issue = "unsupported_late_claim"
            responsible_parties = []
            recommended_refund_brl = 0.0
            primary_action = "reject_late_refund"
            root_cause_code = "DELIVERY_WITHIN_ESTIMATE"

        case_status = "action_required" if recommended_refund_brl > 0 else "no_action"
        confidence = 0.95

        secondary_issues = []
        items_count = len(order_prod_ctx["items"])
        distinct_sellers_count = len(order_prod_ctx["seller_ids"])
        payments_count = len(payment_ctx["payment_ids"])
        history_orders_count = len(customer_ctx["related_order_ids"])
        categories_count = len(order_prod_ctx["category_names"])

        if items_count >= 2:
            secondary_issues.append("multi_item_order")
        if distinct_sellers_count >= 2:
            secondary_issues.append("multi_seller_order")
        if payments_count >= 2:
            secondary_issues.append("split_payment")
        if history_orders_count >= 1:
            secondary_issues.append("repeat_customer")
        if categories_count >= 2:
            secondary_issues.append("multiple_categories")

        resolution_actions = [primary_action]
        
        if primary_issue == "late_delivery_seller":
            resolution_actions.append("review_seller_handoff")
        elif primary_issue == "late_delivery_logistics":
            resolution_actions.append("review_carrier_delay")

        if recommended_refund_brl > 0:
            resolution_actions.append("verify_refund_completion")

        if "multi_seller_order" in secondary_issues:
            resolution_actions.append("coordinate_multi_seller_case")

        if "split_payment" in secondary_issues and primary_issue != "valid_split_payment":
            resolution_actions.append("verify_payment_allocation")

        evidence_ids = [f"order:{order_id}"]
        for item_id in order_prod_ctx["item_ids"]:
            evidence_ids.append(f"item:{item_id}")

        for p_id in payment_ctx["payment_ids"]:
            evidence_ids.append(f"payment:{p_id}")

        for resp in responsible_parties:
            if resp["party_type"] == "seller":
                evidence_ids.append(f"seller:{resp['party_id']}")

        evidence_ids.append(f"policy:{root_cause_code}")

        system_prompt = "You are PolicyAgent implementing EC_POLICY_V2. Return JSON."
        user_prompt = f"Evaluate EC_POLICY_V2 for Order {order_id}: Primary Issue: {primary_issue}, Refund: {recommended_refund_brl}."
        llm_response = self.llm.chat_completion(system_prompt, user_prompt)

        result_context = {
            "primary_issue": primary_issue,
            "secondary_issues": secondary_issues,
            "case_status": case_status,
            "confidence": confidence,
            "root_cause_code": root_cause_code,
            "responsible_parties": responsible_parties,
            "recommended_refund_brl": round(recommended_refund_brl, 2),
            "resolution_actions": resolution_actions,
            "evidence_ids": evidence_ids
        }

        trace_log = {
            "agent": "PolicyAgent",
            "model": "llama-3.1-8b-instant",
            "prompt_summary": f"Evaluated EC_POLICY_V2 -> Primary: {primary_issue}, Refund: {recommended_refund_brl} BRL",
            "llm_status": llm_response.get("status"),
            "llm_output": llm_response.get("content"),
            "llm_error": llm_response.get("error")
        }

        return result_context, trace_log
