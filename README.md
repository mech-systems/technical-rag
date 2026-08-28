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
- `strict_rag.py`: applies context-only prompting, fallback behavior, distance filtering, source output, and interactive questioning.
- `evaluate.py`: runs retrieval tests, content checks, and answerability evaluation.
- `inspect_db.py`: displays stored document IDs, metadata, and chunk content.
- `Modelfile.strict-rag`: configures deterministic Ollama generation with temperature `0` and seed `42`.

## Requirements

- Linux
- Python 3
- Ollama
- Local Ollama model `granite4.1:3b`

Python dependencies are listed in `requirements.txt`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama pull granite4.1:3b
ollama create strict-rag -f Modelfile.strict-rag
```

## Build the Knowledge Base

Place Markdown files in `docs/`, then run:

```bash
python scripts/ingest.py
```

The ingest process splits each document into chunks. Chunk IDs follow a readable pattern such as `rsync-0` or `borgbackup-0`. The source filename is stored in the ChromaDB metadata.

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

The evaluation separates three concerns:

- Retrieval tests verify that a question retrieves the expected source document.
- Answerability classification verifies whether the system should answer or use the fallback.
- Content validation checks required, alternative, forbidden, and exact answer content.

Example answer-test expectations:

```python
{
    "question": "How do I copy files in archive mode?",
    "answer_expected": True,
    "must_contain_any": ["-a", "--archive"],
    "must_not_contain": ["-A", "--delete"],
}
```

### Evaluation Results

Four repeated runs produced identical answerability results:

- Answerability accuracy: 100.0%
- Answer precision: 100.0%
- Answer recall: 100.0%
- Fallback specificity: 100.0%
- Hallucination rate at the answerability level: 0.0%
- Content validation: 4 of 6 tests passed

Confusion matrix:

```text
                    Answered    Fallback
Answer expected            4           0
Fallback expected          0           2
```

The confusion matrix evaluates only whether the system correctly decides to answer or use the fallback. It does not prove that every generated statement is supported by the retrieved context.

Two answers were correctly classified as answerable but still failed content validation because they contained additional commands or more specific syntax than permitted by the test expectations. The repeated results show that deterministic generation makes the observed behavior reproducible. Answerability and content faithfulness are therefore reported separately.

## Observed Hallucinations

Earlier experiments showed that correct retrieval did not guarantee a fully grounded answer. The local language model sometimes used pretrained knowledge or unsupported inference when retrieved context was thematically related but did not explicitly contain the requested detail.

Observed examples included:

- Naming a specific BorgBackup encryption algorithm without explicit support in the retrieved context
- Producing a concrete command when the evaluated context was insufficient
- Adding commands and options that were not required by the question
- Answering `No` when the knowledge base contained no evidence for either a positive or negative answer

After strengthening the evidence-based fallback rule, unsupported questions in the current test set were rejected reliably across four repeated runs. Content-level issues remain possible when a question is answerable but the model adds details beyond the explicit evidence or test expectations.

A retrieval distance threshold reduces unrelated context but does not prevent unsupported conclusions from thematically relevant chunks. Temperature `0` and seed `42` make failures reproducible, but do not make unsupported statements grounded.

The project does not claim that prompt-based Strict RAG eliminates hallucinations. Instead, it makes failure modes visible through repeatable tests, explicit fallback behavior, retrieved-source output, content validation, and documented limitations.

## Knowledge Base

The example documents cover:

- BorgBackup
- DNS
- rsync
- WireGuard

The BorgBackup reference is based on the [official stable BorgBackup documentation](https://borgbackup.readthedocs.io/_/downloads/en/stable/pdf/).

## Design Decisions

### Local-first

Embeddings, vector storage, retrieval, and answer generation run locally. This keeps the demonstrator independent of cloud APIs and supports privacy-conscious use cases.

### Minimal dependencies

The project intentionally avoids orchestration and RAG frameworks. Individual processing steps remain visible and easy to inspect.

### Explicit source attribution

The source filename is stored during ingestion and returned with retrieval results. This shows which documents were supplied to the model, but does not prove that every generated statement is supported by them.

### Separate retrieval and answer evaluation

Good retrieval can still produce an unsupported answer. Testing retrieval, answerability, and content separately makes failures easier to diagnose.

### Reproducible evaluation

Deterministic generation settings reduce variation between runs and make failures easier to compare.

## Known Limitations

- Strict prompting cannot guarantee that a language model never uses pretrained knowledge.
- Retrieved context can be relevant but still insufficient.
- Similarity distance alone is not proof that a passage supports an answer.
- A fixed distance threshold must be calibrated for the embedding model and knowledge base.
- Character-based chunking can split related Markdown content across chunks.
- Source attribution identifies retrieved sources, not necessarily every passage used by the model.
- Deterministic string checks do not measure semantic correctness comprehensively.
- The demonstrator is not designed for production workloads, access control, multi-user operation, or untrusted documents.

## Security and Data Scope

- Do not add customer, confidential, personal, or company-internal data.
- Use public, synthetic, or self-written documentation.
- Treat retrieved document text as data, not as trusted instructions.
- Review generated commands before executing them.

## Project Status

The core demonstrator is complete:

- ingestion and chunking
- embeddings and vector storage
- semantic retrieval and distance filtering
- local RAG and strict prompting
- source attribution
- deterministic generation settings
- retrieval, answerability, and content evaluation
- documented hallucination behavior

Further work should focus on small, measurable improvements rather than additional infrastructure.

## License

See `LICENSE`.
