# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json


@gl.evm.contract_interface
class _Recipient:
    class View:
        pass
    class Write:
        pass


class FreelanceEscrow(gl.Contract):
    client: Address
    freelancer: Address
    brief: str
    amount: u256              # expected escrow amount, in wei-equivalent base units
    status: str                # "awaiting_funding" | "open" | "submitted" | "released" | "refunded" | "disputed"
    deliverable_url: str
    verdict_reasoning: str

    def __init__(self, client: str, freelancer: str, brief: str, amount: int):
        self.client = Address(client)
        self.freelancer = Address(freelancer)
        self.brief = brief
        self.amount = u256(amount)
        self.status = "awaiting_funding"
        self.deliverable_url = ""
        self.verdict_reasoning = ""

    @gl.public.write.payable
    def fund_escrow(self) -> None:
        # Only the client can fund, and only once, before work is open for submission.
        assert gl.message.sender_address == self.client, "Only client can fund escrow"
        assert self.status == "awaiting_funding", "Escrow already funded"
        assert gl.message.value == self.amount, "Funded value must exactly match agreed amount"
        self.status = "open"

    @gl.public.write
    def submit_work(self, deliverable_url: str) -> None:
        assert gl.message.sender_address == self.freelancer, "Only freelancer can submit work"
        assert self.status == "open", "Contract not open for submission (must be funded first)"
        self.deliverable_url = deliverable_url
        self.status = "submitted"

    @gl.public.write
    def resolve(self) -> None:
        sender = gl.message.sender_address
        assert sender == self.client or sender == self.freelancer, "Not authorized"
        assert self.status == "submitted", "No submitted work to resolve"
        assert self.balance >= self.amount, "Escrow balance does not cover agreed amount"

        brief = self.brief
        deliverable_url = self.deliverable_url

        def leader_fn():
            page = gl.nondet.web.render(deliverable_url, mode="text")
            content = page[:4000]
            lines = [
                "You are an impartial freelance-work arbitrator.",
                "",
                "BRIEF:",
                brief,
                "",
                "DELIVERABLE CONTENT (fetched from submitted URL):",
                content,
                "",
                "Decide whether the deliverable satisfies the brief. Consider",
                "partial completion and reasonable scope interpretation, not",
                "just exact wording matches.",
                "",
                "Respond as JSON with exactly these keys:",
                '{"reasoning": "<short explanation>", "decision": "release|refund|split", "release_percent": <0-100 integer>}',
                "release: deliverable fully meets the brief, release_percent = 100.",
                "refund: deliverable does not address the brief at all, release_percent = 0.",
                "split: partial or incomplete work, release_percent between 1 and 99.",
            ]
            prompt = chr(10).join(lines)
            return gl.nondet.exec_prompt(prompt, response_format="json")

        def validator_fn(leaders_res) -> bool:
            if not isinstance(leaders_res, gl.vm.Return):
                return False
            my_result = leader_fn()
            leader_result = leaders_res.calldata
            # Validators only need to agree on the decision-relevant fields,
            # not the exact reasoning text (which legitimately varies
            # between independent LLM calls).
            return (
                my_result["decision"] == leader_result["decision"]
                and int(my_result["release_percent"]) == int(leader_result["release_percent"])
            )

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        decision = result["decision"]
        assert decision in ("release", "refund", "split")
        pct = int(result["release_percent"])
        assert 0 <= pct <= 100

        self.verdict_reasoning = result["reasoning"]

        freelancer_share = (self.amount * u256(pct)) // u256(100)
        client_share = self.amount - freelancer_share

        if freelancer_share > u256(0):
            _Recipient(self.freelancer).emit_transfer(value=freelancer_share)
        if client_share > u256(0):
            _Recipient(self.client).emit_transfer(value=client_share)

        if pct == 100:
            self.status = "released"
        elif pct == 0:
            self.status = "refunded"
        else:
            self.status = "disputed"

    @gl.public.view
    def get_status(self) -> str:
        return self.status

    @gl.public.view
    def get_verdict(self) -> str:
        return self.verdict_reasoning

    @gl.public.view
    def get_deliverable(self) -> str:
        return self.deliverable_url

    @gl.public.view
    def get_amount(self) -> u256:
        return self.amount

    @gl.public.view
    def get_balance(self) -> u256:
        return self.balance
        
