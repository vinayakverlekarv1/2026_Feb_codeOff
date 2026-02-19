"""Load and expose the knowledge base for static company questions."""
import os

# Default path relative to project root (where main is run from)
DEFAULT_KB_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base.txt")


def load_knowledge_base(path: str | None = None) -> str:
    """Load full content of knowledge_base.txt."""
    p = path or DEFAULT_KB_PATH
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def search_knowledge_base(query: str, path: str | None = None) -> str:
    """
    Search the knowledge base for information relevant to the query.
    Returns the full KB content so the LLM can extract the answer in UK English.
    """
    return load_knowledge_base(path)
