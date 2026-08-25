from sentence_transformers import SentenceTransformer
import chromadb
 
model = SentenceTransformer("all-MiniLM-L6-v2")
 
client = chromadb.PersistentClient(path="db")
collection = client.get_collection("knowledge")
print(collection.count())
 
question = input("Question: ")
 
embedding = model.encode(question).tolist()
 
result = collection.query(
    query_embeddings=[embedding],
    n_results=3
)
 
for i, doc in enumerate(result["documents"][0], start=1):
    print(f"\n=== Result {i} ===\n")
    print(doc)

