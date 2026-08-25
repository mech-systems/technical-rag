from sentence_transformers import SentenceTransformer
import chromadb
import subprocess

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="db")
collection = client.get_collection("knowledge")

question = input("Question: ")

embedding = model.encode(question).tolist()

result = collection.query(
    query_embeddings=[embedding],
    n_results=3
)

documents = [
    doc
    for doc in result["documents"][0]
    if doc.strip()
]

if not documents:
    print("No matching documents found.")
    exit(1)

context = "\n\n".join(documents)

prompt = f"""
Answer ONLY using the provided context.

If the answer is not explicitly contained in the context, respond:
 
"I could not find that information in the knowledge base." 
 
Cite the source document name.
 
Context:
 
{context}
 
Question:
{question}
 
Answer:
"""


response = subprocess.run(
    ["ollama", "run", "granite3-dense:2b"],
    input=prompt,
    capture_output=True,
    text=True
)

print("\n=== ANSWER ===\n")
print(response.stdout)

print("\n=== SOURCES ===\n")

for i, source in enumerate(result["ids"][0], start=1):
    print(f"{i}. {source}.md")
