"""CLI demo + smoke test for the helpdesk agent.

Runs the agent end to end in-process (no server needed):
  1. Ask a password question       -> RAG answer from the KB, with source
  2. Ask a leave-policy question   -> RAG answer from the KB, with source
  3. Raise a ticket                -> ticket created with a TKT- id
  4. Check that ticket's status    -> status returned
  5. Escalate the ticket           -> status becomes Escalated
  6. Ask something outside the KB  -> honest "not in the KB" fallback

Usage:
    python demo.py            # uses a throwaway database in a temp dir
    python demo.py --keep-db  # keep data/tickets.db instead (default store)

Exits 0 when every step passes, 1 otherwise.
"""
import argparse
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from helpdesk.agent import HelpdeskAgent
from helpdesk.tickets import TicketStore


def check(name: str, ok: bool, detail: str = "") -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep-db", action="store_true",
                        help="use the default data/tickets.db instead of a temp DB")
    args = parser.parse_args()

    if args.keep_db:
        store = TicketStore()
    else:
        tmp = Path(tempfile.mkdtemp(prefix="helpdesk-demo-"))
        store = TicketStore(tmp / "tickets.db")

    agent = HelpdeskAgent(ticket_store=store)
    print(f"Agent ready — KB loaded: {agent.kb_docs} chunks from kb/")
    results: list[bool] = []

    print("\n1. RAG: password reset")
    r = agent.ask("How do I reset my password?")
    print("   " + r["answer"].split("\n")[0])
    results.append(check("answered from password-reset doc",
                         r["intent"] == "rag_answer"
                         and r["sources"] and r["sources"][0]["source"] == "01-password-reset.md",
                         f"top source: {r['sources'][0]['source'] if r['sources'] else 'none'}"))

    print("\n2. RAG: leave policy")
    r = agent.ask("How many days of paid leave do I get per year?")
    print("   " + r["answer"].split("\n")[0])
    results.append(check("answered from leave-policy doc",
                         r["intent"] == "rag_answer"
                         and r["sources"] and r["sources"][0]["source"] == "04-leave-policy.md",
                         f"top source: {r['sources'][0]['source'] if r['sources'] else 'none'}"))

    print("\n3. Tool: raise a ticket")
    r = agent.ask("Raise a ticket: my laptop screen keeps flickering")
    ticket_id = (r["ticket"] or {}).get("ticket_id", "")
    print("   " + r["answer"])
    results.append(check("ticket created with a TKT- id",
                         r["intent"] == "ticket_created" and ticket_id.startswith("TKT-"),
                         ticket_id))

    print("\n4. Tool: ticket status lookup")
    r = agent.ask(f"What is the status of ticket {ticket_id}?")
    print("   " + r["answer"])
    results.append(check("status lookup returns the ticket",
                         r["intent"] == "ticket_status"
                         and r["ticket"] and r["ticket"]["status"] == "Open",
                         f"status: {(r['ticket'] or {}).get('status')}"))

    print("\n5. Tool: escalate the ticket")
    r = agent.ask(f"Please escalate ticket {ticket_id}")
    print("   " + r["answer"])
    results.append(check("ticket escalated",
                         r["intent"] == "ticket_escalated"
                         and r["ticket"] and r["ticket"]["status"] == "Escalated",
                         f"status: {(r['ticket'] or {}).get('status')}"))

    print("\n6. RAG fallback: question outside the KB")
    r = agent.ask("What is the Wi-Fi password for the Tokyo office?")
    print("   " + r["answer"].split("\n")[0])
    results.append(check("honest fallback, no invented answer",
                         r["intent"] == "rag_no_answer",
                         f"intent: {r['intent']}"))

    store.close()
    if not args.keep_db:
        shutil.rmtree(tmp, ignore_errors=True)

    passed = sum(results)
    print(f"\n{passed}/{len(results)} smoke-test steps passed.")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
