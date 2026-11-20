"""The helpdesk agent: routes a question to the right behaviour.

1. Ticket status lookup  — "status of ticket TKT-1001"
2. Escalation            — "escalate ticket TKT-1001"
3. Ticket creation       — "raise a ticket: <what is wrong>"
4. RAG answer            — anything else: retrieve from the KB and answer from
                            the best matching passage, citing the source doc.
                            If nothing in the KB matches well enough, the agent
                            says so honestly and offers to raise a ticket
                            instead of guessing.

There is no paid LLM in this project: answers are composed from the retrieved
KB passage itself. That is a deliberate choice — the demo runs fully offline
and never invents policy text.
"""
import re

from .kb_loader import load_kb
from .retriever import TfidfRetriever
from .tickets import TicketStore

TICKET_RE = re.compile(r"TKT-\d+", re.IGNORECASE)
CREATE_PATTERNS = (
    "raise a ticket",
    "create a ticket",
    "open a ticket",
    "file a ticket",
    "log a ticket",
    "raise ticket",
    "create ticket",
)


class HelpdeskAgent:
    def __init__(self, ticket_store: TicketStore | None = None):
        documents = load_kb()
        self.retriever = TfidfRetriever(documents)
        self.tickets = ticket_store or TicketStore()
        self.kb_docs = len(documents)

    # -- tools ---------------------------------------------------------
    def create_ticket(self, title: str, description: str, category: str = "IT",
                      requester: str = "employee") -> dict:
        return self.tickets.create(title, description, category, requester=requester)

    def get_ticket_status(self, ticket_id: str) -> dict | None:
        return self.tickets.get(ticket_id)

    def escalate_ticket(self, ticket_id: str) -> dict | None:
        return self.tickets.escalate(ticket_id)

    # -- answering -----------------------------------------------------
    def _rag_answer(self, question: str) -> dict:
        results = self.retriever.retrieve(question, k=3)
        best_doc, best_score = results[0]
        sources = [
            {
                "source": doc.metadata["source"],
                "title": doc.metadata["title"],
                "score": round(score, 3),
            }
            for doc, score in results
        ]
        # The KB covers the question only if the best chunk is both similar
        # enough AND actually contains the question's key terms.
        if self.retriever.covers(question) is None:
            return {
                "intent": "rag_no_answer",
                "answer": (
                    "I couldn't find this in the helpdesk knowledge base, so I "
                    "won't guess. If you want, I can raise a support ticket for "
                    "you — just say 'raise a ticket' followed by what's wrong — "
                    "or I can escalate it to a human."
                ),
                "sources": sources,
                "ticket": None,
            }
        passage = best_doc.page_content.strip()
        return {
            "intent": "rag_answer",
            "answer": (
                f"Based on the {best_doc.metadata['title']} guide "
                f"({best_doc.metadata['source']}):\n\n{passage}"
            ),
            "sources": sources,
            "ticket": None,
        }

    def ask(self, question: str, requester: str = "employee") -> dict:
        """Handle one employee message. Returns answer + intent + sources."""
        text = question.strip()
        lowered = text.lower()
        ticket_match = TICKET_RE.search(text)
        ticket_id = ticket_match.group(0).upper() if ticket_match else None

        # 1. Ticket status lookup
        if ticket_id and "status" in lowered:
            ticket = self.get_ticket_status(ticket_id)
            if ticket is None:
                return {
                    "intent": "ticket_not_found",
                    "answer": f"I couldn't find any ticket with ID {ticket_id}. "
                              "Please check the ID and try again.",
                    "sources": [],
                    "ticket": None,
                }
            return {
                "intent": "ticket_status",
                "answer": (
                    f"Ticket {ticket['ticket_id']} — \"{ticket['title']}\" — is "
                    f"currently {ticket['status']} (category: {ticket['category']}, "
                    f"priority: {ticket['priority']}, opened {ticket['created_at']})."
                ),
                "sources": [],
                "ticket": ticket,
            }

        # 2. Escalation
        if ticket_id and "escalat" in lowered:
            ticket = self.escalate_ticket(ticket_id)
            if ticket is None:
                return {
                    "intent": "ticket_not_found",
                    "answer": f"I couldn't find any ticket with ID {ticket_id}.",
                    "sources": [],
                    "ticket": None,
                }
            return {
                "intent": "ticket_escalated",
                "answer": (
                    f"Ticket {ticket['ticket_id']} has been escalated to a human "
                    f"support agent (IT helpdesk L2). Its status is now "
                    f"{ticket['status']}."
                ),
                "sources": [],
                "ticket": ticket,
            }

        # 3. Ticket creation
        for pattern in CREATE_PATTERNS:
            if pattern in lowered:
                # Slice the ORIGINAL text (not the lowercased one) so the
                # ticket title keeps the employee's capitalisation.
                idx = lowered.find(pattern) + len(pattern)
                rest = text[idx:].strip(" :-.").strip()
                title = rest[:80] if rest else "Helpdesk request"
                description = rest if rest else text
                category = "HR" if any(
                    w in lowered for w in ("leave", "salary", "payslip", "holiday", "expense")
                ) else "IT"
                ticket = self.create_ticket(title, description, category, requester)
                return {
                    "intent": "ticket_created",
                    "answer": (
                        f"Done — I raised ticket {ticket['ticket_id']} for you: "
                        f"\"{ticket['title']}\" (category: {ticket['category']}). "
                        f"Status is {ticket['status']}. Ask me 'status of ticket "
                        f"{ticket['ticket_id']}' any time to check it."
                    ),
                    "sources": [],
                    "ticket": ticket,
                }

        # 4. RAG answer from the knowledge base
        return self._rag_answer(text)
