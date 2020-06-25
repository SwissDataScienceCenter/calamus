# -*- coding: utf-8 -*-
#
# Copyright 2017-2020- Swiss Data Science Center (SDSC)
# A partnership between École Polytechnique Fédérale de Lausanne (EPFL) and
# Eidgenössische Technische Hochschule Zürich (ETHZ).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for deserialization from python dicts."""

import pytest

import calamus.fields as fields
from calamus.schema import JsonLDSchema


def test_simple_deserialization():
    class Book:
        def __init__(self, _id, name, *args, test="Bla", **kwargs):
            self._id = _id
            self.name = name

    schema = fields.Namespace("http://schema.org/")

    class BookSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)

        class Meta:
            rdf_type = schema.Book
            model = Book

    data = {
        "@id": "http://example.com/books/1",
        "@type": "http://schema.org/Book",
        "http://schema.org/name": "Hitchhikers Guide to the Galaxy",
    }

    book = BookSchema().load(data)

    assert book._id == "http://example.com/books/1"
    assert book.name == "Hitchhikers Guide to the Galaxy"


def test_simple_deserialization_with_value_type():
    class Book:
        def __init__(self, _id, name):
            self._id = _id
            self.name = name

    schema = fields.Namespace("http://schema.org/")

    class BookSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)

        class Meta:
            rdf_type = schema.Book
            model = Book
            add_value_types = True

    data = {
        "@id": "http://example.com/books/1",
        "@type": "http://schema.org/Book",
        "http://schema.org/name": {
            "@type": "http://www.w3.org/2001/XMLSchema#string",
            "@value": "Hitchhikers Guide to the Galaxy",
        },
    }
    book = BookSchema().load(data)

    assert book._id == "http://example.com/books/1"
    assert book.name == "Hitchhikers Guide to the Galaxy"


@pytest.mark.parametrize(
    "data",
    [
        {
            "@id": "http://example.com/authors/2",
            "@reverse": {
                "http://schema.org/author": [
                    {
                        "@id": "http://example.com/books/1",
                        "@type": "http://schema.org/Book",
                        "http://schema.org/name": "Hitchhikers " "Guide " "to the " "Galaxy",
                    }
                ]
            },
            "@type": "http://schema.org/Person",
            "http://schema.org/name": "Douglas Adams",
        },
        {
            "@id": "http://example.com/authors/2",
            "@reverse": {
                "http://schema.org/author": {
                    "@id": "http://example.com/books/1",
                    "@type": "http://schema.org/Book",
                    "http://schema.org/name": "Hitchhikers " "Guide " "to the " "Galaxy",
                }
            },
            "@type": "http://schema.org/Person",
            "http://schema.org/name": "Douglas Adams",
        },
    ],
)
def test_nested_reverse_deserialization(data):
    class Book:
        def __init__(self, _id, name):
            self._id = _id
            self.name = name

    class Author:
        def __init__(self, _id, name):
            self._id = _id
            self.name = name
            self.books = []

    schema = fields.Namespace("http://schema.org/")

    class BookSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)

        class Meta:
            rdf_type = schema.Book
            model = Book

    class AuthorSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)
        books = fields.Nested(schema.author, BookSchema, reverse=True, many=True)

        class Meta:
            rdf_type = schema.Person
            model = Author

    author = AuthorSchema().load(data)

    assert author.name == "Douglas Adams"
    assert author._id == "http://example.com/authors/2"
    assert len(author.books) == 1
    assert author.books[0]._id == "http://example.com/books/1"
    assert author.books[0].name == "Hitchhikers Guide to the Galaxy"


def test_nested_flattened_deserialization():
    """Test deserialisation of flattened jsonld."""

    class Book:
        def __init__(self, _id, name, author):
            self._id = _id
            self.name = name
            self.author = author

    class Author:
        def __init__(self, _id, name):
            self._id = _id
            self.name = name

    schema = fields.Namespace("http://schema.org/")

    class AuthorSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)

        class Meta:
            rdf_type = schema.Person
            model = Author

    class BookSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)
        author = fields.Nested(schema.author, AuthorSchema)

        class Meta:
            rdf_type = schema.Book
            model = Book

    data = [
        {
            "@id": "http://example.com/authors/2",
            "@type": ["http://schema.org/Person"],
            "http://schema.org/name": [{"@value": "Douglas Adams"}],
        },
        {
            "@id": "http://example.com/books/1",
            "@type": ["http://schema.org/Book"],
            "http://schema.org/author": [{"@id": "http://example.com/authors/2"}],
            "http://schema.org/name": [{"@value": "Hitchhikers Guide to the Galaxy"}],
        },
    ]

    book = BookSchema(flattened=True).load(data)

    assert book._id == "http://example.com/books/1"
    assert book.name == "Hitchhikers Guide to the Galaxy"

    author = book.author

    assert author.name == "Douglas Adams"
    assert author._id == "http://example.com/authors/2"


def test_multiple_nested_reverse_flattened_deserialization():
    """Test deserialisation of flattened jsonld."""

    class Book:
        def __init__(self, _id, name):
            self._id = _id
            self.name = name

    class Author:
        def __init__(self, _id, name, books):
            self._id = _id
            self.name = name
            self.books = books

    schema = fields.Namespace("http://schema.org/")

    class BookSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)

        class Meta:
            rdf_type = schema.Book
            model = Book

    class AuthorSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)
        books = fields.Nested(schema.author, BookSchema, reverse=True, many=True)

        class Meta:
            rdf_type = schema.Person
            model = Author

    data = [
        {
            "@id": "http://example.com/authors/2",
            "@type": ["http://schema.org/Person"],
            "http://schema.org/name": [{"@value": "Douglas Adams"}],
        },
        {
            "@id": "http://example.com/books/1",
            "@type": ["http://schema.org/Book"],
            "http://schema.org/author": [{"@id": "http://example.com/authors/2"}],
            "http://schema.org/name": [{"@value": "Hitchhikers Guide to the Galaxy"}],
        },
        {
            "@id": "http://example.com/books/2",
            "@type": ["http://schema.org/Book"],
            "http://schema.org/author": [{"@id": "http://example.com/authors/2"}],
            "http://schema.org/name": [{"@value": "We Are Legion (We Are Bob)"}],
        },
    ]

    author = AuthorSchema(flattened=True).load(data)

    assert author.name == "Douglas Adams"
    assert author._id == "http://example.com/authors/2"

    assert len(author.books) == 2

    book1 = next(b for b in author.books if b._id == "http://example.com/books/1")
    book2 = next(b for b in author.books if b._id == "http://example.com/books/2")

    assert book1._id == "http://example.com/books/1"
    assert book1.name == "Hitchhikers Guide to the Galaxy"

    assert book2._id == "http://example.com/books/2"
    assert book2.name == "We Are Legion (We Are Bob)"


def test_lazy_deserialization():
    """Tests that lazy deserialization works."""
    import lazy_object_proxy

    class Genre:
        def __init__(self, name):
            self.name = name

        def test(self):
            return self.name

        def __call__(self):
            return self.name

    class Book:
        def __init__(self, name, genre):
            self.name = name
            self.genre = genre

    class Author:
        def __init__(self, name, books):
            self.name = name
            self.books = books

    schema = fields.Namespace("https://schema.org/")

    class GenreSchema(JsonLDSchema):
        _id = fields.BlankNodeId()
        name = fields.String(schema.name)

        class Meta:
            rdf_type = schema.Genre
            model = Genre

    class BookSchema(JsonLDSchema):
        _id = fields.BlankNodeId()
        name = fields.String(schema.name)
        genre = fields.Nested(schema.genre, GenreSchema)

        class Meta:
            rdf_type = schema.Book
            model = Book

    class AuthorSchema(JsonLDSchema):
        _id = fields.BlankNodeId()
        name = fields.String(schema.name)
        books = fields.Nested(schema.books, BookSchema, many=True)

        class Meta:
            rdf_type = schema.Author
            model = Author

    data = {
        "@type": ["https://schema.org/Author"],
        "https://schema.org/books": [
            {
                "@type": ["https://schema.org/Book"],
                "https://schema.org/genre": {"@type": ["https://schema.org/Genre"], "https://schema.org/name": "Novel"},
                "https://schema.org/name": "Don Quixote",
            }
        ],
        "https://schema.org/name": "Miguel de Cervantes",
    }

    a = AuthorSchema(lazy=True).load(data)

    assert a.name == "Miguel de Cervantes"
    book = a.books[0]

    assert isinstance(book, lazy_object_proxy.Proxy)
    assert " wrapping " not in repr(book)  # make sure proxy is not evaluated yet

    assert book.name == "Don Quixote"
    assert " wrapping " in repr(book)  # make sure proxy is evaluated
    assert book.genre.name == "Novel"
