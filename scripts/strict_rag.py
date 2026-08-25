from pathlib import Path
import subprocess

import chromadb
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "db"

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path=str(DB_PATH))
collection = client.get_collection("knowledge")

while True:
    question = input("\nQuestion (exit to quit): ").strip()

    if not question or question.lower() in {"exit", "quit"}:
        break

    embedding = model.encode(
        question,
        normalize_embeddings=False,
    ).tolist()

    result = collection.query(
        query_embeddings=[embedding],
        n_results=3,
        include=["documents", "metadatas"],
    )

    documents = [
        document
        for document in result["documents"][0]
        if document.strip()
    ]

    if not documents:
        print("No matching documents found.")
        continue

    context = "\n\n".join(documents)

    prompt = f"""
Answer ONLY using the provided context.
If the answer is not explicitly contained in the context, respond:
"I could not find that information in the knowledge base."

Context:
{context}

Question:
{question}

Answer:
"""

    response = subprocess.run(
        ["ollama", "run", "granite4.1:3b"],
        input=prompt,
        capture_output=True,
        text=True,
    )

    print("\n=== ANSWER ===\n")
    print(response.stdout)

    print("\n=== SOURCES ===\n")

    sources = []

    for metadata in result["metadatas"][0]:
        source = metadata.get("source")

        if source and source not in sources:
            sources.append(source)

    for number, source in enumerate(sources, start=1):
        print(f"{number}. {source}")
