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

## Setup
 
Create virtual environment:
 
```bash
python3 -m venv .venv
source .venv/bin/activate
```
 
Install dependencies:
 
```bash
pip install -r requirements.txt
```

## Requirements
Python 3.14.6


## Observation

Even with a strict prompt, the language model may incorporate
pretrained knowledge that is not explicitly present in the retrieved
documents.

To make this behavior transparent, the demonstrator always displays:

- Generated answer
- Retrieved source documents
- Source file name

## Finding:
Granite3-Dense:2B may supplement answers with model knowledge even
when instructed to answer only from retrieved context.
