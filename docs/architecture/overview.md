# Architecture Overview

Reveal is designed around a simple principle:

> Separate where data comes from, how it is accessed, and how its content is interpreted.

This allows the library to support new storage systems and new file formats without changing the core data model or processing pipeline.

## The three plugin layers

A file is processed through three independent steps:

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

Each layer has a single responsibility.

---

## 1. SourceProvider

A `SourceProvider` discovers a source and produces a `Source` object.

The source may represent:

* one file
* a directory
* a nested directory tree
* a remote object hierarchy

The provider is storage-specific.

For example:

```text
LocalFileSystemSourceProvider
S3SourceProvider
AzureSourceProvider
```

The interface is:

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

The provider does not read or parse the file content.

### SourceLocation

A `SourceLocation` describes where a source is located.

```python
class SourceLocation(CoreModel):
    scheme: str
    path: str
    options: dict[str, Any] = Field(
        default_factory=dict
    )
```

For example:

```python
Location.from_path(
    "data/recipes.json"
)
```

produces approximately:

```python
SourceLocation(
    scheme="file",
    path="/absolute/path/data/recipes.json",
)
```

A future S3 location could be represented as:

```python
Location.from_s3(
    "my-bucket/recipes/recipes.json",
    region="eu-west-1",
)
```

The important point is that `SourceLocation` itself does not contain filesystem or S3 logic.

The `Location` factory provides convenient constructors while keeping the domain model generic.

### Source

`Source` represents the discovered source.

It contains information such as:

* source type
* name
* location
* size
* MIME type
* extension
* timestamps
* checksum
* children

A directory therefore becomes a tree of `Source` objects.

For example:

```text
recipes/
├── recipes.json
├── ingredients.csv
└── archived/
    └── old-recipes.json
```

can be represented as:

```text
Source(recipes/)
├── Source(recipes.json)
├── Source(ingredients.csv)
└── Source(archived/)
    └── Source(old-recipes.json)
```

This makes the concept of a source independent from the physical storage technology.

---

## 2. ContentProvider

Once a source has been discovered, a `ContentProvider` provides access to the content of an individual file.

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

For a local file:

```python
with content_provider.open(source) as content:
    ...
```

The result is a `BinaryIO`.

The content provider does not know anything about JSON, CSV, Excel, or XML.

For example:

```text
LocalFileContentProvider
        │
        └── local filesystem → BinaryIO

S3ContentProvider
        │
        └── S3 object        → BinaryIO
```

This means the same JSON reader can process both local and S3 JSON files.

---

## 3. FileReader

The `FileReader` interprets the content.

It is format-specific:

```text
JsonFileReader
CsvFileReader
ExcelFileReader
XmlFileReader
```

The interface is:

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

The reader receives a binary stream rather than a path.

Therefore the JSON reader does not care where the file came from.

For example:

```python
with content_provider.open(source) as content:
    result = json_reader.read(
        content,
        source,
    )
```

The exact same code works with a local filesystem or S3 content provider.

---

## ReadResult

A reader returns a `ReadResult`.

```python
class ReadResult(CoreModel):

    node: DocumentNode
    warnings: list[str] = Field(
        default_factory=list
    )
    errors: list[str] = Field(
        default_factory=list
    )
```

This separates parsing diagnostics from the parsed content.

A valid JSON file might produce:

```text
ReadResult
├── node
├── warnings = []
└── errors = []
```

A file with recoverable problems could produce:

```text
ReadResult
├── node
├── warnings
│   └── ...
└── errors
    └── ...
```

---

## DocumentNode

`DocumentNode` is the generic intermediate representation used by Reveal.

It deliberately does not represent JSON specifically.

```python
class NodeKind(str, Enum):

    OBJECT = "object"
    ARRAY = "array"
    VALUE = "value"
```

The node model is:

```python
class DocumentNode(CoreModel):

    kind: NodeKind
    name: str | None = None
    value: Any | None = None
    children: list["DocumentNode"] = Field(
        default_factory=list
    )
```

This creates a generic tree.

For this JSON:

```json
{
  "title": "Chocolate Cake",
  "rating": 4.5,
  "ingredients": [
    "flour",
    "eggs"
  ]
}
```

the resulting tree is:

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

This representation is deliberately independent from JSON.

A CSV reader can produce the same generic representation, as can future Excel or XML readers.

---

## Why use an intermediate representation?

The intermediate `DocumentNode` tree allows the analysis algorithms to be completely independent of the input format.

For example:

```text
JSON ────────┐
CSV ─────────┤
Excel ───────┼──→ DocumentNode ──→ Structure Discovery
XML ─────────┤                         │
API ─────────┘                         ▼
                                      Semantic Discovery
                                          │
                                          ▼
                                      Data Quality
                                          │
                                          ▼
                                      SQL / Excel / ...
```

This is one of the most important architectural boundaries in Reveal.

The analysis algorithms should not contain code such as:

```python
if json:
    ...
elif csv:
    ...
```

They operate only on the generic document model.

---

## Complete example

A local JSON file can therefore be processed as follows:

```python
location = Location.from_path(
    "data/recipes.json"
)

source = source_provider.create_source(
    location
)

with content_provider.open(source) as content:
    result = json_reader.read(
        content,
        source
    )

document_node = result.node
```

Each component has a single responsibility:

| Component         | Responsibility                         |
| ----------------- | -------------------------------------- |
| `Location`        | Conveniently construct locations       |
| `SourceLocation`  | Generic location description           |
| `SourceProvider`  | Discover source structure and metadata |
| `Source`          | Represent discovered sources           |
| `ContentProvider` | Provide file content                   |
| `FileReader`      | Parse a file format                    |
| `ReadResult`      | Return parsed content and diagnostics  |
| `DocumentNode`    | Generic document representation        |

---

## Plugin independence

The architecture allows plugins to be developed independently.

For example, adding S3 support does not require modifying the JSON reader:

```text
LocalFileSystemSourceProvider ──┐
LocalFileContentProvider ───────┼──→ JsonFileReader
                                │
S3SourceProvider ───────────────┤
S3ContentProvider ──────────────┘
```

Likewise, adding Excel support does not require changing the filesystem provider:

```text
LocalFileSystemSourceProvider
          │
          ▼
LocalFileContentProvider
          │
          ├── JsonFileReader
          ├── CsvFileReader
          └── ExcelFileReader
```

The future `DocumentLoader` will orchestrate these components and select the appropriate plugins.

---

## Future processing pipeline

The current architecture establishes the foundation for the higher-level pipeline:

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

The important architectural principle is that each stage communicates through a generic model rather than depending on the implementation of the previous stage.
