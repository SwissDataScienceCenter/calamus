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
"""Tests for serialization to python dicts JSON-LD."""

import calamus.fields as fields
from calamus.schema import JsonLDSchema


def test_simple_serialization():
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

    b = Book("http://example.com/books/1", "Hitchhikers Guide to the Galaxy")

    jsonld = BookSchema().dump(b)

    assert "http://schema.org/name" in jsonld
    assert jsonld["http://schema.org/name"] == b.name
    assert "@id" in jsonld
    assert jsonld["@id"] == b._id
    assert "@type" in jsonld
    assert jsonld["@type"] == ["http://schema.org/Book"]


def test_simple_serialization_with_value_type():
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

    b = Book("http://example.com/books/1", "Hitchhikers Guide to the Galaxy")

    jsonld = BookSchema().dump(b)

    assert "http://schema.org/name" in jsonld
    assert "@type" in jsonld["http://schema.org/name"]
    assert jsonld["http://schema.org/name"]["@value"] == b.name
    assert "@id" in jsonld
    assert jsonld["@id"] == b._id
    assert "@type" in jsonld
    assert jsonld["@type"] == ["http://schema.org/Book"]


def test_nested_reverse_serialization():
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

    b = Book("http://example.com/books/1", "Hitchhikers Guide to the Galaxy")
    a = Author("http://example.com/authors/2", "Douglas Adams")
    a.books.append(b)

    jsonld = AuthorSchema().dump(a)

    assert "http://schema.org/name" in jsonld
    assert jsonld["http://schema.org/name"] == a.name
    assert "@id" in jsonld
    assert jsonld["@id"] == a._id
    assert "@type" in jsonld
    assert jsonld["@type"] == ["http://schema.org/Person"]

    assert "@reverse" in jsonld
    reverse = jsonld["@reverse"]
    assert "http://schema.org/author" in reverse
    book = reverse["http://schema.org/author"][0]

    assert "http://schema.org/name" in book
    assert book["http://schema.org/name"] == b.name
    assert "@id" in book
    assert book["@id"] == b._id
    assert "@type" in book
    assert book["@type"] == ["http://schema.org/Book"]


def test_flattened_serialization():
    """Test that we can output flattened jsonld."""

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

    a = Author("http://example.com/authors/2", "Douglas Adams")
    b = Book("http://example.com/books/1", "Hitchhikers Guide to the Galaxy", a)

    jsonld = BookSchema(flattened=True).dump(b)

    assert len(jsonld) == 2

    book = next(e for e in jsonld if e["@id"] == "http://example.com/books/1")
    author = next(e for e in jsonld if e["@id"] == "http://example.com/authors/2")

    assert "http://schema.org/name" in author
    assert author["http://schema.org/name"][0]["@value"] == a.name
    assert "@id" in author
    assert author["@id"] == a._id
    assert "@type" in author
    assert author["@type"] == ["http://schema.org/Person"]

    assert "http://schema.org/name" in book
    assert book["http://schema.org/name"][0]["@value"] == b.name
    assert "@id" in book
    assert book["@id"] == b._id
    assert "@type" in book
    assert book["@type"] == ["http://schema.org/Book"]
    assert "http://schema.org/author" in book
    assert book["http://schema.org/author"][0]["@id"] == a._id


def test_multiple_nested_flattened_serialization():
    """Test that we can output flattened jsonld for multiple nested objects."""

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

    b1 = Book("http://example.com/books/1", "Hitchhikers Guide to the Galaxy")
    b2 = Book("http://example.com/books/2", "We Are Legion (We Are Bob)")
    a = Author("http://example.com/authors/2", "Douglas Adams", [b1, b2])

    jsonld = AuthorSchema(flattened=True).dump(a)

    assert len(jsonld) == 3

    book1 = next(e for e in jsonld if e["@id"] == "http://example.com/books/1")
    book2 = next(e for e in jsonld if e["@id"] == "http://example.com/books/2")
    author = next(e for e in jsonld if e["@id"] == "http://example.com/authors/2")

    assert "http://schema.org/name" in author
    assert author["http://schema.org/name"][0]["@value"] == a.name
    assert "@id" in author
    assert author["@id"] == a._id
    assert "@type" in author
    assert author["@type"] == ["http://schema.org/Person"]

    assert "http://schema.org/name" in book1
    assert book1["http://schema.org/name"][0]["@value"] == b1.name
    assert "@id" in book1
    assert book1["@id"] == b1._id
    assert "@type" in book1
    assert book1["@type"] == ["http://schema.org/Book"]
    assert "http://schema.org/author" in book1
    assert book1["http://schema.org/author"][0]["@id"] == a._id

    assert "http://schema.org/name" in book2
    assert book2["http://schema.org/name"][0]["@value"] == b2.name
    assert "@id" in book2
    assert book2["@id"] == b2._id
    assert "@type" in book2
    assert book2["@type"] == ["http://schema.org/Book"]
    assert "http://schema.org/author" in book2
    assert book2["http://schema.org/author"][0]["@id"] == a._id
