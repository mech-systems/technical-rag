# Technical RAG

A small, fully local Retrieval-Augmented Generation demonstrator for technical documentation.

The project ingests Markdown files, creates local embeddings, stores document chunks in ChromaDB, retrieves relevant context, and generates answers through a local Ollama model. Retrieved sources are shown to make answers traceable.

This is a learning and portfolio project, not a production system. It uses public or self-written technical documentation and contains no customer or company data.

## Features

- Fully local execution on Linux
- Markdown documents as the knowledge base
- SentenceTransformers embeddings with `all-MiniLM-L6-v2`
- Persistent ChromaDB vector storage
- Chunked document ingestion with overlap
- Semantic search
- Local answer generation through Ollama
- Strict RAG mode with a defined fallback answer
- Source attribution based on ChromaDB metadata
- Automated retrieval and answer tests
- German and English questions

## Architecture

```text
Markdown documents
        |
        v
scripts/ingest.py
        |
        v
SentenceTransformers embeddings
        |
        v
ChromaDB collection
        |
        v
semantic retrieval
        |
        v
retrieved context + strict prompt
        |
        v
local Ollama model
        |
        v
answer + retrieved sources
```

## Project Structure

```text
technical-rag/
├── docs/
│   ├── borgbackup.md
│   ├── dns.md
│   ├── rsync.md
│   └── wireguard.md
├── scripts/
│   ├── evaluate.py
│   ├── ingest.py
│   ├── inspect_db.py
│   ├── query.py
│   ├── rag.py
│   └── strict_rag.py
├── README.md
├── requirements.txt
├── LICENSE
└── .gitignore
```

## Components

- `ingest.py`: reads Markdown files, splits them into overlapping chunks, creates embeddings, and rebuilds the ChromaDB collection.
- `query.py`: performs semantic retrieval without answer generation.
- `rag.py`: demonstrates basic retrieval followed by local answer generation.
- `strict_rag.py`: applies stricter context-only prompting, a fallback response, source output, and interactive questioning.
- `evaluate.py`: runs retrieval tests and Strict RAG answer tests.
- `inspect_db.py`: displays stored document IDs, metadata, and chunk content.

## Requirements

- Linux
- Python 3
- Ollama
- Local Ollama model `granite4.1:3b`

Python dependencies are listed in `requirements.txt`.

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Make sure Ollama is installed and the configured model is available:

```bash
ollama pull granite4.1:3b
```

## Build the Knowledge Base

Place Markdown files in `docs/`, then run:

```bash
python scripts/ingest.py
```

The ingest process splits each document into chunks. Chunk IDs follow a readable pattern such as:

```text
rsync-0
rsync-1
borgbackup-0
```

The source filename is stored in the ChromaDB metadata.

## Usage

### Semantic Search

```bash
python scripts/query.py
```

### Basic RAG

```bash
python scripts/rag.py
```

### Strict RAG

```bash
python scripts/strict_rag.py
```

Strict RAG runs interactively. Enter `exit` or `quit` to stop.

Example question:

```text
How do I copy files in archive mode?
```

A grounded answer should identify `-a` or `--archive` and explain that archive mode is equivalent to `-rlptgoD`, provided this information was retrieved from the knowledge base.

## Evaluation

Run the automated evaluation:

```bash
python scripts/evaluate.py
```

The evaluation covers two areas:

- Retrieval tests verify that a question retrieves the expected source document.
- Answer tests verify expected content, forbidden content, and exact fallback responses.

Example answer-test expectations:

```python
{
    "question": "How do I copy files in archive mode?",
    "must_contain": ["-a", "-rlptgoD"],
    "must_not_contain": ["-A", "--delete"],
}
```

`must_not_contain` is useful for detecting unsupported additions and known model mistakes.

## Knowledge Base

The example documents cover technical topics such as:

- BorgBackup
- DNS
- rsync
- WireGuard

The BorgBackup reference is based on the official stable documentation:

[Official BorgBackup documentation](https://borgbackup.readthedocs.io/_/downloads/en/stable/pdf/)

## Design Decisions

### Local-first

Embeddings, vector storage, retrieval, and answer generation run locally. This keeps the demonstrator independent of cloud APIs and supports privacy-conscious use cases.

### Minimal dependencies

The project intentionally avoids orchestration and RAG frameworks. The individual processing steps remain visible and easy to inspect.

### Explicit source attribution

The source filename is stored during ingestion and returned with retrieval results. This makes it possible to see which documents were supplied to the model.

### Separate retrieval and answer evaluation

A correct answer can still be based on poor retrieval, and good retrieval can still produce an incorrect answer. Testing both stages separately makes failures easier to understand.

## Known Limitations

- A strict prompt cannot guarantee that a language model will never use pretrained knowledge.
- Retrieved context can be relevant but still insufficient to answer a question.
- Similarity distance alone is not proof that a passage supports the answer.
- Character-based chunking can split related Markdown content across chunks.
- Source attribution currently identifies retrieved sources, not necessarily every passage actually used by the model.
- The evaluation uses deterministic string checks and does not measure semantic correctness comprehensively.
- The demonstrator is not designed for production workloads, access control, multi-user operation, or untrusted documents.

## Security and Data Scope

- Do not add customer, confidential, personal, or company-internal data.
- Use public, synthetic, or self-written documentation.
- Treat retrieved document text as data, not as trusted instructions.
- Review generated commands before executing them.

## Project Status

The core demonstrator is complete:

- ingestion
- chunking
- embeddings
- vector storage
- semantic retrieval
- local RAG
- strict prompting
- source attribution
- automated retrieval and answer tests

Further work should focus on small, measurable improvements such as retrieval thresholds, clearer chunk attribution, and evaluation reporting rather than adding unnecessary infrastructure.

## License

See `LICENSE`.
