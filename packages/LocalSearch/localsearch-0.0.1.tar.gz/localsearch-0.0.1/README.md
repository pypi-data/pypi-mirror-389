# LocalSearch

**LocalSearch** is a lightweight, privacy-first **local semantic search engine** powered by embeddings and LLMs.
It lets you index your local files (like `.txt`, `.pdf`, `.html`) and query them using natural language - without sending your data anywhere.

---

## Features

* 🔍 **Semantic Search** - uses vector embeddings for meaning-based file retrieval
* 🧩 **Modular Components** - plug in your own LLM, embedder, vector store, or metadata backend
* ⚙️ **Auto Re-Embedding** - detects modified files and re-embeds when needed
* 💬 **Context-Aware Q&A** - LLM answers your questions using only local context
* 🌐 **FastAPI Web Interface** - browse and query files via a simple local web app
* ✅ **Tested & Typed** - full unit tests and type hints included

---

## Installation

You can install from PyPI:

``` bash
pip install localsearch
```

Or, if you’re developing locally:

``` bash
git clone https://github.com/yourusername/LocalSearch.git
cd LocalSearch
pip install -e .
```

---

## Quick Start

``` python
from LocalSearch.backend.engine import SearchEngine
from your_llm import MyLocalLLM  # implement BaseLLM

# Initialize with your local directory and models
engine = SearchEngine(
    directory_path="/path/to/your/files",
    llm=MyLocalLLM(),
    reembed_policy="modified_only",  # or 'force', 'never'
)

# Run a semantic query
answer = engine.search("What does this project do?")
print(answer)
```

To serve the web interface:

``` python
engine.web(host="127.0.0.1", port=8000)
```

Then open your browser at `http://127.0.0.1:8000`.

---

## How It Works

1. **Embedding Generation**

   * `_generate_embeddings` scans files, extracts text, chunks them, and encodes using your chosen embedder.
2. **Metadata & Vector Storage**

   * Uses `JsonMetadataStore` and `FaissVectorStore` by default (both replaceable).
3. **Querying**

   * Queries are embedded, compared against the local FAISS index, and context is fed into the LLM.
4. **Answering**

   * LLM answers using only retrieved context chunks.

---

## Configuration

| Parameter         | Description                                | Default                         |
| ----------------- | ------------------------------------------ | ------------------------------- |
| `directory_path`  | Path to your data folder                   | *required*                      |
| `embedding_model` | Any model implementing `BaseEmbedder`      | `SentenceTransformerEmbedder()` |
| `metadata_store`  | Metadata persistence                       | `JsonMetadataStore`             |
| `vector_store`    | Vector storage                             | `FaissVectorStore`              |
| `extractor`       | Text extraction logic                      | `DefaultTextExtractor`          |
| `reembed_policy`  | `'force'`, `'modified_only'`, or `'never'` | `'modified_only'`               |
| `recursive`       | Scan subfolders                            | `True`                          |
| `verbose`         | Print logs                                 | `True`                          |


---

## Architecture Overview

```
LocalSearch/
├── backend/
│   ├── engine.py                     # Main SearchEngine class
│   ├── _doc_loader/
│   │   ├── _embedding_processor.py   # Handles embedding and file updates
│   │   └── _scan.py                  # Directory scanning utilities
│   ├── embeddings/                   # BaseEmbedder + implementations
│   ├── llms/                         # BaseLLM and custom LLMs
│   ├── metadata_store/               # JsonMetadataStore + Base class
│   └── vector_store/                 # FaissVectorStore + Base class
└── frontend/                         # For web based interface
```

---

## Extending LocalSearch

You can plug in your own components simply by subclassing the base interfaces:

* **Custom Embedder** → subclass `BaseEmbedder`
* **Custom LLM** → subclass `BaseLLM`
* **Custom Vector Store** → subclass `BaseVectorStore`
* **Custom Metadata Store** → subclass `BaseMetadataStore`

Then pass them to the `SearchEngine` constructor.

---

## Documentation

Docs are hosted on **Read the Docs**:
👉 [https://localsearchpy.readthedocs.io](https://localsearchpy.readthedocs.io)

To build docs locally:

```bash
cd docs
pip install -r requirements.txt
make html
```

---

## Example Use Cases

* Personal knowledge base search
* Local document assistant for PDFs and notes
* Offline AI-powered research tool
* Privacy-friendly enterprise document retrieval

---

## License

MIT License © 2025 [Rick Sanchez]

---

## Contributing

Contributions are welcome!
Please open a pull request or file an issue if you’d like to add features, improve performance, or fix bugs.

---

## A Final Note

> “LocalSearch keeps your data *yours*.
> You can use the power of semantic search and LLMs - completely offline.”

