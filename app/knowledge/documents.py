from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
KNOWLEDGE_BASE_DIR = ROOT_DIR / "knowledge_base"


def load_documents():
    documents = []

    for path in sorted(KNOWLEDGE_BASE_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8").strip()

        if content:
            documents.append({
                "source": path.name,
                "text": content,
            })

    return documents