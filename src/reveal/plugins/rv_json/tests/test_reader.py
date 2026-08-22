from pathlib import Path

import pytest

from reveal.core.models.enums import NodeKind
from reveal.core.models.source import Source
from reveal.plugins.rv_filesystem import (
    LocalFileSystemContentProvider,
    LocalFileSystemSourceProvider,
)
from reveal.plugins.rv_filesystem.location import Location
from reveal.plugins.rv_json import JsonFileReader


DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def reader() -> JsonFileReader:
    return JsonFileReader()


@pytest.fixture
def source_factory():
    provider = LocalFileSystemSourceProvider()

    def create(filename: str) -> Source:
        return provider.create_source(
            Location.from_path(DATA_DIR / filename)
        )

    return create


@pytest.fixture
def content_provider() -> LocalFileSystemContentProvider:
    return LocalFileSystemContentProvider()


def read_file(reader, content_provider, source):
    with content_provider.open(source) as content:
        return reader.read(content, source)


def test_supports_json_file(
    reader: JsonFileReader,
    source_factory,
):
    source = source_factory("simple.json")

    assert reader.supports(source) is True


def test_reads_simple_values(
    reader: JsonFileReader,
    content_provider: LocalFileSystemContentProvider,
    source_factory,
):
    source = source_factory("simple.json")

    result = read_file(reader, content_provider, source)

    assert result.errors == []
    assert result.warnings == []

    root = result.node

    assert root.kind == NodeKind.OBJECT

    values = {
        node.name: node.value
        for node in root.children
    }

    assert values["name"] == "Alice"
    assert values["age"] == 42
    assert values["active"] is True
    assert values["score"] == 12.5
    assert values["nothing"] is None


def test_reads_nested_objects(
    reader: JsonFileReader,
    content_provider: LocalFileSystemContentProvider,
    source_factory,
):
    source = source_factory("nested.json")

    result = read_file(reader, content_provider, source)

    assert result.errors == []

    root = result.node

    recipe = root.children[0]

    assert recipe.name == "recipe"
    assert recipe.kind == NodeKind.OBJECT

    title = next(
        node
        for node in recipe.children
        if node.name == "title"
    )

    assert title.kind == NodeKind.VALUE
    assert title.value == "Chocolate Cake"

    author = next(
        node
        for node in recipe.children
        if node.name == "author"
    )

    assert author.kind == NodeKind.OBJECT

    author_name = next(
        node
        for node in author.children
        if node.name == "name"
    )

    assert author_name.value == "Alice"


def test_reads_arrays(
    reader: JsonFileReader,
    content_provider: LocalFileSystemContentProvider,
    source_factory,
):
    source = source_factory("arrays.json")

    result = read_file(reader, content_provider, source)

    assert result.errors == []

    root = result.node

    ingredients = next(
        node
        for node in root.children
        if node.name == "ingredients"
    )

    assert ingredients.kind == NodeKind.ARRAY
    assert len(ingredients.children) == 3

    assert ingredients.children[0].value == "flour"
    assert ingredients.children[1].value == "eggs"
    assert ingredients.children[2].value == "milk"

    nested = next(
        node
        for node in root.children
        if node.name == "nested"
    )

    assert nested.kind == NodeKind.ARRAY
    assert nested.children[0].kind == NodeKind.OBJECT
    assert nested.children[1].kind == NodeKind.OBJECT


def test_reads_recipe_structure(
    reader: JsonFileReader,
    content_provider: LocalFileSystemContentProvider,
    source_factory,
):
    source = source_factory("recipe.json")

    result = read_file(reader, content_provider, source)

    assert result.errors == []

    root = result.node

    recipe = root.children[0]

    assert recipe.name == "0"
    assert recipe.kind == NodeKind.OBJECT

    ingredients = next(
        node
        for node in recipe.children
        if node.name == "ingredients"
    )

    assert ingredients.kind == NodeKind.ARRAY
    assert len(ingredients.children) == 2

    first_ingredient = ingredients.children[0]

    assert first_ingredient.kind == NodeKind.OBJECT

    ingredient_values = {
        node.name: node.value
        for node in first_ingredient.children
    }

    assert ingredient_values["name"] == "ground beef"
    assert ingredient_values["quantity"] == "1"
    assert ingredient_values["unit"] == "lb"

    nutrients = next(
        node
        for node in recipe.children
        if node.name == "nutrients"
    )

    assert nutrients.kind == NodeKind.OBJECT

    calories = next(
        node
        for node in nutrients.children
        if node.name == "calories"
    )

    assert calories.value == "350 kcal"


def test_invalid_json_returns_error(
    reader: JsonFileReader,
    content_provider: LocalFileSystemContentProvider,
    source_factory,
):
    source = source_factory("invalid.json")

    result = read_file(reader, content_provider, source)

    assert len(result.errors) == 1
    assert "Invalid JSON" in result.errors[0]
