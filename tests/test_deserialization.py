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
            class_type = schema.Book
            mapped_type = Book

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
            class_type = schema.Book
            mapped_type = Book
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
            class_type = schema.Book
            mapped_type = Book

    class AuthorSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)
        books = fields.Nested(schema.author, BookSchema, reverse=True, many=True)

        class Meta:
            class_type = schema.Person
            mapped_type = Author

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
