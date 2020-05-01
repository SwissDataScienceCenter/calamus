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
            class_type = schema.Book
            mapped_type = Book

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
            class_type = schema.Book
            mapped_type = Book

    data = '{"@id": "http://example.com/books/1", "http://schema.org/name": "Hitchhikers Guide to the Galaxy", "@type": "http://schema.org/Book"}'

    book = BookSchema().loads(data)

    assert book._id == "http://example.com/books/1"
    assert book.name == "Hitchhikers Guide to the Galaxy"
