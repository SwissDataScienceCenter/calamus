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


def test_nested_reverse_deserialization():
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

    data = {
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
    }

    author = AuthorSchema().load(data)

    assert author.name == "Douglas Adams"
    assert author._id == "http://example.com/authors/2"
    assert len(author.books) == 1
    assert author.books[0]._id == "http://example.com/books/1"
    assert author.books[0].name == "Hitchhikers Guide to the Galaxy"
