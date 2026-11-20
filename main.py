"""FastAPI app: the helpdesk agent as REST endpoints.

Run:  uvicorn main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from helpdesk.agent import HelpdeskAgent

app = FastAPI(
    title="HR/IT Helpdesk Agent",
    description="RAG helpdesk agent: answers from a local knowledge base and "
                "manages support tickets (create, status, escalate).",
    version="0.1.0",
)
agent = HelpdeskAgent()


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, description="Employee's question")
    requester: str = "employee"


class AskResponse(BaseModel):
    intent: str
    answer: str
    sources: list[dict]
    ticket: dict | None = None


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=3)
    category: str = "IT"
    priority: str = "Normal"
    requester: str = "employee"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "kb_chunks": agent.kb_docs}


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest) -> AskResponse:
    result = agent.ask(body.question, requester=body.requester)
    return AskResponse(**result)


@app.post("/tickets", status_code=201)
def create_ticket(body: TicketCreate) -> dict:
    return agent.create_ticket(body.title, body.description, body.category,
                               requester=body.requester)


@app.get("/tickets")
def list_tickets(status: str | None = None) -> list[dict]:
    return agent.tickets.list_all(status=status)


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str) -> dict:
    ticket = agent.get_ticket_status(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"No ticket {ticket_id}")
    return ticket


@app.post("/tickets/{ticket_id}/escalate")
def escalate_ticket(ticket_id: str) -> dict:
    ticket = agent.escalate_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"No ticket {ticket_id}")
    return ticket
