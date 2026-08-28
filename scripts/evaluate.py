#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from strict_rag import answer_question, FALLBACK_ANSWER


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

RETRIEVAL_TEST_CASES = [
    {"question": "How can I verify a Borg repository?", "expected_source": "borgbackup.md"},
    {"question": "Does BorgBackup support deduplication?", "expected_source": "borgbackup.md"},
    {"question": "Does BorgBackup support encryption?", "expected_source": "borgbackup.md"},
    {"question": "Which commands are commonly used with BorgBackup?", "expected_source": "borgbackup.md"},
    {"question": "What is WireGuard?", "expected_source": "wireguard.md"},
    {"question": "What does DNS do?", "expected_source": "dns.md"},
]

ANSWER_TEST_CASES = [
    {
        "question": "Does BorgBackup support encryption?",
        "answer_expected": True,
        "must_contain_any": ["yes", "encryption"],
        "must_not_contain": [FALLBACK_ANSWER],
    },
    {
        "question": "Does BorgBackup support deduplication?",
        "answer_expected": True,
        "must_contain_any": ["yes", "deduplication"],
        "must_not_contain": [FALLBACK_ANSWER],
    },
    {
        "question": "Which commands are commonly used with BorgBackup?",
        "answer_expected": True,
        "must_contain": ["borg create", "borg prune", "borg check" , "borg extract"],
        "must_not_contain": [
            FALLBACK_ANSWER,
            "borg init",
            "borg compact",
            "--dry-run",
            "verify-data",
        ],
    },
    {
        "question": "How do I restore a BorgBackup archive?",
        "answer_expected": True,
        "must_contain": "borg extract",
        "must_not_contain": [
            FALLBACK_ANSWER,
            "borg prune",
            "borg compact",
        ],
    },
    {
        "question": "Which encryption algorithm does BorgBackup use?",
        "answer_expected": False,
        "exact_answer": FALLBACK_ANSWER,
    },
    {
        "question": "Does DNS use BorgBackup for encryption?",
        "answer_expected": False,
        "exact_answer": FALLBACK_ANSWER,
    },
]


def source_filename(metadata):
    if not metadata:
        return None

    for key in ("source", "filename", "file", "path"):
        value = metadata.get(key)
        if value:
            return Path(str(value)).name

    return None


def matches(actual_source, expected_source):
    return actual_source == expected_source


def check_answer(answer, test_case):
    normalized_answer = answer.strip().casefold()

    if "exact_answer" in test_case:
        expected = test_case["exact_answer"].strip().casefold()
        return normalized_answer == expected

    for expected in test_case.get("must_contain", []):
        if expected.casefold() not in normalized_answer:
            return False

    alternatives = test_case.get("must_contain_any", [])
    if alternatives and not any(
        alternative.casefold() in normalized_answer
        for alternative in alternatives
    ):
        return False

    for forbidden in test_case.get("must_not_contain", []):
        if forbidden.casefold() in normalized_answer:
            return False

    return True


def update_confusion_matrix(matrix, answer, answer_expected):
    used_fallback = (
        answer.strip().casefold() == FALLBACK_ANSWER.casefold()
    )

    if answer_expected and not used_fallback:
        matrix["tp"] += 1
        return "TP"
    if answer_expected and used_fallback:
        matrix["fn"] += 1
        return "FN"
    if not answer_expected and not used_fallback:
        matrix["fp"] += 1
        return "FP"

    matrix["tn"] += 1
    return "TN"


def safe_divide(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def print_confusion_matrix(matrix):
    tp = matrix["tp"]
    fp = matrix["fp"]
    fn = matrix["fn"]
    tn = matrix["tn"]
    total = tp + fp + fn + tn

    print("\n=== ANSWERABILITY CONFUSION MATRIX ===\n")
    print("                    Answered    Fallback")
    print(f"Answer expected     {tp:8}    {fn:8}")
    print(f"Fallback expected   {fp:8}    {tn:8}")
    print()
    print(f"Accuracy:             {safe_divide(tp + tn, total):.1%}")
    print(f"Answer precision:     {safe_divide(tp, tp + fp):.1%}")
    print(f"Answer recall:        {safe_divide(tp, tp + fn):.1%}")
    print(f"Fallback specificity: {safe_divide(tn, tn + fp):.1%}")
    print(f"Hallucination rate:   {safe_divide(fp, fp + tn):.1%}")


def evaluator_self_test():
    retrieval_checks = [
        ("borgbackup.md", "borgbackup.md", True),
        ("wireguard.md", "borgbackup.md", False),
        (None, "dns.md", False),
    ]
    answer_checks = [
        ("Yes", {"must_contain_any": ["yes", "encryption"]}, True),
        (FALLBACK_ANSWER, {"exact_answer": FALLBACK_ANSWER}, True),
        (
            f"{FALLBACK_ANSWER} Source: borgbackup.md",
            {"exact_answer": FALLBACK_ANSWER},
            False,
        ),
    ]

    failures = 0
    print("Evaluator self-test\n")

    for actual, expected, expected_result in retrieval_checks:
        passed = matches(actual, expected) == expected_result
        print("PASS" if passed else "FAIL")
        failures += not passed

    for answer, test_case, expected_result in answer_checks:
        passed = check_answer(answer, test_case) == expected_result
        print("PASS" if passed else "FAIL")
        failures += not passed

    print("\nSelf-test passed" if not failures else f"\nSelf-test failed: {failures}")
    return 0 if not failures else 1


def open_collection():
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}", file=sys.stderr)
        return None

    client = chromadb.PersistentClient(path=str(DB_PATH))
    collections = client.list_collections()

    if len(collections) != 1:
        print("Expected exactly one Chroma collection.", file=sys.stderr)
        return None

    collection = client.get_collection(name=collections[0].name)
    print(f"Database:   {DB_PATH}")
    print(f"Collection: {collection.name}")
    print(f"Documents:  {collection.count()}\n")
    return collection


def run_retrieval_tests():
    collection = open_collection()
    if collection is None:
        return 1

    model = SentenceTransformer(EMBEDDING_MODEL)
    passed_count = 0
    print("=== RETRIEVAL TESTS ===\n")

    for number, test_case in enumerate(RETRIEVAL_TEST_CASES, start=1):
        question = test_case["question"]
        expected_source = test_case["expected_source"]
        embedding = model.encode(
            question,
            normalize_embeddings=False,
        ).tolist()
        result = collection.query(
            query_embeddings=[embedding],
            n_results=1,
            include=["metadatas", "distances"],
        )

        if not result["ids"] or not result["ids"][0]:
            print(f"Test {number}: FAIL, no result\n")
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

        passed_count += passed

    total = len(RETRIEVAL_TEST_CASES)
    print(f"{passed_count}/{total} retrieval tests passed")
    return 0 if passed_count == total else 1


def run_answer_tests():
    passed_count = 0
    matrix = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    print("\n=== STRICT RAG ANSWER TESTS ===\n")

    for number, test_case in enumerate(ANSWER_TEST_CASES, start=1):
        question = test_case["question"]

        try:
            result = answer_question(question)
            if isinstance(result, tuple):
                answer, sources = result
            else:
                answer, sources = result, []

            answer = str(answer).strip()
            passed = check_answer(answer, test_case)
            classification = update_confusion_matrix(
                matrix,
                answer,
                test_case["answer_expected"],
            )
        except Exception as error:
            answer = f"ERROR: {error}"
            sources = []
            passed = False
            classification = "ERROR"

        print(f"Test {number}")
        print(f"Question: {question}")
        print(f"Answer:   {answer}")
        print(f"Classification: {classification}")

        source_names = []
        for source in sources:
            name = source.get("source") if isinstance(source, dict) else str(source)
            if name and name not in source_names:
                source_names.append(name)
        if source_names:
            print(f"Sources:  {', '.join(source_names)}")

        print("PASS" if passed else "FAIL")
        print()
        passed_count += passed

    total = len(ANSWER_TEST_CASES)
    print(f"{passed_count}/{total} answer tests passed")
    print_confusion_matrix(matrix)
    return 0 if passed_count == total else 1


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate retrieval and Strict RAG answers."
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--retrieval-only", action="store_true")
    parser.add_argument("--answers-only", action="store_true")
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
