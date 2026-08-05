from src.agents.customer_agent import CustomerAgent
from src.agents.order_product_agent import OrderProductAgent
from src.agents.payment_agent import PaymentAgent
from src.agents.delivery_agent import DeliveryAgent
from src.agents.policy_agent import PolicyAgent
from src.agents.verifier_agent import VerifierAgent

class CoordinatorAgent:
    """Coordinator Agent: Orchestrates execution flow, agent LLM prompts, handoffs, and tracing."""
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.customer_agent = CustomerAgent(data_loader)
        self.order_prod_agent = OrderProductAgent(data_loader)
        self.payment_agent = PaymentAgent(data_loader)
        self.delivery_agent = DeliveryAgent(data_loader)
        self.policy_agent = PolicyAgent()
        self.verifier_agent = VerifierAgent()

    def process_case(self, case_input):
        case_id = case_input.get("case_id")
        cust_req = case_input.get("customer_request", {})
        claimed_order_id = cust_req.get("claimed_order_id")

        trace_steps = []
        trace_steps.append({
            "agent": "CoordinatorAgent",
            "action": "received_case",
            "case_id": case_id,
            "claimed_order_id": claimed_order_id
        })

        order_data = self.data_loader.get_order(claimed_order_id)

        # Handoff 1: Customer Agent
        customer_ctx, trace1 = self.customer_agent.process(claimed_order_id)
        trace_steps.append(trace1)

        # Handoff 2: Order & Product Agent
        order_prod_ctx, trace2 = self.order_prod_agent.process(claimed_order_id)
        trace_steps.append(trace2)

        # Handoff 3: Payment Agent
        has_items = len(order_prod_ctx["items"]) > 0
        payment_ctx, trace3 = self.payment_agent.process(
            claimed_order_id,
            has_items,
            order_prod_ctx["item_total_brl"],
            order_prod_ctx["freight_total_brl"]
        )
        trace_steps.append(trace3)

        # Handoff 4: Delivery Agent
        delivery_ctx, trace4 = self.delivery_agent.process(claimed_order_id, order_prod_ctx["items"])
        trace_steps.append(trace4)

        # Handoff 5: Policy Agent
        policy_res, trace5 = self.policy_agent.evaluate(
            claimed_order_id,
            order_data,
            customer_ctx,
            order_prod_ctx,
            payment_ctx,
            delivery_ctx
        )
        trace_steps.append(trace5)

        # Handoff 6: Verifier Agent
        final_payload, trace6 = self.verifier_agent.verify_and_format(
            case_id,
            claimed_order_id,
            customer_ctx,
            order_prod_ctx,
            payment_ctx,
            delivery_ctx,
            policy_res
        )
        trace_steps.append(trace6)

        return final_payload, trace_steps
