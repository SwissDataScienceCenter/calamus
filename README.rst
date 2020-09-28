..
    Copyright 2017-2020 - Swiss Data Science Center (SDSC)
    A partnership between École Polytechnique Fédérale de Lausanne (EPFL) and
    Eidgenössische Technische Hochschule Zürich (ETHZ).

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

.. image:: https://github.com/SwissDataScienceCenter/calamus/blob/master/docs/reed.png?raw=true
   :align: center

==================================================
 calamus: JSON-LD Serialization Library for Python
==================================================

.. image:: https://readthedocs.org/projects/calamus/badge/?version=latest
   :target: https://calamus.readthedocs.io/en/latest/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/SwissDataScienceCenter/calamus/workflows/Test,%20Integration%20Tests%20and%20Deploy/badge.svg
   :target: https://github.com/SwissDataScienceCenter/calamus/actions?query=workflow%3A%22Test%2C+Integration+Tests+and+Deploy%22+branch%3Amaster

.. image:: https://badges.gitter.im/SwissDataScienceCenter/calamus.svg
   :target: https://gitter.im/SwissDataScienceCenter/calamus?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge

calamus is a library built on top of marshmallow to allow (de-)Serialization
of Python classes to JSON-LD


Installation
============

calamus releases and development versions are available from `PyPI
<https://pypi.org/project/calamus/>`_. You can install it using any tool that
knows how to handle PyPI packages.

With pip:

::

    $ pip install calamus


Usage
=====

Assuming you have a class like

.. code-block:: python

    class Book:
        def __init__(self, _id, name):
            self._id = _id
            self.name = name

Declare schemes
---------------
You can declare a schema for serialization like

.. code-block:: python

    from calamus import fields
    from calamus.schema import JsonLDSchema

    schema = fields.Namespace("http://schema.org/")

    class BookSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)

        class Meta:
            rdf_type = schema.Book
            model = Book

The ``fields.Namespace`` class represents an ontology namespace.

Make sure to set ``rdf_type`` to the RDF triple type you want get and
``model`` to the python class this schema applies to.

Serializing objects ("Dumping")
-------------------------------

You can now easily serialize python classes to JSON-LD

.. code-block:: python

    book = Book(_id="http://example.com/books/1", name="Ilias")
    jsonld_dict = BookSchema().dump(book)
    #{
    #    "@id": "http://example.com/books/1",
    #    "@type": "http://schema.org/Book",
    #    "http://schema.org/name": "Ilias",
    #}

    jsonld_string = BookSchema().dumps(book)
    #'{"@id": "http://example.com/books/1", "http://schema.org/name": "Ilias", "@type": "http://schema.org/Book"}')

Deserializing objects ("Loading")
---------------------------------

You can also easily deserialize JSON-LD to python objects

.. code-block:: python

    data = {
        "@id": "http://example.com/books/1",
        "@type": "http://schema.org/Book",
        "http://schema.org/name": "Ilias",
    }
    book = BookSchema().load(data)
    #<Book(_id="http://example.com/books/1", name="Ilias")>

Validation of properties in a namespace using an OWL ontology
-------------------------------------------------------------

You can validate properties in a python class during serialization using an OWL ontology. The ontology used in the example below doesn't have ``publishedYear`` defined as a property.
::

    class Book:
        def __init__(self, _id, name, author, publishedYear):
            self._id = _id
            self.name = name
            self.author = author
            self.publishedYear = publishedYear

    class BookSchema(JsonLDSchema):
        _id = fields.Id()
        name = fields.String(schema.name)
        author = fields.String(schema.author)
        publishedYear = fields.Integer(schema.publishedYear)

        class Meta:
           rdf_type = schema.Book
           model = Book

    book = Book(id="http://example.com/books/2", name="Outliers", author="Malcolm Gladwell", publishedYear=2008)

    data = {
        "@id": "http://example.com/books/3",
        "@type": "http://schema.org/Book",
        "http://schema.org/name" : "Harry Potter & The Prisoner of Azkaban",
        "http://schema.org/author" : "J. K. Rowling",
        "http://schema.org/publishedYear" : 1999
    }

    valid_invalid_dict = BookSchema().validate_properties(
        data,
        "tests/fixtures/book_ontology.owl"
    )
    # The ontology doesn't have a publishedYear property
    # {'valid': {'http://schema.org/author', 'http://schema.org/name'}, 'invalid': {'http://schema.org/publishedYear'}}

    validated_json = BookSchema().validate_properties(book, "tests/fixtures/book_ontology.owl", return_valid_data=True)
    #{'@id': 'http://example.com/books/2', '@type': ['http://schema.org/Book'], 'http://schema.org/name': 'Outliers', 'http://schema.org/author': 'Malcolm Gladwell'}



You can also use this during deserialization.
::

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
        "@id": "http://example.com/books/1",
        "@type": "http://schema.org/Book",
        "http://schema.org/name": "Harry Potter & The Chamber of Secrets",
        "http://schema.org/author": "J. K. Rowling",
        "http://schema.org/publishedYear": 1998,
    }

    verified_data = BookSchema().validate_properties(data, "tests/fixtures/book_ontology.owl", return_valid_data=True)

    book_verified = BookSchema().load(verified_data)
    #<Book(_id="http://example.com/books/1", name="Harry Potter & The Chamber of Secrets", author="J. K. Rowling")>


The function validate_properties has 3 arguments: ``data``, ``ontology`` and ``return_valid_data``.

``data`` can be a Json-LD, a python object of the schema's model class, or a list of either of those.

``ontology`` is a string pointing to the OWL ontology's location (path or URI).

``return_valid_data`` is an optional argument with the default value ``False``. Default behavior is to return dictionary with valid and invalid properties. Setting this to True returns the JSON-LD with only validated properties.

Annotations
-----------

Classes can also be annotated directly with schema information, removing the need to have a separate schema. This
can be done by setting the ``metaclass`` of the model to ``JsonLDAnnotation``.

.. code-block:: python

    import datetime.datetime as dt

    from calamus import JsonLDAnnotation
    import calamus.fields as fields

    schema = fields.Namespace("http://schema.org/")

    class User(metaclass=JsonLDAnnotation):
        _id = fields.Id()
        birth_date = fields.Date(schema.birthDate, default=dt.now)
        name = fields.String(schema.name, default=lambda: "John")

        class Meta:
            rdf_type = schema.Person

    user = User()

    # dumping
    User.schema().dump(user)
    # or
    user.dump()

    # loading
    u = User.schema().load({"_id": "http://example.com/user/1", "name": "Bill", "birth_date": "1970-01-01 00:00"})

Support
=======

You can reach us on our `Gitter Channel <https://gitter.im/SwissDataScienceCenter/calamus>`_.
