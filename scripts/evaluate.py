#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from strict_rag import answer_question, FALLBACK_ANSWER


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "db"

# Muss dem Modell aus ingest.py entsprechen.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


RETRIEVAL_TEST_CASES = [
    {
        "question": "How can I verify a Borg repository?",
        "expected_source": "borgbackup.md",
    },
    {
        "question": "Does BorgBackup support deduplication?",
        "expected_source": "borgbackup.md",
    },
    {
        "question": "Does BorgBackup support encryption?",
        "expected_source": "borgbackup.md",
    },
    {
        "question": "Which commands are commonly used with BorgBackup?",
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


ANSWER_TEST_CASES = [
    {
        "question": "Does BorgBackup support encryption?",
        "must_contain": [
            "encryption",
        ],
        "must_not_contain": [
            FALLBACK_ANSWER,
        ],
    },
    {
        "question": "Does BorgBackup support deduplication?",
        "must_contain": [
            "deduplication",
        ],
        "must_not_contain": [
            FALLBACK_ANSWER,
        ],
    },
    {
        "question": "Which commands are commonly used with BorgBackup?",
        "must_contain": [
            "borg create",
            "borg prune",
            "borg check",
        ],
        "must_not_contain": [
            FALLBACK_ANSWER,
        ],
    },
    {
        "question": "How do I restore a BorgBackup archive?",
        "exact_answer": FALLBACK_ANSWER,
    },
    {
        "question": "Which encryption algorithm does BorgBackup use?",
        "exact_answer": FALLBACK_ANSWER,
    },
    {
        "question": "Does DNS use BorgBackup for encryption?",
        "exact_answer": FALLBACK_ANSWER,
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


def check_answer(answer, test_case):
    """Prüft eine generierte Antwort."""

    normalized_answer = answer.strip().casefold()

    if "exact_answer" in test_case:
        expected = test_case["exact_answer"].strip().casefold()
        return normalized_answer == expected

    for expected in test_case.get("must_contain", []):
        if expected.casefold() not in normalized_answer:
            return False

    for forbidden in test_case.get("must_not_contain", []):
        if forbidden.casefold() in normalized_answer:
            return False

    return True


def evaluator_self_test():
    """Prüft die PASS/FAIL-Logik ohne ChromaDB und Ollama."""

    retrieval_tests = [
        ("borgbackup.md", "borgbackup.md", True),
        ("wireguard.md", "borgbackup.md", False),
        (None, "dns.md", False),
    ]

    answer_tests = [
        (
            "BorgBackup supports encryption.",
            {
                "must_contain": ["encryption"],
                "must_not_contain": [FALLBACK_ANSWER],
            },
            True,
        ),
        (
            FALLBACK_ANSWER,
            {
                "exact_answer": FALLBACK_ANSWER,
            },
            True,
        ),
        (
            "BorgBackup uses AES encryption.",
            {
                "exact_answer": FALLBACK_ANSWER,
            },
            False,
        ),
    ]

    print("Evaluator self-test")
    print()

    failures = 0

    for actual, expected, expected_result in retrieval_tests:
        actual_result = matches(actual, expected)
        passed = actual_result == expected_result

        print(f"Retrieval: {actual} / {expected}")
        print("PASS" if passed else "FAIL")
        print()

        if not passed:
            failures += 1

    for answer, test_case, expected_result in answer_tests:
        actual_result = check_answer(answer, test_case)
        passed = actual_result == expected_result

        print(f"Answer: {answer}")
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
        print(
            f"No Chroma collection found in: {DB_PATH}",
            file=sys.stderr,
        )
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

    print("=== RETRIEVAL TESTS ===")
    print()

    for number, test_case in enumerate(
        RETRIEVAL_TEST_CASES,
        start=1,
    ):
        question = test_case["question"]
        expected_source = test_case["expected_source"]

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
        print("PASS" if passed else "FAIL")
        print()

        if passed:
            passed_count += 1

    total_count = len(RETRIEVAL_TEST_CASES)

    print(
        f"{passed_count}/{total_count} retrieval tests passed"
    )

    return 0 if passed_count == total_count else 1


def run_answer_tests():
    """Führt die Strict-RAG-Antworttests aus."""

    passed_count = 0

    print()
    print("=== STRICT RAG ANSWER TESTS ===")
    print()

    for number, test_case in enumerate(
        ANSWER_TEST_CASES,
        start=1,
    ):
        question = test_case["question"]

        try:
            answer, sources = answer_question(question)
            passed = check_answer(answer, test_case)
        except Exception as error:
            answer = f"ERROR: {error}"
            sources = []
            passed = False

        print(f"Test {number}")
        print(f"Question: {question}")
        print(f"Answer:   {answer}")

        if sources:
            source_names = []

            for source in sources:
                name = source.get("source")

                if name and name not in source_names:
                    source_names.append(name)

            print(f"Sources:  {', '.join(source_names)}")

        print("PASS" if passed else "FAIL")
        print()

        if passed:
            passed_count += 1

    total_count = len(ANSWER_TEST_CASES)

    print(
        f"{passed_count}/{total_count} answer tests passed"
    )

    return 0 if passed_count == total_count else 1


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate retrieval and Strict RAG answers."
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Test only the PASS/FAIL evaluation logic.",
    )

    parser.add_argument(
        "--retrieval-only",
        action="store_true",
        help="Run only retrieval tests.",
    )

    parser.add_argument(
        "--answers-only",
        action="store_true",
        help="Run only Strict RAG answer tests.",
    )

    args = parser.parse_args()

    if args.self_test:
        return evaluator_self_test()

    if args.retrieval_only:
        return run_retrieval_tests()

    if args.answers_only:
        return run_answer_tests()

    retrieval_result = run_retrieval_tests()
    answer_result = run_answer_tests()

    return 0 if retrieval_result == 0 and answer_result == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
