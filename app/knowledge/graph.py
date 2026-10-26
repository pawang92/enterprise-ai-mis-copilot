class BusinessKnowledgeGraph:
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

    def query(self, question: str):
        terms = {
            term.strip(".,?!:;").lower()
            for term in question.split()
        }

        matches = []

        for subject, relation, obj in self.triples:
            searchable = {
                subject.lower(),
                relation.lower(),
                obj.lower(),
            }

            if any(
                term in item or item in term
                for term in terms
                for item in searchable
                if len(term) >= 3
            ):
                matches.append({
                    "subject": subject,
                    "relation": relation,
                    "object": obj,
                })

        return matches