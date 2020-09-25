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
"""Calamus utilities."""

import types
import typing
from lazy_object_proxy.slots import Proxy as LazyProxy, _ProxyMetaType
from lazy_object_proxy.compat import with_metaclass
import rdflib
from rdflib.plugins.sparql import prepareQuery


JSON_LD_SYNTAX_TOKENS = [
    "@id",
    "@type",
    "@base",
    "@container",
    "@context",
    "@direction",
    "@graph",
    "@import",
    "@included",
    "@index",
    "@json",
    "@language",
    "@list",
    "@nest",
    "@none",
    "@prefix",
    "@propagate",
    "@protected",
    "@reverse",
    "@set",
    "@value",
    "@version",
    "@vocab",
]

ONTOLOGY_QUERY = prepareQuery(
    "ask { { ?property rdf:type <http://www.w3.org/2002/07/owl#DatatypeProperty> .} UNION { ?property rdf:type "
    "<http://www.w3.org/2002/07/owl#ObjectProperty> .} }"
)


def normalize_id(
    id_object: typing.Union[typing.Mapping[str, typing.Any], typing.Iterable[typing.Mapping[str, typing.Any]], str]
):
    """Turns a JsonLD id reference into normalized form (list of strings)."""
    if isinstance(id_object, str):
        return [id_object]
    if isinstance(id_object, dict):
        if "@id" not in id_object:
            raise ValueError("No @id found in id object")
        return [id_object["@id"]]
    if isinstance(id_object, list) or isinstance(id_object, types.GeneratorType):
        return [i for o in id_object for i in normalize_id(o)]

    return [str(id_object)]


def normalize_type(type_data):
    """Normalizes a JsonLD type reference as list of string."""
    if isinstance(type_data, list) or isinstance(type_data, types.GeneratorType):
        return sorted([t for e in type_data for t in normalize_type(e)])
    if isinstance(type_data, str):
        return [type_data]
    return [str(type_data)]


def normalize_value(value):
    """Normalizes a JsonLD value object to a simple value."""
    if isinstance(value, list):
        if len(value) == 1:
            # single values can be single element lists in jsonld
            return normalize_value(value[0])
        return [normalize_value(v) for v in value]

    if isinstance(value, dict) and "@value" in value:
        return value["@value"]

    return value


def validate_field_properties(data, ontology, query=None, mem={"valid": set(), "invalid": set()}):
    """Validates if the field properties for data are present in the OWL ontology graph or not.

    Args:
        data (dict): The data to validate.
        ontology (``rdflib.Graph``): The OWL ontology graph to validate against.
        query (``rdflib.plugins.sparql.sparql.prepareQuery``): Optional prepared query (for performance reasons).
        mem (dict): memoization for repeated calls.

    Returns:
        dict: Key ``valid`` has all valid properties (excluding @id and @type), ``invalid`` has all invalid properties
    """

    res = {"valid": set(), "invalid": set()}

    if query is None:
        query = ONTOLOGY_QUERY

    if not isinstance(data, dict):
        raise ValueError("`data` must be a dict.")

    if not isinstance(ontology, rdflib.Graph):
        raise ValueError("`graph` must be an `rdflib.Graph`")

    for prop in data.keys():
        if prop in mem["valid"]:
            res["valid"].add(prop)
            continue
        if prop in mem["invalid"]:
            res["invalid"].add(prop)
            continue

        # after checking memoization
        if prop not in JSON_LD_SYNTAX_TOKENS:
            p = rdflib.URIRef(prop)
            qres = ontology.query(query, initBindings={"property": p})
            if next(iter(qres), False):
                res["valid"].add(prop)
            else:
                res["invalid"].add(prop)
    return res


class Proxy(LazyProxy, with_metaclass(_ProxyMetaType)):
    """Proxy object to support lazy loading."""

    __slots__ = "__target__", "__factory__", "__proxy_initialized__", "__proxy_schema__", "__proxy_original_data__"

    def __init__(self, factory, schema, original_data):
        object.__setattr__(self, "__factory__", factory)
        object.__setattr__(self, "__proxy_initialized__", False)
        object.__setattr__(self, "__proxy_schema__", schema)
        object.__setattr__(self, "__proxy_original_data__", original_data)

    @property
    def __wrapped__(
        self, __getattr__=object.__getattribute__, __setattr__=object.__setattr__, __delattr__=object.__delattr__
    ):
        try:
            return __getattr__(self, "__target__")
        except AttributeError:
            try:
                factory = __getattr__(self, "__factory__")
            except AttributeError:
                raise ValueError("Proxy hasn't been initiated: __factory__ is missing.")
            target = factory()
            __setattr__(self, "__target__", target)
            __setattr__(self, "__proxy_initialized__", True)
            return target

    def __setattr__(self, name, value, __setattr__=object.__setattr__):
        if hasattr(type(self), name):
            __setattr__(self, name, value)
        else:
            setattr(self.__wrapped__, name, value)

    def __getattr__(self, name):
        if name in (
            "__wrapped__",
            "__factory__",
            "__proxy_initialized__",
            "__proxy_schema__",
            "__proxy_original_data__",
        ):
            raise AttributeError(name)
        else:
            return getattr(self.__wrapped__, name)
