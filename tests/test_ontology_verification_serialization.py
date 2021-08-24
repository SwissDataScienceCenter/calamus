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
"""Tests for Ontology Verification during serialization to python dicts Json-LD."""
import pytest

from calamus import fields
from calamus.schema import JsonLDSchema


def test_simple_verification_serialization():
    """The ontology doesn't contain the property of publishedYear so it shoudn't be included in the jsonld returned"""

    class Book:
        def __init__(self, _id, name, author, publishedYear):
            self._id = _id
            self.name = name
            self.author = author
            self.publishedYear = publishedYear

    schema = fields.Namespace("http://schema.org/")

    class BookSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)
        author = fields.String(schema.author)
        publishedYear = fields.Integer(schema.publishedYear)

        class Meta:
            rdf_type = schema.Book
            model = Book

    book = Book(
        _id="http://example.com/books/1", name="The Great Gatsby", author="F. Scott Fitzgerald", publishedYear=1925
    )

    jsonld_pure = BookSchema().dump(book)

    with pytest.raises(ValueError, match="Invalid properties found in ontology.*"):
        jsonld_validated = BookSchema().validate_properties(
            book, "tests/fixtures/book_ontology.owl", return_valid_data=True, strict=True
        )

    jsonld_validated = BookSchema().validate_properties(
        book, "tests/fixtures/book_ontology.owl", return_valid_data=True
    )

    assert "http://schema.org/name" in jsonld_validated
    assert jsonld_validated["http://schema.org/name"] == book.name
    assert "@id" in jsonld_validated
    assert jsonld_validated["@id"] == book._id
    assert "@type" in jsonld_validated
    assert jsonld_validated["@type"] == ["http://schema.org/Book"]
    assert "http://schema.org/author" in jsonld_validated
    assert jsonld_validated["http://schema.org/author"] == book.author

    assert "http://schema.org/publishedYear" not in jsonld_validated
    assert "http://schema.org/publishedYear" in jsonld_pure


def test_namespace_verification():
    """The ontology doesn't contain the property of publishedYear so it shoudn't be included in the jsonld returned"""

    schema = fields.Namespace("http://schema.org/", ontology="tests/fixtures/book_ontology.owl")

    with pytest.raises(ValueError, match="Property publishedYear does not exist in namespace http://schema.org/"):
        schema.publishedYear

    # this should not throw an exception, so the test passes
    assert schema.name
    assert schema.author
