"""Load the local knowledge base (Markdown files in kb/) and split it into
chunks using LangChain's text splitter. Returns LangChain Documents, each
carrying its source file in metadata.
"""
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

KB_DIR = Path(__file__).resolve().parent.parent / "kb"


def load_kb(kb_dir: Path = KB_DIR) -> list[Document]:
    """Read every .md file in kb_dir and split it into overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " "],
    )
    docs: list[Document] = []
    for path in sorted(kb_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip() if text else path.stem
        category = ""
        for line in text.splitlines():
            if line.lower().startswith("category:"):
                category = line.split(":", 1)[1].strip()
                break
        for chunk in splitter.split_text(text):
            docs.append(
                Document(
                    page_content=chunk,
                    metadata={"source": path.name, "title": title, "category": category},
                )
            )
    return docs


if __name__ == "__main__":
    documents = load_kb()
    print(f"Loaded {len(documents)} chunks from {KB_DIR}")
    for doc in documents[:3]:
        print("-", doc.metadata["source"], "|", doc.page_content[:80].replace("\n", " "))
