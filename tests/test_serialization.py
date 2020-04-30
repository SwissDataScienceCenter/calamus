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
