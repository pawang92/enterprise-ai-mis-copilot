class BusinessKnowledgeGraph:
    """Minimal in-memory entity-relation graph for prototype queries."""

    def __init__(self):
        self.triples = [
            ("MED001", "belongs_to", "Cardiology"),
            ("MED002", "belongs_to", "Diabetes Care"),
            ("MED003", "belongs_to", "Respiratory"),
            ("MED004", "belongs_to", "Pain Management"),
            ("MED005", "belongs_to", "Nutrition"),
            ("Sales", "measured_by", "Revenue"),
            ("Sales", "compared_against", "Sales Target"),
            ("Inventory", "measured_by", "Days of Inventory"),
            ("Low Inventory", "requires_review_by", "Inventory Planning"),
            ("Sales Decline", "requires_investigation_by", "Business Analyst"),
        ]

    def query(self, question: str) -> list[dict[str, str]]:
        """Return triples matching explicit entity/relation terms in a query.

        Prefer exact entity matches; this keeps product-specific questions from
        accidentally returning unrelated triples due to common words.
        """
        normalized = question.lower().replace("-", " ")
        exact_entities = [
            (subject, relation, obj)
            for subject, relation, obj in self.triples
            if subject.lower() in normalized or obj.lower() in normalized
        ]

        if exact_entities:
            matches = exact_entities
        else:
            terms = {
                token.strip(".,?!:;()").lower()
                for token in normalized.split()
            }
            matches = []
            for subject, relation, obj in self.triples:
                searchable = {
                    subject.lower(),
                    relation.replace("_", " ").lower(),
                    obj.lower(),
                }
                if any(
                    term in item
                    for term in terms
                    for item in searchable
                    if len(term) >= 4
                ):
                    matches.append((subject, relation, obj))

        return [
            {"subject": subject, "relation": relation, "object": obj}
            for subject, relation, obj in matches
        ]
