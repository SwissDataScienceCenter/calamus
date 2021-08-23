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
from calamus.schema import JsonLDSchema, blank_node_id_strategy


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


def test_multiple_nested_flattened_reverse_serialization():
    """Test that we can output flattened jsonld for multiple nested objects."""

    class A:
        def __init__(self, _id, name):
            self._id = _id
            self.name = name

    class B:
        def __init__(self, _id, name, children):
            self._id = _id
            self.name = name
            self.children = children

    class C:
        def __init__(self, _id, name, children):
            self._id = _id
            self.name = name
            self.children = children

    schema = fields.Namespace("http://schema.org/")

    class ASchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)

        class Meta:
            rdf_type = schema.A
            model = A

    class BSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)
        children = fields.Nested(schema.parent, ASchema, reverse=True, many=True)

        class Meta:
            rdf_type = schema.B
            model = B

    class CSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)
        children = fields.Nested(schema.parent, BSchema, reverse=True, many=True)

        class Meta:
            rdf_type = schema.C
            model = C

    a1 = A("http://example.com/a/1", "a1")
    a2 = A("http://example.com/a/2", "a2")
    a3 = A("http://example.com/a/3", "a3")

    b1 = B("http://example.com/b/1", "b1", [a1, a2])
    b2 = B("http://example.com/b/2", "b2", [a3])

    c = C("http://example.com/c/1", "c1", [b1, b2])

    jsonld = CSchema(flattened=True).dump(c)

    assert len(jsonld) == 6

    as1 = next(e for e in jsonld if e["@id"] == "http://example.com/a/1")
    as3 = next(e for e in jsonld if e["@id"] == "http://example.com/a/3")
    bs1 = next(e for e in jsonld if e["@id"] == "http://example.com/b/1")
    bs2 = next(e for e in jsonld if e["@id"] == "http://example.com/b/2")
    cs = next(e for e in jsonld if e["@id"] == "http://example.com/c/1")

    assert "http://schema.org/name" in cs
    assert cs["http://schema.org/name"][0]["@value"] == c.name
    assert "@id" in cs
    assert cs["@id"] == c._id
    assert "@type" in cs
    assert cs["@type"] == ["http://schema.org/C"]

    assert "http://schema.org/name" in bs1
    assert bs1["http://schema.org/name"][0]["@value"] == b1.name
    assert "@id" in bs1
    assert bs1["@id"] == b1._id
    assert "@type" in bs1
    assert bs1["@type"] == ["http://schema.org/B"]

    assert "http://schema.org/name" in bs2
    assert bs2["http://schema.org/name"][0]["@value"] == b2.name
    assert "@id" in bs2
    assert bs2["@id"] == b2._id
    assert "@type" in bs2
    assert bs2["@type"] == ["http://schema.org/B"]

    assert "http://schema.org/name" in as1
    assert as1["http://schema.org/name"][0]["@value"] == a1.name
    assert "@id" in as1
    assert as1["@id"] == a1._id
    assert "@type" in as1
    assert as1["@type"] == ["http://schema.org/A"]

    assert "http://schema.org/name" in as3
    assert as3["http://schema.org/name"][0]["@value"] == a3.name
    assert "@id" in as3
    assert as3["@id"] == a3._id
    assert "@type" in as3
    assert as3["@type"] == ["http://schema.org/A"]


def test_iri_field_serialization():
    """Tests serialization of IRI fields."""

    class A(object):
        def __init__(self, _id, url):
            super().__init__()
            self._id = _id
            self.url = url

    schema = fields.Namespace("http://schema.org/")

    class ASchema(JsonLDSchema):
        _id = fields.Id()
        url = fields.IRI(schema.url)

        class Meta:
            rdf_type = schema.A
            model = A

    a = A("http://example.com/1", "http://datascience.ch")

    jsonld = ASchema().dump(a)

    assert "http://schema.org/url" in jsonld
    assert "@id" in jsonld["http://schema.org/url"]
    assert jsonld["http://schema.org/url"]["@id"] == "http://datascience.ch"

    b = A("http://example.com/2", None)

    jsonld = ASchema().dump(b)

    assert "http://schema.org/url" in jsonld
    assert jsonld["http://schema.org/url"] == None


def test_lazy_proxy_serialization():
    """Tests that lazy deserialization works."""
    from calamus.utils import Proxy

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
        name = fields.String(schema.name)

        class Meta:
            rdf_type = schema.Genre
            model = Genre
            id_generation_strategy = blank_node_id_strategy

    class BookSchema(JsonLDSchema):
        name = fields.String(schema.name)
        genre = fields.Nested(schema.genre, GenreSchema)

        class Meta:
            rdf_type = schema.Book
            model = Book
            id_generation_strategy = blank_node_id_strategy

    class AuthorSchema(JsonLDSchema):
        name = fields.String(schema.name)
        books = fields.Nested(schema.books, BookSchema, many=True)

        class Meta:
            rdf_type = schema.Author
            model = Author
            id_generation_strategy = blank_node_id_strategy

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
        "@id": "_:dummyid",
    }

    a = AuthorSchema(lazy=True).load(data)

    assert a.name == "Miguel de Cervantes"
    book = a.books[0]

    assert isinstance(book, Proxy)

    author = AuthorSchema().dump(a)

    assert not book.__proxy_initialized__

    assert author.keys() == data.keys()

    original_book = BookSchema(flattened=False).dump(book)
    assert isinstance(original_book, dict)
    assert not book.__proxy_initialized__

    flat_book = BookSchema(flattened=True).dump(book)

    assert isinstance(flat_book, list)
    assert len(flat_book) == 2
    assert book.__proxy_initialized__


def test_blank_node_serialization():
    """Test serialization with blank-node ids."""

    class A(object):
        def __init__(self, _id, name):
            self._id = _id
            self.name = name

    class B(object):
        def __init__(self, _id, value):
            self._id = _id
            self.value = value

    schema = fields.Namespace("http://schema.org/")

    class ASchema(JsonLDSchema):
        _id = fields.BlankNodeId()
        name = fields.String(schema.name)

        class Meta:
            rdf_type = schema.A
            model = A

    class BSchema(JsonLDSchema):
        _id = fields.BlankNodeId()
        value = fields.Nested(schema.specifiedBy, ASchema)

        class Meta:
            rdf_type = schema.B
            model = B

    b = B("dummyid2", A("dummyid1", "test"))

    jsonld = BSchema().dump(b)

    assert "@id" in jsonld
    assert jsonld["@id"] == "_:dummyid2"
    assert "http://schema.org/specifiedBy" in jsonld

    dumped_a = jsonld["http://schema.org/specifiedBy"]

    assert "@id" in dumped_a
    assert dumped_a["@id"] == "_:dummyid1"


def test_blank_node_id_generation():
    """Test serialization with generated blank-node ids."""

    class A(object):
        def __init__(self, name):
            self.name = name

    class B(object):
        def __init__(self, value):
            self.value = value

    schema = fields.Namespace("http://schema.org/")

    class ASchema(JsonLDSchema):
        name = fields.String(schema.name)

        class Meta:
            rdf_type = schema.A
            model = A
            id_generation_strategy = blank_node_id_strategy

    class BSchema(JsonLDSchema):
        value = fields.Nested(schema.specifiedBy, ASchema)

        class Meta:
            rdf_type = schema.B
            model = B
            id_generation_strategy = blank_node_id_strategy

    b = B(A("test"))

    jsonld = BSchema().dump(b)

    assert "@id" in jsonld
    assert jsonld["@id"].startswith("_:")
    assert "http://schema.org/specifiedBy" in jsonld

    dumped_a = jsonld["http://schema.org/specifiedBy"]

    assert "@id" in dumped_a
    assert dumped_a["@id"].startswith("_:")


def test_date_time_serialization():
    """Tests serialization of different date/time fields."""

    class A(object):
        def __init__(self, _id, dt, naive_dt, aware_dt, date, time):
            super().__init__()
            self._id = _id
            self.dt = dt
            self.naive_dt = naive_dt
            self.aware_dt = aware_dt
            self.date = date
            self.time = time

    schema = fields.Namespace("http://schema.org/")

    class ASchema(JsonLDSchema):
        _id = fields.Id()
        dt = fields.DateTime(schema.dateTime)
        naive_dt = fields.NaiveDateTime(schema.naiveDateTime)
        aware_dt = fields.AwareDateTime(schema.awareDateTime)
        date = fields.Date(schema.date)
        time = fields.Time(schema.time)

        class Meta:
            rdf_type = schema.A
            model = A

    import datetime as dt

    a = A(
        "http://example.com/1",
        dt.datetime(2007, 12, 6, 16, 29, 43),
        dt.datetime(2020, 8, 18, 12, 45, 43),
        dt.datetime(2020, 6, 6, 23, 59, 59, tzinfo=dt.timezone(dt.timedelta(hours=1))),
        dt.date(2002, 12, 31),
        dt.time(12, 10, 30),
    )

    jsonld = ASchema().dump(a)

    assert "http://schema.org/awareDateTime" in jsonld
    assert jsonld["http://schema.org/awareDateTime"] == "2020-06-06T23:59:59+01:00"

    assert "http://schema.org/date" in jsonld
    assert jsonld["http://schema.org/date"] == "2002-12-31"

    assert "http://schema.org/dateTime" in jsonld
    assert jsonld["http://schema.org/dateTime"] == "2007-12-06T16:29:43"

    assert "http://schema.org/naiveDateTime" in jsonld
    assert jsonld["http://schema.org/naiveDateTime"] == "2020-08-18T12:45:43"

    assert "http://schema.org/time" in jsonld
    assert jsonld["http://schema.org/time"] == "12:10:30"


def test_rawjsonld_deserialization():
    """Tests deserialization of raw JSON-LD field."""

    class A(object):
        def __init__(self, _id, simple, nested):
            super().__init__()
            self._id = _id
            self.simple = simple
            self.nested = nested

    schema = fields.Namespace("http://schema.org/")

    class ASchema(JsonLDSchema):
        _id = fields.Id()
        simple = fields.RawJsonLD("http://www.w3.org/ns/oa#hasBody")
        nested = fields.RawJsonLD("http://www.w3.org/ns/oa#hasBody2")

        class Meta:
            rdf_type = schema.A
            model = A

    raw_field = {
        "@id": "example_run123",
        "@type": "http://www.w3.org/ns/mls#Run",
        "http://www.w3.org/ns/mls#implements": {
            "http://www.w3.org/2000/01/rdf-schema#label": "sklearn.ensemble._forest.RandomForestClassifier",
            "@id": "sklearn.ensemble._forest.RandomForestClassifier",
            "@type": ["http://www.w3.org/ns/mls#Algorithm"],
        },
    }
    is_partof_raw_field = [
        {
            "@id": "id1",
            "@type": "http://www.w3.org/ns/mls#Run",
            "http://schema.org/isPartOf": {
                "@id": "id2",
                "@type": "http://www.w3.org/ns/mls#Algorithm",
                "http://www.w3.org/2000/01/rdf-schema#label": "sklearn.ensemble._forest.RandomForestClassifier",
            },
        }
    ]

    data = {
        "@type": ["https://schema.org/A"],
        "@id": "_:dummyid",
        "http://www.w3.org/ns/oa#hasBody": raw_field,
        "http://www.w3.org/ns/oa#hasBody2": is_partof_raw_field,
    }

    a = ASchema().load(data)
    assert a.simple["@id"] == "example_run123"
    assert "http://www.w3.org/ns/mls#implements" in a.simple
    assert a.simple["http://www.w3.org/ns/mls#implements"]["@id"] == "sklearn.ensemble._forest.RandomForestClassifier"

    # test loading raw JSON-LD field that was flattened
    jsonld = ASchema(flattened=True).dump(a)

    a = ASchema(flattened=True).load(jsonld)
    assert a.simple["@id"] == "example_run123"
    assert "http://www.w3.org/ns/mls#implements" in a.simple
    assert (
        a.simple["http://www.w3.org/ns/mls#implements"][0]["@id"] == "sklearn.ensemble._forest.RandomForestClassifier"
    )
    assert a.nested["@id"] == "id1"
    assert a.nested["http://schema.org/isPartOf"][0]["@id"] == "id2"
    assert (
        a.nested["http://schema.org/isPartOf"][0]["http://www.w3.org/2000/01/rdf-schema#label"][0]["@value"]
        == "sklearn.ensemble._forest.RandomForestClassifier"
    )
