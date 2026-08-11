# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json


class FreelanceEscrow(gl.Contract):
    client: Address
    freelancer: Address
    brief: str
    amount: u256
    status: str
    deliverable_url: str
    verdict_reasoning: str

    def __init__(self, client: str, freelancer: str, brief: str, amount: int):
        self.client = Address(client)
        self.freelancer = Address(freelancer)
        self.brief = brief
        self.amount = u256(amount)
        self.status = "open"
        self.deliverable_url = ""
        self.verdict_reasoning = ""

    @gl.public.write
    def submit_work(self, deliverable_url: str) -> None:
        assert gl.message.sender_address == self.freelancer, "Only freelancer can submit work"
        assert self.status == "open", "Contract not open for submission"
        self.deliverable_url = deliverable_url
        self.status = "submitted"

    @gl.public.write
    def resolve(self) -> None:
        sender = gl.message.sender_address
        assert sender == self.client or sender == self.freelancer, "Not authorized"
        assert self.status == "submitted", "No submitted work to resolve"

        brief = self.brief
        deliverable_url = self.deliverable_url

        def get_input() -> str:
            page = gl.nondet.web.render(deliverable_url, mode="text")
            content = page[:4000]
            lines = [
                "BRIEF:",
                brief,
                "",
                "DELIVERABLE CONTENT (fetched from submitted URL):",
                content,
            ]
            return chr(10).join(lines)

        task_lines = [
            "You are an impartial freelance-work arbitrator.",
            "Based on the BRIEF and DELIVERABLE CONTENT given, decide whether the",
            "deliverable satisfies the brief. Consider partial completion and",
            "reasonable scope interpretation, not just exact wording matches.",
            "Respond using ONLY valid JSON in this exact format, nothing else,",
            "no markdown fences:",
            '{"reasoning": "<short explanation>", "decision": "release|refund|split", "release_percent": <0-100 integer>}',
            "release: deliverable fully meets the brief, release_percent = 100.",
            "refund: deliverable does not address the brief at all, release_percent = 0.",
            "split: partial or incomplete work, choose a fair release_percent between 1 and 99.",
        ]
        task = chr(10).join(task_lines)

        criteria_lines = [
            "The response must be valid JSON with exactly the keys reasoning,",
            "decision, and release_percent.",
            "decision must be one of: release, refund, split.",
            "release_percent must be an integer between 0 and 100.",
            "release_percent must be logically consistent with decision and with",
            "how well the deliverable content actually matches the brief.",
        ]
        criteria = chr(10).join(criteria_lines)

        result_str = gl.eq_principle.prompt_non_comparative(
            get_input, task=task, criteria=criteria
        )
        fence = chr(96) * 3
        result_str = result_str.replace(fence + "json", "").replace(fence, "").strip()
        result = json.loads(result_str)

        decision = result["decision"]
        assert decision in ("release", "refund", "split")
        pct = int(result["release_percent"])
        assert 0 <= pct <= 100

        self.verdict_reasoning = result["reasoning"]
        if pct == 100:
            self.status = "released"
        elif pct == 0:
            self.status = "refunded"
        else:
            self.status = "disputed"
        # In production: trigger actual GEN/token transfer here, split by pct/100.

    @gl.public.view
    def get_status(self) -> str:
        return self.status

    @gl.public.view
    def get_verdict(self) -> str:
        return self.verdict_reasoning

    @gl.public.view
    def get_deliverable(self) -> str:
        return self.deliverable_url
