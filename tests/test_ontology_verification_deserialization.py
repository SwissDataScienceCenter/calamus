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
"""Tests for Ontology Verification during deserialization from python dicts."""
import pytest

from calamus import fields
from calamus.schema import JsonLDSchema


def test_simple_verification_deserialization():
    """ Shouldn't raise any error while deserializing """

    class Book:
        def __init__(self, _id, name, author):
            self._id = _id
            self.name = name
            self.author = author

    schema = fields.Namespace("http://schema.org/")

    class BookSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)
        author = fields.String(schema.author)

        class Meta:
            rdf_type = schema.Book
            model = Book

    data = {
        "@id": "http://example.com/books/4",
        "@type": "http://schema.org/Book",
        "http://schema.org/name": "Harry Potter & The Chamber of Secrets",
        "http://schema.org/author": "J. K. Rowling",
        "http://schema.org/publishedYear": 1998,
    }

    verified_data = BookSchema().validate_properties(data, "tests/fixtures/book_ontology.owl", return_valid_data=True)

    assert BookSchema().load(verified_data)
