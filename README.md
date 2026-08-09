# Reveal

**Reveal** is a modular data inspection library designed to help users understand heterogeneous data sources before importing, transforming, or analyzing them.

The goal is simple:

> Give Reveal a file or directory and let it discover, inspect, validate, and eventually transform the data into useful structures such as SQLite databases or Excel files.

The project is currently developed as a side project and is being designed as an open, extensible library first, with a user-facing application planned later.

---

## Current MVP

The current implementation focuses on the foundation for a generic data inspection pipeline.

Reveal separates data processing into three independent plugin layers:

```text
Location
    │
    ▼
SourceProvider
    │
    ▼
Source
    │
    ▼
ContentProvider
    │
    ▼
BinaryIO
    │
    ▼
FileReader
    │
    ▼
DocumentNode
```

This allows storage and file formats to evolve independently.

For example:

```text
Local filesystem ──┐
S3 ────────────────┼──→ ContentProvider ──→ JSON reader
Azure ─────────────┘                         CSV reader
                                             Excel reader
```

### Current capabilities

* Generic `SourceLocation`
* Local filesystem source discovery
* Recursive source trees
* Source metadata
* Pluggable content providers
* Local filesystem content provider
* Generic `DocumentNode` representation
* JSON file reader
* JSON parsing warnings and errors
* Pydantic domain models
* Pytest plugin tests
* Sphinx documentation

### Planned capabilities

* Generic `DocumentLoader`
* CSV reader
* Excel reader
* XML reader
* S3 and other remote storage providers
* Structure discovery
* Semantic discovery
* Data sanity checks
* Data quality scoring
* Relational model discovery
* SQLite export
* Excel export
* CLI
* HTTP API
* Web frontend
* Large dataset processing
* Optional AI-assisted analysis

---

## Architecture

The project is organized around a small core and independent plugins.

```text
src/reveal/
├── core/
│   ├── interfaces/
│   └── models/
│
├── plugins/
│   ├── filesystem/
│   └── json/
│
├── pipeline/
├── cli/
└── api/
```

### Core

The `core` package contains the stable domain models and interfaces.

It should not contain storage- or format-specific implementation details.

Examples include:

* `Source`
* `SourceLocation`
* `Document`
* `DocumentNode`
* `ReadResult`
* `NodeKind`
* `SourceProvider`
* `ContentProvider`
* `FileReader`

The core defines **what the system does**, not how a particular storage system or file format implements it.

### Plugins

Plugins contain concrete implementations of the core interfaces.

For example:

```text
plugins/
├── filesystem/
│   ├── source_provider.py
│   ├── content_provider.py
│   └── tests/
│
└── json/
    ├── file_reader.py
    ├── tests/
    │   └── data/
    └── ...
```

A plugin is intended to be as self-contained as possible.

This makes it possible to eventually move plugins into separate packages or repositories without changing the core architecture.

---

## Source discovery

A source is not necessarily a single file.

Reveal treats a source as a generic structure that can represent:

* a file
* a directory
* nested directories
* collections of files
* remote storage hierarchies

A `SourceProvider` discovers this structure.

```python
class SourceProvider(Protocol):

    def supports(
        self,
        location: SourceLocation,
    ) -> bool:
        ...

    def create_source(
        self,
        location: SourceLocation,
    ) -> Source:
        ...
```

The first implementation is the local filesystem provider.

---

## Content access

Source discovery and content access are deliberately separated.

A `ContentProvider` opens the content of an individual file and returns a binary stream.

```python
class ContentProvider(Protocol):

    def supports(
        self,
        source: Source,
    ) -> bool:
        ...

    def open(
        self,
        source: Source,
    ) -> BinaryIO:
        ...
```

For example:

```python
with content_provider.open(source) as content:
    ...
```

This means that file parsers never need to know whether the data came from a local filesystem, S3, or another storage system.

---

## File parsing

`FileReader` implementations convert file content into Reveal's generic document representation.

```python
class FileReader(Protocol):

    def supports(
        self,
        source: Source,
    ) -> bool:
        ...

    def read(
        self,
        content: BinaryIO,
        source: Source,
    ) -> ReadResult:
        ...
```

The current implementation is:

```text
JsonFileReader
```

Future readers will include:

```text
CsvFileReader
ExcelFileReader
XmlFileReader
...
```

---

## DocumentNode

Reveal uses `DocumentNode` as an intermediate representation between file parsing and data analysis.

```python
class NodeKind(str, Enum):

    OBJECT = "object"
    ARRAY = "array"
    VALUE = "value"
```

A document is represented as a tree:

```text
OBJECT
├── title
│   └── VALUE("Chocolate Cake")
│
├── rating
│   └── VALUE(4.5)
│
└── ingredients
    └── ARRAY
        ├── 0
        │   └── VALUE("flour")
        └── 1
            └── VALUE("eggs")
```

The important property is that this representation is **not JSON-specific**.

The same structure can be produced by future CSV, Excel, XML, or other readers.

This allows the analysis algorithms to work on a single generic representation.

---

## Development

### Requirements

* Python 3.13+
* [uv](https://docs.astral.sh/uv/)
* Node.js and npm for the future frontend

---

## Install

Clone the repository and install the Python dependencies with `uv`:

```bash
uv sync
```

This creates/updates the project's virtual environment and installs the dependencies defined in `pyproject.toml`.

For development dependencies:

```bash
uv sync --dev
```

---

## Tests

The project uses Pytest.

Run the complete test suite:

```bash
uv run pytest
```

Run tests with more detailed output:

```bash
uv run pytest -v
```

Run only the JSON plugin tests:

```bash
uv run pytest src/reveal/plugins/json/tests
```

Plugin tests are kept close to their implementation so that each plugin remains self-contained.

For example:

```text
src/reveal/plugins/json/
├── file_reader.py
└── tests/
    ├── data/
    │   ├── simple.json
    │   ├── nested.json
    │   ├── arrays.json
    │   ├── recipe.json
    │   └── invalid.json
    │
    └── test_reader.py
```

---

## Documentation

Reveal uses **Sphinx** with MyST Markdown and the Furo theme.

Install the documentation dependencies:

```bash
uv sync --dev
```

Build the HTML documentation:

```bash
uv run sphinx-build -b html docs docs/_build/html
```

The generated documentation is available at:

```text
docs/_build/html/index.html
```

### Live documentation

For development, `sphinx-autobuild` can be used:

```bash
uv run sphinx-autobuild docs docs/_build/html
```

The documentation will automatically rebuild when files change.

---

## Frontend

The frontend is planned but is not currently part of the MVP implementation.

The intended technology is:

* React
* Vite

When the frontend is introduced:

```bash
cd app
npm install
npm run dev
```

---

## Future pipeline

The long-term processing pipeline is planned as:

```text
Location
    ↓
SourceProvider
    ↓
Source
    ↓
ContentProvider
    ↓
BinaryIO
    ↓
FileReader
    ↓
DocumentNode
    ↓
Document
    ↓
Structure Discovery
    ↓
Semantic Discovery
    ↓
Data Quality / Sanity Checks
    ↓
Relational Model
    ↓
SQLite / Excel / ...
```

The objective is to make each stage independently extensible.

In particular, storage providers and file readers should never need to know about the higher-level analysis algorithms.

---

## Code Style

The project uses:

* Python 3.13+
* Pydantic v2
* Pytest
* Ruff
* Type hints
* Google-style docstrings
* Sphinx / MyST for documentation
* `uv` for Python dependency and environment management

---

## Design Principles

### Separation of concerns

Storage, content access, parsing, and analysis are independent concerns.

### Plugin-first architecture

New storage systems and file formats should be implementable as independent plugins.

### Generic intermediate representation

Analysis algorithms operate on `DocumentNode`, not directly on JSON, CSV, Excel, etc.

### Explicit interfaces

The core defines stable interfaces that plugins implement.

### Extensibility

The architecture is intentionally designed so that future implementations can support:

* remote storage
* large datasets
* database sources
* additional file formats
* AI-assisted semantic discovery
* alternative export formats

### Keep the MVP small

The initial objective is not to build a complete ETL platform.

The first useful product is a **data inspection tool**:

> Give Reveal a source, and Reveal tells you what is inside it, what the structure looks like, and where the data appears problematic.

---

## License

TBD
