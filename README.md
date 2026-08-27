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
- Retrieval distance threshold
- Source attribution based on ChromaDB metadata
- Automated retrieval and answer tests
- German and English questions
- Deterministic generation settings for repeatable evaluation

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
semantic retrieval + distance filter
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
├── Modelfile.strict-rag
├── README.md
├── requirements.txt
├── LICENSE
└── .gitignore
```

## Components

- `ingest.py`: reads Markdown files, splits them into overlapping chunks, creates embeddings, and rebuilds the ChromaDB collection.
- `query.py`: performs semantic retrieval without answer generation.
- `rag.py`: demonstrates basic retrieval followed by local answer generation.
- `strict_rag.py`: applies context-only prompting, a fallback response, distance filtering, source output, and interactive questioning.
- `evaluate.py`: runs retrieval tests and Strict RAG answer tests.
- `inspect_db.py`: displays stored document IDs, metadata, and chunk content.
- `Modelfile.strict-rag`: configures deterministic Ollama generation with temperature `0` and seed `42`.

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

Make sure Ollama is installed and the base model is available:

```bash
ollama pull granite4.1:3b
```

Create the configured Strict RAG model:

```bash
ollama create strict-rag -f Modelfile.strict-rag
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

A grounded answer should identify `-a` or `--archive`, provided this information is present in the retrieved context.

## Evaluation

Run all automated tests:

```bash
python scripts/evaluate.py
```

Run only answer tests:

```bash
python scripts/evaluate.py --answers-only
```

Run only retrieval tests:

```bash
python scripts/evaluate.py --retrieval-only
```

The evaluation covers two separate areas:

- Retrieval tests verify that a question retrieves the expected source document.
- Answer tests verify required content, acceptable alternatives, forbidden content, and exact fallback responses.

Example answer-test expectations:

```python
{
    "question": "How do I copy files in archive mode?",
    "must_contain_any": ["-a", "--archive"],
    "must_not_contain": ["-A", "--delete"],
}
```

`must_not_contain` helps detect unsupported additions and known model mistakes. These checks are intentionally simple and transparent rather than a complete semantic evaluation.

## Observed Hallucinations

The experiments show that correct retrieval does not guarantee a fully grounded answer. The local language model may still use pretrained knowledge or make unsupported inferences when the retrieved topic is familiar but the requested detail is absent.

Observed examples include:

- Naming a specific BorgBackup encryption algorithm even though the retrieved context did not specify one.
- Producing a concrete `borg extract` command when the evaluated context was expected to be insufficient.
- Expanding a request for commonly used Borg commands with additional commands and options not required by the test.
- Answering `No` when the knowledge base contained no evidence for either a positive or a negative answer.

These cases are retained as negative tests. They demonstrate the difference between:

- retrieving a thematically relevant document,
- finding explicit evidence for the requested fact,
- and generating an answer that remains within that evidence.

A retrieval distance threshold reduces unrelated context, but it does not prevent unsupported conclusions from thematically relevant chunks. Setting temperature to `0` and seed to `42` makes failures more reproducible, but does not make unsupported answers factually grounded.

The project therefore does not claim that prompt-based Strict RAG eliminates hallucinations. Instead, it makes them visible through repeatable tests, explicit fallback behavior, retrieved-source output, and documented limitations.

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

The source filename is stored during ingestion and returned with retrieval results. This shows which documents were supplied to the model. It does not prove that every generated statement is supported by those documents.

### Separate retrieval and answer evaluation

A correct answer can still be based on poor retrieval, and good retrieval can still produce an unsupported answer. Testing both stages separately makes failures easier to understand.

### Reproducible evaluation

Deterministic generation settings reduce variation between runs. This makes repeated failures easier to compare and investigate.

## Known Limitations

- A strict prompt cannot guarantee that a language model will never use pretrained knowledge.
- Retrieved context can be relevant but still insufficient to answer a question.
- Similarity distance alone is not proof that a passage supports the answer.
- A fixed distance threshold must be calibrated for the current embedding model and knowledge base.
- Character-based chunking can split related Markdown content across chunks.
- Source attribution identifies retrieved sources, not necessarily every passage actually used by the model.
- Deterministic string checks do not measure semantic correctness comprehensively.
- Known negative tests can detect repeatable failures, but not every possible hallucination.
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
- retrieval distance filtering
- local RAG
- strict prompting
- source attribution
- deterministic generation settings
- automated retrieval and answer tests
- documented hallucination behavior

Further work should focus on small and measurable improvements rather than additional infrastructure.

## License

See `LICENSE`.
