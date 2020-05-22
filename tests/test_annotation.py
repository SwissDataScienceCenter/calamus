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

import calamus.fields as fields
from calamus.schema import JsonLDAnnotation


def test_annotation():
    """Test annotation support."""
    schema = fields.Namespace("http://schema.org/")

    class Book(metaclass=JsonLDAnnotation):
        _id = fields.Id()
        name = fields.String(schema.name)

        def __init__(self, _id, name):
            self._id = _id
            self.name = name

        class Meta:
            rdf_type = schema.Book

    data = {
        "@id": "http://example.com/books/1",
        "@type": ["http://schema.org/Book"],
        "http://schema.org/name": "Hitchhikers Guide to the Galaxy",
    }

    book = Book.schema().load(data)

    assert book._id == "http://example.com/books/1"
    assert book.name == "Hitchhikers Guide to the Galaxy"

    dumped = Book.schema().dump(book)
    assert data == dumped

    dumped = book.dump()
    assert data == dumped


def test_annotation_with_default():
    """Test annotation with default values."""
    schema = fields.Namespace("http://schema.org/")

    def default_surname():
        return "Doe"

    class Book(metaclass=JsonLDAnnotation):
        _id = fields.Id(default="http://example.com/book/1")
        name = fields.String(schema.name, default=lambda: "Bill")
        surname = fields.String(schema.surname, default=default_surname)

        class Meta:
            rdf_type = schema.Book

    b = Book()

    assert b._id == "http://example.com/book/1"
    assert b.name == "Bill"
    assert b.surname == "Doe"

    book_dict = b.dump()

    assert "@id" in book_dict
    assert book_dict["@id"] == b._id
    assert "http://schema.org/name" in book_dict
    assert b.name == book_dict["http://schema.org/name"]
    assert b.surname == book_dict["http://schema.org/surname"]


def test_nested_annotation():
    """Test that nesting works for annotated classes."""

    schema = fields.Namespace("http://schema.org/")

    class Book(metaclass=JsonLDAnnotation):
        _id = fields.Id()
        name = fields.String(schema.name)

        def __init__(self, _id, name):
            self._id = _id
            self.name = name

        class Meta:
            rdf_type = schema.Book

    class Author(metaclass=JsonLDAnnotation):
        _id = fields.Id()
        name = fields.String(schema.name)
        books = fields.Nested(schema.author, Book, reverse=True, many=True)

        def __init__(self, _id, name, books):
            self._id = _id
            self.name = name
            self.books = books

        class Meta:
            rdf_type = schema.Person

    b = Book("http://example.com/book/1", "Le Petit Prince")
    a = Author("http://example.com/authors/1", "Antoine de Saint-Exupéry", [b])

    author_dict = a.dump()

    assert "@reverse" in author_dict
    assert "http://schema.org/author" in author_dict["@reverse"]
    books = author_dict["@reverse"]["http://schema.org/author"]
    assert len(books) == 1
    assert books[0]["http://schema.org/name"] == b.name
