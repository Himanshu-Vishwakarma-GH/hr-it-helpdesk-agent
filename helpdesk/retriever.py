"""TF-IDF retriever over the KB chunks.

No paid embedding API is needed: scikit-learn's TfidfVectorizer turns every
chunk into a vector, and a question is ranked by cosine similarity against
them. Returns the top-k chunks with their scores, so the agent can decide
whether the KB actually covers the question.

A similarity score alone is not enough: a question can share one strong
keyword with a doc ("Wi-Fi password for the Tokyo office" vs the Wi-Fi
troubleshooting guide) and still not be covered by it. So the agent also
checks *coverage*: the fraction of the question's content words that appear
in the best chunk. Both gates must pass before the agent answers from the KB.
"""
import re

from langchain_core.documents import Document
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Below this similarity score the KB is treated as "no good answer".
MIN_SCORE = 0.15
# Below this coverage the best chunk is treated as not covering the question.
# Tuned by hand on the demo questions: real matches cover 1.00 of the
# question's content words; the closest miss (a Wi-Fi-password question
# against the Wi-Fi guide) covers 0.60.
MIN_COVERAGE = 0.67


def coverage(query: str, chunk_text: str) -> float:
    """Fraction of the question's content words present in the chunk."""
    words = [
        w for w in re.findall(r"[a-z0-9]+", query.lower())
        if w not in ENGLISH_STOP_WORDS
    ]
    if not words:
        return 1.0
    text = chunk_text.lower()
    hits = sum(
        1 for w in words if re.search(r"\b" + re.escape(w) + r"\b", text)
    )
    return hits / len(words)


class TfidfRetriever:
    def __init__(self, documents: list[Document]):
        self.documents = documents
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform([d.page_content for d in documents])

    def retrieve(self, query: str, k: int = 3) -> list[tuple[Document, float]]:
        """Return up to k (document, score) pairs, best first."""
        if not self.documents:
            return []
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix)[0]
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [(self.documents[i], float(scores[i])) for i in ranked[:k]]

    def best(self, query: str) -> tuple[Document, float] | None:
        """Return the single best (document, score), or None if the KB is empty."""
        results = self.retrieve(query, k=1)
        return results[0] if results else None

    def covers(self, query: str) -> tuple[Document, float, float] | None:
        """Return (best document, score, coverage) if the KB covers the
        question (score >= MIN_SCORE and coverage >= MIN_COVERAGE),
        else None."""
        result = self.best(query)
        if result is None:
            return None
        doc, score = result
        cov = coverage(query, doc.page_content)
        if score >= MIN_SCORE and cov >= MIN_COVERAGE:
            return doc, score, cov
        return None
