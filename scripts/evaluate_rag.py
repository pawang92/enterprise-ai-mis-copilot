from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.knowledge.rag_evaluation import evaluate_retrieval


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate local TF-IDF retrieval against labelled SOP queries."
    )
    parser.add_argument("--k", type=int, default=3, help="Number of retrieved documents to evaluate.")
    args = parser.parse_args()
    result = evaluate_retrieval(k=args.k)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
