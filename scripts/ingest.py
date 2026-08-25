#!/usr/bin/env python3

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_PATH = PROJECT_ROOT / "docs"
DB_PATH = PROJECT_ROOT / "db"

COLLECTION_NAME = "knowledge"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
NORMALIZE_EMBEDDINGS = False


def load_documents():
    documents = []

    for file_path in sorted(DOCS_PATH.glob("*.md")):
        content = file_path.read_text(encoding="utf-8").strip()

        if not content:
            print(f"Skipping empty document: {file_path.name}")
            continue

        documents.append(
            {
                "id": file_path.stem,
                "content": content,
                "source": file_path.name,
            }
        )

    return documents


def main():
    documents = load_documents()

    if not documents:
        raise SystemExit(f"No Markdown documents found in: {DOCS_PATH}")

    print(f"Documents found: {len(documents)}")
    print(f"Database:        {DB_PATH}")
    print(f"Collection:      {COLLECTION_NAME}")
    print(f"Embedding model: {EMBEDDING_MODEL}")
    print()

    model = SentenceTransformer(EMBEDDING_MODEL)

    texts = [document["content"] for document in documents]

    embeddings = model.encode(
        texts,
        normalize_embeddings=NORMALIZE_EMBEDDINGS,
        show_progress_bar=True,
    ).tolist()

    client = chromadb.PersistentClient(path=str(DB_PATH))

    existing_collections = {
        collection.name for collection in client.list_collections()
    }

    if COLLECTION_NAME in existing_collections:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"Deleted existing collection: {COLLECTION_NAME}")

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=None,
    )

    collection.add(
        ids=[document["id"] for document in documents],
        documents=texts,
        embeddings=embeddings,
        metadatas=[
            {
                "source": document["source"],
            }
            for document in documents
        ],
    )

    print()

    for document in documents:
        print(f"Added: {document['source']}")

    print()
    print(f"Ingest completed: {collection.count()} documents")


if __name__ == "__main__":
    main()
