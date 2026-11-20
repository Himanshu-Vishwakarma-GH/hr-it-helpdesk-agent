# HR/IT Helpdesk Agent

A demo project built by Himanshu Vishwakarma for the GoAified AI Internship
application. It is a working helpdesk agent: employees ask HR and IT questions
in plain language, the agent retrieves the answer from a local knowledge base,
and it can raise a support ticket, check a ticket's status, or escalate a
ticket to a human.

## What it does

- **RAG answers** — questions like "How do I reset my password?" or "How many
  days of paid leave do I get?" are answered from a local knowledge base of 12
  short IT/HR guides (password reset, VPN, laptop requests, leave policy,
  Wi-Fi, email setup, software installs, printers, remote-work policy,
  expenses, onboarding, account lockout). Every answer cites its source file.
- **Ticket tools** — the agent can create a support ticket, look up a ticket's
  status by ID (e.g. `TKT-1001`), and escalate a ticket to a human agent.
- **Honest fallback** — if a question is not covered by the knowledge base, the
  agent says so and offers to raise a ticket instead of inventing an answer.

## Stack

Python, FastAPI, LangChain (document loading + text splitting), RAG with a
TF-IDF retriever (scikit-learn), REST APIs, SQLite for the ticket store.

No paid API key is needed. Retrieval is TF-IDF cosine similarity over the KB
chunks — it runs fully offline. Answers are composed from the retrieved KB
passage itself; there is no LLM generating text in this version, so the agent
cannot hallucinate policy that is not in the KB. That trade-off is deliberate
for a helpdesk: a wrong answer is worse than no answer.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the CLI demo / smoke test

```bash
python demo.py
```

This runs the agent end to end without a server: two RAG questions, a ticket
creation, a status lookup, an escalation, and one out-of-KB question to show
the fallback. It prints PASS/FAIL per step and exits 0 when all pass.
It uses a throwaway database; add `--keep-db` to use `data/tickets.db` instead.

## Run the API

```bash
uvicorn main:app --reload --port 8000
```

Interactive docs: http://localhost:8000/docs

Endpoints:

| Method | Path | What it does |
| ------ | ---- | ------------ |
| GET | `/health` | Health check + KB chunk count |
| POST | `/ask` | Ask a question: `{"question": "...", "requester": "employee"}` |
| POST | `/tickets` | Create a ticket directly |
| GET | `/tickets` | List tickets (optional `?status=Open`) |
| GET | `/tickets/{ticket_id}` | Get one ticket, e.g. `TKT-1001` |
| POST | `/tickets/{ticket_id}/escalate` | Escalate a ticket to a human |

Example:

```bash
curl -X POST localhost:8000/ask -H 'Content-Type: application/json' \
  -d '{"question": "How do I reset my password?"}'

curl -X POST localhost:8000/ask -H 'Content-Type: application/json' \
  -d '{"question": "Raise a ticket: my laptop screen keeps flickering"}'

curl localhost:8000/tickets/TKT-1001
```

## How it works

1. `helpdesk/kb_loader.py` reads the Markdown files in `kb/` and splits them
   into overlapping chunks with LangChain's `RecursiveCharacterTextSplitter`,
   keeping the source file in each chunk's metadata.
2. `helpdesk/retriever.py` builds a TF-IDF index over the chunks
   (scikit-learn) and ranks them by cosine similarity to the question.
3. `helpdesk/agent.py` routes the question: ticket-status lookup, escalation,
   ticket creation, or a RAG answer. If the best retrieval score is below
   0.15, or the best chunk covers less than 0.67 of the question's content
   words, the KB is treated as not covering the question and the agent says so
   instead of guessing.
4. `helpdesk/tickets.py` stores tickets in SQLite (`data/tickets.db`),
   with IDs like `TKT-1001` and statuses Open / In Progress / Escalated /
   Resolved.

## Project layout

```
├── kb/                  # 12 knowledge-base guides (Markdown)
├── helpdesk/
│   ├── kb_loader.py     # load + chunk the KB (LangChain)
│   ├── retriever.py     # TF-IDF retriever (scikit-learn)
│   ├── tickets.py       # SQLite ticket store
│   └── agent.py         # router + answer composer + tools
├── main.py              # FastAPI app (REST endpoints)
├── demo.py              # CLI demo + smoke test
├── requirements.txt
├── LOOM_DEMO_SCRIPT.md  # script for the under-5-minute demo video
└── HARDEST_PART_DRAFT.md# draft write-up of the hardest part
```

## Limitations (stated honestly)

- Demo-scale knowledge base: 12 guides, written for this project.
- No LLM: answers come from retrieved KB text, so the agent can only answer
  what the KB covers. That is by design — see the fallback above.
- Single-user, local SQLite ticket store; no auth, no multi-tenancy.
- The retrieval threshold (score 0.15 + content-word coverage 0.67) was tuned
  by hand on the demo questions.
