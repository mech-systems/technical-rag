from sentence_transformers import SentenceTransformer
import chromadb
from pathlib import Path

DOC_PATH = Path(__file__).parent.parent / "docs"

print(f"Searching in: {DOC_PATH}")

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="db")
collection = client.get_or_create_collection("knowledge")

for file in DOC_PATH.glob("*.md"):

    print(f"Loading: {file.name}")

    text = file.read_text(encoding="utf-8")

    embedding = model.encode(text).tolist()

    collection.add(
        documents=[text],
        embeddings=[embedding],
        ids=[file.stem]
    )

print(f"Documents in collection: {collection.count()}")

print("Done")
