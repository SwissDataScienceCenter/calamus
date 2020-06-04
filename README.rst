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

::

    class Book:
        def __init__(self, _id, name):
            self._id = _id
            self.name = name

Declare schemes
---------------
You can declare a schema for serialization like
::

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

::

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

::

    data = {
        "@id": "http://example.com/books/1",
        "@type": "http://schema.org/Book",
        "http://schema.org/name": "Ilias",
    }
    book = BookSchema().load(data)
    #<Book(_id="http://example.com/books/1", name="Ilias")>


Support
=======

You can reach us on our `Gitter Channel <https://gitter.im/SwissDataScienceCenter/calamus>`_.
