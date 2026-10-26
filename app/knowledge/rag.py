from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.knowledge.documents import load_documents


class LocalRAG:
    """Small local lexical retriever over Markdown SOP documents."""

    def __init__(self):
        self.documents = load_documents()
        if not self.documents:
            raise ValueError("No knowledge documents found in knowledge_base/")

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
        )
        self.matrix = self.vectorizer.fit_transform(
            [document["text"] for document in self.documents]
        )

    def retrieve(self, question: str, top_k: int = 3) -> list[dict]:
        if not question or not question.strip() or top_k < 1:
            return []

        query_vector = self.vectorizer.transform([question])
        scores = cosine_similarity(query_vector, self.matrix).ravel()
        ranked_indices = scores.argsort()[::-1][:top_k]
        results = []

        for index in ranked_indices:
            score = float(scores[index])
            if score <= 0:
                continue
            document = self.documents[index]
            results.append({
                "source": document["source"],
                "score": round(score, 4),
                "text": document["text"],
            })
        return results

    def answer(self, question: str) -> dict:
        results = self.retrieve(question)
        if not results:
            return {
                "answer": (
                    "I could not find relevant supporting information "
                    "in the available SOP documents."
                ),
                "sources": [],
                "grounded": False,
            }

        context = "\n\n".join(
            f"Source: {item['source']}\n{item['text']}"
            for item in results
        )
        return {
            "answer": (
                "Relevant information retrieved from the available "
                f"SOP documents:\n\n{context}"
            ),
            "sources": [
                {
                    "source": item["source"],
                    "score": item["score"],
                }
                for item in results
            ],
            "grounded": True,
        }
