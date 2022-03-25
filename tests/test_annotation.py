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

from functools import lru_cache
import functools
from marshmallow import pre_load

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


def test_annotation_meta_option():
    """Test annotation support with marshmallow meta option."""
    schema = fields.Namespace("http://schema.org/")

    class Book(metaclass=JsonLDAnnotation):
        _id = fields.Id()
        name = fields.String(schema.name)

        def __init__(self, _id, name=""):
            self._id = _id
            self.name = name

        class Meta:
            rdf_type = schema.Book
            exclude = ("name",)

    data = {"@id": "http://example.com/books/1", "@type": ["http://schema.org/Book"]}

    book = Book.schema().load(data)

    assert book._id == "http://example.com/books/1"
    assert book.name == ""

    dumped = Book.schema().dump(book)
    assert data == dumped
    assert "http://schema.org/name" not in data

    dumped = book.dump()
    assert data == dumped
    assert "http://schema.org/name" not in data


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


def test_annotation_inheritance():
    """Test that inheritance works for annotated classes."""
    schema = fields.Namespace("http://schema.org/")

    class Book(metaclass=JsonLDAnnotation):
        _id = fields.Id()
        name = fields.String(schema.name)

        def __init__(self, _id, name):
            self._id = _id
            self.name = name

        class Meta:
            rdf_type = schema.Book

    class Schoolbook(Book):
        course = fields.String(schema.course)

        def __init__(self, _id, name, course):
            self.course = course
            super().__init__(_id, name)

        class Meta(Book.Meta):
            rdf_type = Book.Meta.rdf_type

    data = {
        "@id": "http://example.com/books/1",
        "@type": ["http://schema.org/Book"],
        "http://schema.org/name": "Hitchhikers Guide to the Galaxy",
        "http://schema.org/course": "Literature",
    }

    book = Schoolbook.schema().load(data)

    assert book._id == "http://example.com/books/1"
    assert book.name == "Hitchhikers Guide to the Galaxy"
    assert book.course == "Literature"

    dumped = Schoolbook.schema().dump(book)
    assert data == dumped

    dumped = book.dump()
    assert data == dumped


def test_annotation_without_inheritance():
    """Test that inheritance works for annotated classes with type inheritance disabled."""
    schema = fields.Namespace("http://schema.org/")

    class Book(metaclass=JsonLDAnnotation):
        _id = fields.Id()
        name = fields.String(schema.name)

        def __init__(self, _id, name):
            self._id = _id
            self.name = name

        class Meta:
            rdf_type = schema.Book

    class Schoolbook(Book):
        course = fields.String(schema.course)

        def __init__(self, _id, name, course):
            self.course = course
            super().__init__(_id, name)

        class Meta(Book.Meta):
            rdf_type = schema.SchoolBook
            inherit_parent_types = False

    data = {
        "@id": "http://example.com/books/1",
        "@type": ["http://schema.org/SchoolBook"],
        "http://schema.org/name": "Hitchhikers Guide to the Galaxy",
        "http://schema.org/course": "Literature",
    }

    book = Schoolbook.schema().load(data)

    assert book._id == "http://example.com/books/1"
    assert book.name == "Hitchhikers Guide to the Galaxy"
    assert book.course == "Literature"

    dumped = Schoolbook.schema().dump(book)
    assert data == dumped

    dumped = book.dump()
    assert data == dumped


def test_annotation_without_inheritance_multiple():
    """Test that inheritance works for annotated classes with type inheritance enabled selectively."""
    schema = fields.Namespace("http://schema.org/")

    class Book(metaclass=JsonLDAnnotation):
        _id = fields.Id()
        name = fields.String(schema.name)

        def __init__(self, _id, name):
            self._id = _id
            self.name = name

        class Meta:
            rdf_type = schema.Book

    class Schoolbook(Book):
        course = fields.String(schema.course)

        def __init__(self, _id, name, course):
            self.course = course
            super().__init__(_id, name)

        class Meta:
            rdf_type = schema.SchoolBook
            inherit_parent_types = False

    class Biologybook(Schoolbook):
        topic = fields.String(schema.topic)

        def __init__(self, _id, name, course, topic):
            self.topic = topic
            super().__init__(_id, name, course)

        class Meta:
            rdf_type = schema.BiologyBook
            inherit_parent_types = True

    data = {
        "@id": "http://example.com/books/1",
        "@type": ["http://schema.org/BiologyBook", "http://schema.org/SchoolBook"],
        "http://schema.org/name": "Hitchhikers Guide to the Galaxy",
        "http://schema.org/course": "Literature",
        "http://schema.org/topic": "Genetics",
    }

    book = Biologybook.schema().load(data)

    assert book._id == "http://example.com/books/1"
    assert book.name == "Hitchhikers Guide to the Galaxy"
    assert book.course == "Literature"
    assert book.topic == "Genetics"

    dumped = Biologybook.schema().dump(book)
    assert data == dumped

    dumped = book.dump()
    assert data == dumped


def test_annotation_multiple_inheritance():
    """Test that inheritance works for annotated classes."""
    schema = fields.Namespace("http://schema.org/")

    class Book(metaclass=JsonLDAnnotation):
        _id = fields.Id()
        name = fields.String(schema.name)

        def __init__(self, _id, name):
            self._id = _id
            self.name = name

        class Meta:
            rdf_type = schema.Book

    class EducationMaterial(metaclass=JsonLDAnnotation):
        _id = fields.Id()
        grade = fields.String(schema.grade)

        def __init__(self, _id, grade):
            self._id = _id
            self.grade = grade

        class Meta:
            rdf_type = schema.EducationMaterial

    class Schoolbook(Book, EducationMaterial):
        course = fields.String(schema.course)

        def __init__(self, _id, name, course):
            self.course = course
            super().__init__(_id, name)

        class Meta:
            rdf_type = schema.SchoolBook

    data = {
        "@id": "http://example.com/books/1",
        "@type": ["http://schema.org/Book", "http://schema.org/EducationMaterial", "http://schema.org/SchoolBook"],
        "http://schema.org/name": "Hitchhikers Guide to the Galaxy",
        "http://schema.org/course": "Literature",
        "http://schema.org/grade": "Primary",
    }

    book = Schoolbook.schema().load(data)

    assert book._id == "http://example.com/books/1"
    assert book.name == "Hitchhikers Guide to the Galaxy"
    assert book.course == "Literature"
    assert book.grade == "Primary"

    dumped = Schoolbook.schema().dump(book)
    assert data == dumped

    dumped = book.dump()
    assert data == dumped


def test_annotation_hook_inheritance():
    """Test that inheritance works for hooks declared on annotated classes."""
    schema = fields.Namespace("http://schema.org/")

    class Book(metaclass=JsonLDAnnotation):
        _id = fields.Id()
        name = fields.String(schema.name)

        def __init__(self, _id, name):
            self._id = _id
            self.name = name

        class Meta:
            rdf_type = schema.Book

            @pre_load
            def _preload(self, in_data, **kwargs):
                in_data["@id"] += "hook1"
                return in_data

    class Schoolbook(Book):
        course = fields.String(schema.course)

        def __init__(self, _id, name, course):
            self.course = course
            super().__init__(_id, name)

        class Meta(Book.Meta):
            rdf_type = Book.Meta.rdf_type

            @pre_load
            def _preload(self, in_data, **kwargs):
                super()._preload(in_data, **kwargs)
                in_data["@id"] += "hook2"
                return in_data

    data = {
        "@id": "http://example.com/books/1",
        "@type": ["http://schema.org/Book"],
        "http://schema.org/name": "Hitchhikers Guide to the Galaxy",
        "http://schema.org/course": "Literature",
    }

    book = Schoolbook.schema().load(data)

    assert book._id.endswith("hook1hook2")


def test_annotation_hook_inheritance_with_extra_closure():
    """Test that inheritance works for hooks declared on annotated classes with extra closures in the hook."""
    schema = fields.Namespace("http://schema.org/")

    x = 3
    y = 4

    class Book(metaclass=JsonLDAnnotation):
        _id = fields.Id()
        name = fields.String(schema.name)

        def __init__(self, _id, name):
            self._id = _id
            self.name = name

        class Meta:
            rdf_type = schema.Book

            @pre_load
            def _preload(self, in_data, **kwargs):
                in_data["@id"] += f"hook{x}"
                return in_data

    class Schoolbook(Book):
        course = fields.String(schema.course)

        def __init__(self, _id, name, course):
            self.course = course
            super().__init__(_id, name)

        class Meta(Book.Meta):
            rdf_type = Book.Meta.rdf_type

            @pre_load
            def _preload(self, in_data, **kwargs):
                super()._preload(in_data, **kwargs)
                in_data["@id"] += f"hook{y}"
                return in_data

    data = {
        "@id": "http://example.com/books/1",
        "@type": ["http://schema.org/Book"],
        "http://schema.org/name": "Hitchhikers Guide to the Galaxy",
        "http://schema.org/course": "Literature",
    }

    book = Schoolbook.schema().load(data)

    assert book._id.endswith(f"hook{x}hook{y}")


def test_annotation_hook_inheritance_with_additional_decorator():
    """Test that inheritance works for hooks declared on annotated classes with decorators other than the hook."""
    schema = fields.Namespace("http://schema.org/")

    def my_decorator(value):
        def actual_decorator(func):
            @functools.wraps(func)
            def wrapper_my_decorator(self, in_data, *args, **kwargs):
                in_data["@id"] += f"dec{value}"
                return func(self, in_data, *args, **kwargs)

            return wrapper_my_decorator

        return actual_decorator

    class Book(metaclass=JsonLDAnnotation):
        _id = fields.Id()
        name = fields.String(schema.name)

        def __init__(self, _id, name):
            self._id = _id
            self.name = name

        class Meta:
            rdf_type = schema.Book

            @pre_load
            @my_decorator(1)
            def _preload(self, in_data, **kwargs):
                in_data["@id"] += "hook1"
                return in_data

    class Schoolbook(Book):
        course = fields.String(schema.course)

        def __init__(self, _id, name, course):
            self.course = course
            super().__init__(_id, name)

        class Meta(Book.Meta):
            rdf_type = Book.Meta.rdf_type

            @my_decorator(2)
            @pre_load
            def _preload(self, in_data, **kwargs):
                super()._preload(in_data, **kwargs)
                in_data["@id"] += "hook2"
                return in_data

    data = {
        "@id": "http://example.com/books/1",
        "@type": ["http://schema.org/Book"],
        "http://schema.org/name": "Hitchhikers Guide to the Galaxy",
        "http://schema.org/course": "Literature",
    }

    book = Schoolbook.schema().load(data)

    assert book._id.endswith("dec2dec1hook1hook2")
