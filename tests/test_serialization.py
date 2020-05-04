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
"""Tests for serialization to python dicts Json-LD."""

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
    assert jsonld["@type"] == "http://schema.org/Book"


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
    assert jsonld["@type"] == "http://schema.org/Book"


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
    assert jsonld["@type"] == "http://schema.org/Person"

    assert "@reverse" in jsonld
    reverse = jsonld["@reverse"]
    assert "http://schema.org/author" in reverse
    book = reverse["http://schema.org/author"][0]

    assert "http://schema.org/name" in book
    assert book["http://schema.org/name"] == b.name
    assert "@id" in book
    assert book["@id"] == b._id
    assert "@type" in book
    assert book["@type"] == "http://schema.org/Book"
