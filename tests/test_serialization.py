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
            class_type = schema.Book

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
            class_type = schema.Book
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
            class_type = schema.Book
            mapped_type = Book

    class AuthorSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)
        books = fields.Nested(schema.author, BookSchema, reverse=True, many=True)

        class Meta:
            class_type = schema.Person
            mapped_type = Author

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
