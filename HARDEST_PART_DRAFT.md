# Hardest Part — DRAFT (for Himanshu to approve/edit; not final)

> The hardest part was deciding when the agent should answer and when it
> should stop. Retrieval gives a similarity score, but a score is not
> confidence — a question about something the knowledge base doesn't cover
> can still match a doc weakly, and the agent would then answer with the
> wrong doc's text, sounding sure of itself. That is worse than saying
> "I don't know", especially for a helpdesk where a wrong answer can lock
> someone out or send them down the wrong process. So I tuned a cutoff by
> hand on real questions, and built the fallback first: below the cutoff,
> the agent admits the gap and offers to raise a ticket. Getting that
> boundary right — helpful but never confidently wrong — took more
> iterations than the retriever or the ticket tools themselves.

Word count: 132 words. Draft only — Himanshu to approve or rewrite in his
own words before submitting.
