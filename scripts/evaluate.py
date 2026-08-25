#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "db"

# Muss dem Modell aus ingest.py entsprechen.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

TEST_CASES = [
    {
        "question": "How can I verify a Borg repository?",
        "expected_source": "borgbackup.md",
    },
    {
        "question": "What is WireGuard?",
        "expected_source": "wireguard.md",
    },
    {
        "question": "What does DNS do?",
        "expected_source": "dns.md",
    },
]


def source_filename(metadata):
    """Liest den Dateinamen aus den Chroma-Metadaten."""

    if not metadata:
        return None

    for key in ("source", "filename", "file", "path"):
        value = metadata.get(key)

        if value:
            return Path(str(value)).name

    return None


def matches(actual_source, expected_source):
    """Vergleicht tatsächliche und erwartete Quelldatei."""

    return actual_source == expected_source


def evaluator_self_test():
    """Prüft die PASS/FAIL-Logik ohne ChromaDB."""

    test_data = [
        ("borgbackup.md", "borgbackup.md", True),
        ("wireguard.md", "borgbackup.md", False),
        (None, "dns.md", False),
    ]

    print("Evaluator self-test")
    print()

    failures = 0

    for actual, expected, expected_result in test_data:
        actual_result = matches(actual, expected)
        passed = actual_result == expected_result

        print(f"Actual source:   {actual}")
        print(f"Expected source: {expected}")
        print(f"Expected result: {expected_result}")
        print(f"Actual result:   {actual_result}")
        print("PASS" if passed else "FAIL")
        print()

        if not passed:
            failures += 1

    if failures:
        print(f"Self-test failed: {failures} error(s)")
        return 1

    print("Self-test passed")
    return 0


def open_collection():
    """Öffnet die einzige Collection der lokalen ChromaDB."""

    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}", file=sys.stderr)
        return None

    client = chromadb.PersistentClient(path=str(DB_PATH))
    collections = client.list_collections()

    if not collections:
        print(f"No Chroma collection found in: {DB_PATH}", file=sys.stderr)
        return None

    if len(collections) > 1:
        print("Multiple collections found:", file=sys.stderr)

        for collection in collections:
            print(f"  {collection.name}", file=sys.stderr)

        print(
            "Set COLLECTION_NAME explicitly in evaluate.py.",
            file=sys.stderr,
        )
        return None

    collection_name = collections[0].name
    collection = client.get_collection(name=collection_name)

    print(f"Database:   {DB_PATH}")
    print(f"Collection: {collection_name}")
    print(f"Documents:  {collection.count()}")
    print()

    return collection


def run_retrieval_tests():
    """Führt die definierten Retrieval-Tests aus."""

    collection = open_collection()

    if collection is None:
        return 1

    model = SentenceTransformer(EMBEDDING_MODEL)

    passed_count = 0

    for number, test_case in enumerate(TEST_CASES, start=1):
        question = test_case["question"]
        expected_source = test_case["expected_source"]

        # Diese Einstellung muss zu ingest.py passen.
        embedding = model.encode(
            question,
            normalize_embeddings=False,
        ).tolist()

        result = collection.query(
            query_embeddings=[embedding],
            n_results=1,
            include=["metadatas", "distances", "documents"],
        )

        if not result["ids"] or not result["ids"][0]:
            print(f"Test {number}")
            print(f"Question: {question}")
            print("FAIL: no result")
            print()
            continue

        metadata = result["metadatas"][0][0] or {}
        distance = result["distances"][0][0]
        actual_source = source_filename(metadata)

        passed = matches(actual_source, expected_source)

        print(f"Test {number}")
        print(f"Question: {question}")
        print(f"Expected: {expected_source}")
        print(f"Actual:   {actual_source}")
        print(f"Distance: {distance:.4f}")
        print(f"Metadata: {metadata}")
        print("PASS" if passed else "FAIL")
        print()

        if passed:
            passed_count += 1

    total_count = len(TEST_CASES)

    print(f"{passed_count}/{total_count} retrieval tests passed")

    return 0 if passed_count == total_count else 1


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate retrieval from the local ChromaDB."
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Test only the PASS/FAIL evaluation logic.",
    )

    args = parser.parse_args()

    if args.self_test:
        return evaluator_self_test()

    return run_retrieval_tests()


if __name__ == "__main__":
    raise SystemExit(main())
