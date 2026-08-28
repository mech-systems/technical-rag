#!/usr/bin/env python3

from pathlib import Path
import subprocess

import chromadb
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "db"

COLLECTION_NAME = "knowledge"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

OLLAMA_COMMAND = "/usr/local/bin/ollama"
#OLLAMA_MODEL = "granite4.1:3b"
#adding to the model PARAMETER temperature 0 and PARAMETER seed 42
OLLAMA_MODEL = "strict-rag"

RESULT_COUNT = 5
MAX_DISTANCE = 1.35

FALLBACK_ANSWER = (
    "I could not find that information in the knowledge base."
)


model = SentenceTransformer(EMBEDDING_MODEL)
client = chromadb.PersistentClient(path=str(DB_PATH))
collection = client.get_collection(COLLECTION_NAME)

def answer_question(question):
    question = question.strip()

    query_embedding = model.encode(question).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=RESULT_COUNT,
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    document_ids = results["ids"][0]

    relevant_results = [
        {
            "id": document_id,
            "document": document,
            "metadata": metadata,
            "distance": distance,
        }
        for document_id, document, metadata, distance in zip(
            document_ids,
            documents,
            metadatas,
            distances,
        )
        if document.strip() and distance <= MAX_DISTANCE
    ]

    if not relevant_results:
        return FALLBACK_ANSWER, []

    context = "\n\n".join(
        f"[source: {item['metadata'].get('source', 'unknown')}]\n"
        f"{item['document']}"
        for item in relevant_results
    )

    prompt = f"""
You answer questions using only the supplied context.

NON-NEGOTIABLE RULES
- A thematically relevant context is not sufficient evidence.
- Answer only if the context explicitly states the requested fact,
command purpose, option meaning, or relationship.

If explicit evidence is missing, return exactly:
I could not find that information in the knowledge base.
- Use only information explicitly stated in the context.
- Answer in the same language as the question.
- Do not use prior knowledge or assumptions.
- Do not infer a negative answer from missing information.
- Do not add commands or options not required by the question.
- Preserve commands, filenames, options, and values exactly.
- If the context is insufficient, return exactly:
{FALLBACK_ANSWER}

CONTEXT

{context}

QUESTION

{question}

REQUIRED OUTPUT

Return only the final answer.
"""

    result = subprocess.run(
        [OLLAMA_COMMAND, "run", OLLAMA_MODEL],
        input=prompt,
        text=True,
        capture_output=True,
        check=True,
    )

    answer = result.stdout.strip()

    sources = [
        {
            "source": item["metadata"].get("source", "unknown"),
            "chunk": item["metadata"].get("chunk", item["id"]),
            "distance": item["distance"],
        }
        for item in relevant_results
    ]

    return answer, sources

def main():
    print("Strict RAG interactive mode")
    print("Enter 'exit' or 'quit' to stop.")

    while True:
        try:
            question = input("\nQuestion: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if question.casefold() in {"exit", "quit"}:
            print("Exiting.")
            break

        if not question:
            continue

        try:
            answer, sources = answer_question(question)
        except Exception as error:
            print(f"\nERROR: {error}")
            continue

        print("\n=== ANSWER ===\n")
        print(answer)

        print("\n=== RETRIEVED SOURCES ===\n")

        for source in sources:
            print(
                f"- {source['source']}, "
                f"distance: {source['distance']:.4f}"
            )

if __name__ == "__main__":
    main()
