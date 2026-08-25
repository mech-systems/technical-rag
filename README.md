# Technical RAG

Small proof-of-concept Retrieval-Augmented Generation project.

## Current Status

Implemented:

- Markdown document ingestion
- Embedding generation using SentenceTransformers
- ChromaDB vector storage
- Similarity search

Not yet implemented:

- LLM integration
- Context generation
- Answer generation

## Usage

Build index:

```bash
python scripts/ingest.py
```

Query knowledge base:

```bash
python scripts/query.py
```
