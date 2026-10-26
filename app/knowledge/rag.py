from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.knowledge.documents import load_documents


class LocalRAG:
    def __init__(self):
        self.documents = load_documents()

        if not self.documents:
            raise ValueError(
                "No knowledge documents found in knowledge_base/"
            )

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
        )

        self.matrix = self.vectorizer.fit_transform(
            [doc["text"] for doc in self.documents]
        )

    def retrieve(self, question: str, top_k: int = 3):
        if not question.strip():
            return []

        query_vector = self.vectorizer.transform([question])
        scores = cosine_similarity(
            query_vector, self.matrix
        ).ravel()

        ranked_indices = scores.argsort()[::-1][:top_k]
        results = []

        for index in ranked_indices:
            score = float(scores[index])

            if score <= 0:
                continue

            doc = self.documents[index]
            results.append({
                "source": doc["source"],
                "score": round(score, 4),
                "text": doc["text"],
            })

        return results

    def answer(self, question: str):
        results = self.retrieve(question)

        if not results:
            return {
                "answer": (
                    "I could not find relevant supporting "
                    "information in the available SOP documents."
                ),
                "sources": [],
            }

        context = "\n\n".join(
            f"Source: {item['source']}\n{item['text']}"
            for item in results
        )

        # Extractive, deterministic baseline; no LLM required.
        return {
            "answer": (
                "Relevant information retrieved from the "
                "available SOP documents:\n\n" + context
            ),
            "sources": [
                {
                    "source": item["source"],
                    "score": item["score"],
                }
                for item in results
            ],
        }