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
from calamus.schema import JsonLDSchema, blank_node_id_strategy


def test_simple_deserialization():
    class Book:
        def __init__(self, _id, name, year=2020, **kwargs):
            self._id = _id
            self.name = name
            self.year = year
            for k, v in kwargs.items():
                setattr(self, k, v)

    schema = fields.Namespace("http://schema.org/")

    class BookSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)
        isbn = fields.String(schema.isbn)

        class Meta:
            rdf_type = schema.Book
            model = Book

    data = {
        "@id": "http://example.com/books/1",
        "@type": "http://schema.org/Book",
        "http://schema.org/name": "Hitchhikers Guide to the Galaxy",
        "http://schema.org/isbn": "0-330-25864-8",
    }

    book = BookSchema().load(data)

    assert book._id == "http://example.com/books/1"
    assert book.name == "Hitchhikers Guide to the Galaxy"
    assert book.isbn == "0-330-25864-8"
    assert book.year == 2020


def test_deserialization_error_with_missing_data():
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

    data = {
        "@id": "http://example.com/books/1",
        "@type": "http://schema.org/Book",
    }

    with pytest.raises(ValueError) as e:
        BookSchema().load(data)
        assert "Field name not found in data" in str(e)


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
    """Test deserialization of flattened jsonld."""

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
    """Test deserialization of flattened jsonld."""

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


def test_iri_field_deserialization():
    """Tests deserialization of IRI fields."""

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

    data = {
        "@id": "http://example.com/1",
        "@type": ["http://schema.org/A"],
        "http://schema.org/url": {"@id": "http://datascience.ch"},
    }

    a = ASchema().load(data)

    assert a.url == "http://datascience.ch"


@pytest.mark.parametrize("value", [["1"], ["1", "2"]])
def test_list_field_deserialization(value):
    """Test deserialization of List fields."""

    class Entity:
        def __init__(self, field):
            self.field = field

    schema = fields.Namespace("http://schema.org/")

    class EntitySchema(JsonLDSchema):
        field = fields.List(schema.field, fields.String)

        class Meta:
            rdf_type = schema.Entity
            model = Entity

    data = {"@type": ["http://schema.org/Entity"], "http://schema.org/field": value}

    entity = EntitySchema().load(data)

    assert entity.field == value


def test_init_name():
    """Test deserialization of fields with init_name."""

    class Entity:
        def __init__(self, another_field):
            self.field = another_field

    schema = fields.Namespace("http://schema.org/")

    class EntitySchema(JsonLDSchema):
        field = fields.Boolean(schema.field, init_name="another_field")

        class Meta:
            rdf_type = schema.Entity
            model = Entity

    data = {"@type": ["http://schema.org/Entity"], "http://schema.org/field": "true"}

    entity = EntitySchema().load(data)

    assert entity.field is True


def test_init_name_failure():
    """Test deserialization of fields with init_name fails in case of duplication."""

    class Entity:
        def __init__(self, field, another_field):
            self.field = field
            self.another_field = another_field

    schema = fields.Namespace("http://schema.org/")

    class EntitySchema(JsonLDSchema):
        field = fields.Boolean(schema.field, init_name="another_field")
        another_field = fields.Boolean(schema.another_field, missing=False)

        class Meta:
            rdf_type = schema.Entity
            model = Entity

    data = {"@type": ["http://schema.org/Entity"], "http://schema.org/field": "true"}

    with pytest.raises(ValueError) as e:
        EntitySchema().load(data)
        assert "Initialization name another_field for field is already in data" in str(e)


@pytest.mark.parametrize(
    "formats, value, deserialized_value",
    [
        ([], "2020-06-15T08:34:03.607590+00:00", "2020-06-15 08:34:03.607590+00:00"),
        (["%Y-%m-%d"], "2020-06-15", "2020-06-15 00:00:00"),
        (["iso", "%Y-%m-%d", "%Y-%m"], "2020-06", "2020-06-01 00:00:00"),
    ],
)
def test_alternative_date_format_deserialization(formats, value, deserialized_value):
    """Test deserialization of DateTime fields with extra formats."""

    class Entity:
        def __init__(self, field):
            self.field = field

    schema = fields.Namespace("http://schema.org/")

    class EntitySchema(JsonLDSchema):
        field = fields.DateTime(schema.field, extra_formats=formats)

        class Meta:
            rdf_type = schema.Entity
            model = Entity

    data = {"@type": ["http://schema.org/Entity"], "http://schema.org/field": value}

    entity = EntitySchema().load(data)

    assert str(entity.field) == deserialized_value


def test_lazy_deserialization():
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

    assert isinstance(book, Proxy)
    assert " wrapping " not in repr(book)  # make sure proxy is not evaluated yet

    assert book.name == "Don Quixote"
    assert " wrapping " in repr(book)  # make sure proxy is evaluated
    assert book.genre.name == "Novel"


def test_lazy_flattened_deserialization():
    """Tests that lazy deserialization works."""
    from calamus.utils import Proxy

    class Genre:
        def __init__(self, _id, name):
            self._id = _id
            self.name = name

        def test(self):
            return self.name

        def __call__(self):
            return self.name

    class Book:
        def __init__(self, _id, name, genre):
            self._id = _id
            self.name = name
            self.genre = genre

    class Author:
        def __init__(self, _id, name, book):
            self._id = _id
            self.name = name
            self.book = book

    schema = fields.Namespace("https://schema.org/")

    class GenreSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)

        class Meta:
            rdf_type = schema.Genre
            model = Genre

    class BookSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)
        genre = fields.Nested(schema.genre, GenreSchema)

        class Meta:
            rdf_type = schema.Book
            model = Book

    class AuthorSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)
        book = fields.Nested(schema.books, BookSchema)

        class Meta:
            rdf_type = schema.Author
            model = Author

    data = [
        {
            "@id": "http://example.org/author1",
            "@type": ["https://schema.org/Author"],
            "https://schema.org/books": {"@id": "http://example.org/book1"},
            "https://schema.org/name": "Miguel de Cervantes",
        },
        {
            "@id": "http://example.org/book1",
            "@type": ["https://schema.org/Book"],
            "https://schema.org/genre": {"@id": "http://example.org/genre1"},
            "https://schema.org/name": "Don Quixote",
        },
        {"@id": "http://example.org/genre1", "@type": ["https://schema.org/Genre"], "https://schema.org/name": "Novel"},
    ]

    a = AuthorSchema(lazy=True, flattened=True).load(data)

    assert a.name == "Miguel de Cervantes"

    assert isinstance(a.book, Proxy)
    assert " wrapping " not in repr(a.book)  # make sure proxy is not evaluated yet

    assert a.book.name == "Don Quixote"
    assert " wrapping " in repr(a.book)  # make sure proxy is evaluated
    assert a.book.genre.name == "Novel"


def test_generated_id_deserialization():
    """Test deserialization with `id_generation_strategy` used."""

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

    data = {
        "@id": "_:cd54868014124a1e91420cbba92b507e",
        "@type": ["http://schema.org/B"],
        "http://schema.org/specifiedBy": {
            "@id": "_:68bde922a8d1479cb66c705f7a0c8498",
            "@type": ["http://schema.org/A"],
            "http://schema.org/name": "test",
        },
    }

    b = BSchema().load(data)

    assert b.value
    assert b.value.name == "test"


def test_date_time_deserialization():
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

    data = {
        "@id": "http://example.com/1",
        "@type": ["http://schema.org/A"],
        "http://schema.org/awareDateTime": "2020-06-06T23:59:59+01:00",
        "http://schema.org/date": "2002-12-31",
        "http://schema.org/dateTime": "2007-12-06T16:29:43",
        "http://schema.org/naiveDateTime": "2020-08-18T12:45:43",
        "http://schema.org/time": "12:10:30",
    }

    a = ASchema().load(data)

    assert a._id == "http://example.com/1"
    assert a.dt == dt.datetime(2007, 12, 6, 16, 29, 43)
    assert a.naive_dt == dt.datetime(2020, 8, 18, 12, 45, 43)
    assert a.aware_dt == dt.datetime(2020, 6, 6, 23, 59, 59, tzinfo=dt.timezone(dt.timedelta(hours=1)))
    assert a.date == dt.date(2002, 12, 31)
    assert a.time == dt.time(12, 10, 30)
