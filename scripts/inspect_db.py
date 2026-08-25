#!/usr/bin/env python3

from pathlib import Path

import chromadb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "db"
COLLECTION_NAME = "knowledge"


def main():
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_collection(name=COLLECTION_NAME)

    result = collection.get(
        include=["documents", "metadatas"]
    )

    print(f"Collection: {COLLECTION_NAME}")
    print(f"Entries:    {collection.count()}")
    print()

    for document_id, metadata, document in zip(
        result["ids"],
        result["metadatas"],
        result["documents"],
    ):
        print(f"ID:       {document_id}")
        print(f"Metadata: {metadata}")
        print("Document:")
        print(document)
        print("-" * 60)


if __name__ == "__main__":
    main()
