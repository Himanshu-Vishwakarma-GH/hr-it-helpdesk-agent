# Loom Demo Script — HR/IT Helpdesk Agent (under 5 minutes)

Total target: ~4 minutes 30 seconds. Record in one take if possible; it is
fine to pause between sections. Show the terminal and the browser (FastAPI
docs page). Keep it to what the project actually does — no claims beyond that.

## 0:00 – 0:20 — Intro (face cam or terminal, your choice)

Say:
> "Hi, I'm Himanshu. This is a helpdesk AI agent I built — it answers
> employee HR and IT questions from a knowledge base, and it can raise
> tickets, check ticket status, and escalate to a human."

On screen: the project folder open, README visible for a second.

## 0:20 – 1:20 — Ask two questions (terminal: `python demo.py`)

Say:
> "First, the knowledge-base part. I'll ask it how to reset a password —
> and then a leave policy question."

On screen: run `python demo.py`. Let it print the first two steps.
Point at the answers and the source file shown next to each one.
Say:
> "Each answer comes from a doc in the knowledge base, and it shows which
> doc it used. Nothing is made up — if the doc doesn't cover it, it says so.
> I'll show that in a minute."

## 1:20 – 2:20 — Raise a ticket, check its status (terminal, same run)

Say:
> "Now the tools. I'll raise a ticket about a flickering laptop screen —
> the agent creates it and gives me a ticket ID."

On screen: the demo's ticket step. Point at the `TKT-1001` ID.
Say:
> "And I can ask for the status of that ticket any time, like this."

On screen: the status-lookup step.

## 2:20 – 3:10 — Escalate the ticket (terminal, same run)

Say:
> "If the issue is urgent, I can escalate it — the ticket goes to a human
> support agent and the status changes."

On screen: the escalation step showing status `Escalated`.

## 3:10 – 4:00 — The honest fallback + the API (terminal, then browser)

Say:
> "Last, the part I care about most. If I ask something the knowledge base
> doesn't cover — say, the Wi-Fi password for an office that isn't in the
> docs — it doesn't guess. It says it doesn't know and offers to raise a
> ticket."

On screen: the fallback step in the demo output.
Then switch to the browser, open `http://localhost:8000/docs`, and say:
> "The same agent also runs as an API — FastAPI, with an ask endpoint and
> ticket endpoints. Same code, same knowledge base."

On screen: the `/docs` page; expand `POST /ask` briefly.

## 4:00 – 4:30 — Wrap-up

Say:
> "Stack is Python, FastAPI, LangChain, and a TF-IDF retriever over a local
> knowledge base — no paid API key, it runs fully offline. The hardest part
> was deciding when the agent should answer and when it should stop and hand
> off to a ticket instead — that's in the write-up in the repo. Thanks for
> watching."

Stop recording. Check the video is under 5 minutes before uploading.
