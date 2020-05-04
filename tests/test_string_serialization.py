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
"""Tests for (de-)serialization from/to Json-LD."""

import calamus.fields as fields
from calamus.schema import JsonLDSchema


def test_simple_string_serialization():
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

    jsonld = BookSchema().dumps(b)

    assert '"@id": "http://example.com/books/1"' in jsonld
    assert '"http://schema.org/name": "Hitchhikers Guide to the Galaxy"' in jsonld
    assert '"@type": "http://schema.org/Book"' in jsonld


def test_simple_string_deserialization():
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

    data = '{"@id": "http://example.com/books/1", "http://schema.org/name": "Hitchhikers Guide to the Galaxy", "@type": "http://schema.org/Book"}'

    book = BookSchema().loads(data)

    assert book._id == "http://example.com/books/1"
    assert book.name == "Hitchhikers Guide to the Galaxy"
