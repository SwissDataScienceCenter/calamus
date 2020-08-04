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
"""Marshmallow fields for use with JSON-LD."""

from functools import total_ordering

import lazy_object_proxy
import marshmallow.fields as fields
from marshmallow.base import SchemaABC
from marshmallow import class_registry, utils
from marshmallow.exceptions import ValidationError
import logging
import copy
from uuid import uuid4

import typing
import types

from calamus.utils import normalize_type, normalize_value

logger = logging.getLogger("calamus")


@total_ordering
class IRIReference(object):
    """ Represent an IRI in a namespace.

    Args:
        namespace (Namespace): The ``Namespace`` this IRI is part of.
        name (str): the property name of this IRI."""

    def __init__(self, namespace, name):
        self.namespace = namespace
        self.name = name

    def __str__(self):
        """Return expanded string for IRI."""
        return "{namespace}{name}".format(namespace=self.namespace, name=self.name)

    def __repr__(self):
        """Representation of IRI."""
        return 'IRIReference(namespace="{namespace}", name="{name}")'.format(namespace=self.namespace, name=self.name)

    def __eq__(self, other):
        """Check equality between this and an other IRIReference."""
        expanded = str(self)

        if isinstance(other, IRIReference):
            other = str(other)

        return expanded == other

    def __lt__(self, other):
        """Compare this with another IRI."""
        return str(self) < str(other)

    def __hash__(self):
        return str(self).__hash__()


class BlankNodeId(object):
    """ A blank/anonymous node identifier.

    Args:
        name (str): The name used to construct the blank node id. Default: ``None``.
                    Will use a UUID if not supplied."""

    def __init__(self, name=None):
        self.name = name

    def __str__(self):
        if self.name:
            return "_:{name}".format(name=self.name)
        return "_:{uuid}".format(uuid=uuid4)


class Namespace(object):
    """Represents a namespace/ontology.

    Args:
        namespace (str): The base namespace URI for this namespace.
    """

    def __init__(self, namespace):
        self.namespace = namespace

    def __getattr__(self, name):
        return IRIReference(self, name)

    def __str__(self):
        return self.namespace


class _JsonLDField(fields.Field):
    """Internal class that enables marshmallow fields to be serialized with a JsonLD field name.

    Args:
        field_name (IRIReference): The JSON-LD field name.
        reverse (bool): Whether this is a reverse relation (via the ``@reverse`` keyword).
        init_name (str): Name of this parameter in the ``__init__`` method, if it differs from the name on the class.
        add_value_types (bool): Whether to add xsd value type information when serializing.
    """

    def __init__(self, field_name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_name = field_name

        self.reverse = kwargs.get("reverse", False)
        self.init_name = kwargs.get("init_name", None)
        self.add_value_types = kwargs.get("add_value_types", False)

    @property
    def data_key(self):
        """Return the (expanded) JsonLD field name."""
        if self.field_name is None:
            raise ValueError("field_name was not set for {} in schema {}".format(self.name, self.root.__class__))
        return str(self.field_name)

    @data_key.setter
    def data_key(self, value):
        pass

    def _deserialize(self, value, attr, data, **kwargs):
        value = normalize_value(value)
        return super()._deserialize(value, attr, data, **kwargs)

    def _reversed_fields(self):
        """Get fields that are reversed in type hierarchy."""
        return {}


class Id(_JsonLDField, fields.String):
    """A node identifier."""

    def __init__(self, *args, **kwargs):
        super().__init__(field_name="@id", *args, **kwargs)


class String(_JsonLDField, fields.String):
    """A string field."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        value = super()._serialize(value, attr, obj, **kwargs)
        if self.parent.opts.add_value_types or self.add_value_types:
            value = {"@value": value, "@type": "http://www.w3.org/2001/XMLSchema#string"}
        return value


class IRI(String):
    """An external IRI reference."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        value = super()._serialize(value, attr, obj, **kwargs)
        return {"@id": value}

    def _deserialize(self, value, attr, data, **kwargs):
        if "@id" in value:
            value = value["@id"]
        return super()._deserialize(value, attr, data, **kwargs)


class Integer(_JsonLDField, fields.Integer):
    """An integer field."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        value = super()._serialize(value, attr, obj, **kwargs)
        if self.parent.opts.add_value_types or self.add_value_types:
            value = {"@value": value, "@type": "http://www.w3.org/2001/XMLSchema#integer"}
        return value


class Float(_JsonLDField, fields.Float):
    """A float field."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        value = super()._serialize(value, attr, obj, **kwargs)
        if self.parent.opts.add_value_types or self.add_value_types:
            value = {"@value": value, "@type": "http://www.w3.org/2001/XMLSchema#float"}
        return value


class Boolean(_JsonLDField, fields.Boolean):
    """A Boolean field."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        value = super()._serialize(value, attr, obj, **kwargs)
        if self.parent.opts.add_value_types or self.add_value_types:
            value = {"@value": value, "@type": "http://www.w3.org/2001/XMLSchema#boolean"}
        return value


class DateTime(_JsonLDField, fields.DateTime):
    """A date/time field."""

    def __init__(self, *args, extra_formats=("%Y-%m-%d",), **kwargs):
        super().__init__(*args, **kwargs)
        self._extra_formats = extra_formats

    def _serialize(self, value, attr, obj, **kwargs):
        value = super()._serialize(value, attr, obj, **kwargs)
        if self.parent.opts.add_value_types or self.add_value_types:
            value = {"@value": value, "@type": "http://www.w3.org/2001/XMLSchema#dateTime"}
        return value

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return super()._deserialize(value, attr, data, **kwargs)
        except ValidationError:
            pass

        # Try with extra formats
        for format in self._extra_formats:
            try:
                original_format = self.format
                self.format = format
                return super()._deserialize(value, attr, data, **kwargs)
            except ValidationError:
                pass
            finally:
                self.format = original_format

        raise self.make_error("invalid", input=value, obj_type=self.OBJ_TYPE)


class Dict(_JsonLDField, fields.Dict):
    """A dict field."""

    pass


class Raw(_JsonLDField, fields.Raw):
    """A raw field."""

    pass


class Nested(_JsonLDField, fields.Nested):
    """A reference to one or more nested classes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not isinstance(self.nested, list):
            self.nested = [self.nested]

    @property
    def schema(self):
        """The nested Schema object.

        This method was copied from marshmallow and modified to support multiple different nested schemes.
        """
        if not self._schema:
            # Inherit context from parent.
            context = getattr(self.parent, "context", {})
            self._schema = {"from": {}, "to": {}}
            for nest in self.nested:
                if isinstance(nest, SchemaABC):
                    rdf_type = str(normalize_type(nest.opts.rdf_type))
                    model = nest.opts.model
                    if not rdf_type or not model:
                        raise ValueError("Both rdf_type and model need to be set on the schema for nested to work")
                    _schema = copy.copy(nest)
                    _schema.context.update(context)
                    # Respect only and exclude passed from parent and re-initialize fields
                    set_class = _schema.set_class
                    if self.only is not None:
                        if self._schema.only is not None:
                            original = _schema.only
                        else:  # only=None -> all fields
                            original = _schema.fields.keys()
                        _schema.only = set_class(self.only).intersection(original)
                    if self.exclude:
                        original = _schema.exclude
                        _schema.exclude = set_class(self.exclude).union(original)
                    _schema._init_fields()
                    _schema._visited = self.root._visited
                    self._schema["from"][rdf_type] = _schema
                    self._schema["to"][model] = _schema
                else:
                    if isinstance(nest, type) and issubclass(nest, SchemaABC):
                        schema_class = nest
                    elif not isinstance(nest, (str, bytes)):
                        raise ValueError("Nested fields must be passed a " "Schema, not {}.".format(nest.__class__))
                    elif nest == "self":
                        ret = self
                        while not isinstance(ret, SchemaABC):
                            ret = ret.parent
                        schema_class = ret.__class__
                    else:
                        schema_class = class_registry.get_class(nest)

                    rdf_type = str(normalize_type(schema_class.opts.rdf_type))
                    model = schema_class.opts.model
                    if not rdf_type or not model:
                        raise ValueError("Both rdf_type and model need to be set on the schema for nested to work")

                    self._schema["from"][rdf_type] = schema_class(
                        many=False,
                        only=self.only,
                        exclude=self.exclude,
                        context=context,
                        load_only=self._nested_normalized_option("load_only"),
                        dump_only=self._nested_normalized_option("dump_only"),
                        lazy=self.root.lazy,
                        flattened=self.root.flattened,
                        _visited=self.root._visited,
                        _top_level=False,
                    )
                    self._schema["to"][model] = self._schema["from"][rdf_type]
        return self._schema

    def _serialize_single_obj(self, obj, **kwargs):
        """Deserializes a single (possibly flattened) object."""
        if type(obj) not in self.schema["to"]:
            ValueError("Type {} not found in field {}.{}".format(type(obj), type(self.parent), self.name))

        schema = self.schema["to"][type(obj)]
        schema._top_level = False
        return schema.dump(obj)

    def _serialize(self, nested_obj, attr, obj, many=False, **kwargs):
        """Deserialize a nested field with one or many values."""
        if nested_obj is None:
            return None
        many = self.many or many
        if many:
            result = []
            for obj in nested_obj:
                result.append(self._serialize_single_obj(obj, **kwargs))
            return result
        else:
            if utils.is_collection(nested_obj):
                raise ValueError("Expected single value for field {} but got a collection".format(self.name))

            return self._serialize_single_obj(nested_obj, **kwargs)

    def _test_collection(self, value, many=False):
        return  # getting a non list for a list field is valid in jsonld

    def load_single_entry(self, value, partial):
        """Loads a single nested entry from its schema."""
        type_ = normalize_type(value["@type"])

        schema = self.schema["from"][str(type_)]

        if not schema:
            ValueError("Type {} not found in {}.{}".format(value["@type"], type(self.parent), self.data_key))

        if schema.lazy:
            return lazy_object_proxy.Proxy(lambda: schema.load(value, unknown=self.unknown, partial=partial))
        if not schema._all_objects and self.root._all_objects:
            schema._all_objects = self.root._all_objects
        schema._reversed_properties = self.root._reversed_properties
        return schema.load(value, unknown=self.unknown, partial=partial)

    def _load(self, value, data, partial=None, many=False):
        many = self.many or many

        try:
            if many:
                if not utils.is_collection(value):
                    value = [value]
                valid_data = []
                for val in value:
                    valid_data.append(self.load_single_entry(val, partial))
            else:
                if utils.is_collection(value):
                    # single values can be single element lists in jsonld
                    if len(value) > 1:
                        raise ValueError(
                            "Got multiple values for nested field {name} but many is not set.".format(name=self.name)
                        )
                    else:
                        value = value[0]

                valid_data = self.load_single_entry(value, partial)

        except ValidationError as error:
            raise ValidationError(error.messages, valid_data=error.valid_data) from error
        return valid_data

    def _dereference_single_id(self, value, attr, **kwargs):
        """Dereference a single id."""
        data = kwargs["_all_objects"].get(value, None)
        if not data:
            raise ValueError("Couldn't dereference id {id}".format(id=value))

        try:
            data = dict(data)
        except (TypeError, ValueError):
            raise ValueError(f"Couldn't convert value '{data}' to dictionary.")

        if self.reverse:
            # we need to remove the property from the child when handling reverse nesting
            del data[attr]

        return data

    def _dereference_flattened(self, value, attr, **kwargs):
        """Dereference an id or a list of ids."""
        if isinstance(value, list) or isinstance(value, types.GeneratorType):
            return [self._dereference_flattened(i, attr, **kwargs) for i in value]
        if isinstance(value, str):
            return self._dereference_single_id(value, attr, **kwargs)
        elif isinstance(value, dict):
            if len(value.keys()) == 1 and "@id" in value:
                return self._dereference_single_id(value["@id"], attr, **kwargs)
            else:
                return value
        else:
            raise ValueError("Nested field needs to be a dict or an id entry/list, got {value}".format(value=value))

    def _deserialize(self, value, attr, data, **kwargs):
        """Deserialize nested object."""

        if kwargs.get("flattened", False):
            # could be id references, dereference them to continue deserialization
            value = self._dereference_flattened(value, attr, **kwargs)

        return super()._deserialize(value, attr, data, **kwargs)

    def _reversed_fields(self):
        """Get fields that are reversed in type hierarchy."""
        fields = {}

        if self.reverse:
            fields = {self.data_key: {type(s) for s in self.schema["from"].values()}}

        for schema in self.schema["from"].values():
            for k, v in schema._reversed_properties.items():
                if k not in fields:
                    fields[k] = set()
                fields[k].update(v)

        return fields


class List(_JsonLDField, fields.List):
    """A potentially ordered list using the ``@list`` keyword.

    Args:
        ordered (bool): Whether this is an ordered (via ``@list`` keyword) list.

    Warning: The JSON-LD flattening algorithm does not combine ``@list`` entries when merging nodes.
    So if you use ``ordered=True`` and flatten the output, and you have the node containing the list
    in multiple places in the graph, the node will get merged but its lists wont get merged (you get a list of lists
    instead), which means that the output can't be deserialized back to python objects."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ordered = kwargs.get("ordered", False)

    def _serialize(self, value, attr, obj, **kwargs):
        value = super()._serialize(value, attr, obj, **kwargs)
        return {"@list": value} if self.ordered else value

    def _deserialize(self, value, attr, data, **kwargs) -> typing.List[typing.Any]:
        if isinstance(value, dict):  # an ordered list
            value = value["@list"]
        return super(_JsonLDField, self)._deserialize(value, attr, data, **kwargs)

    @property
    def opts(self):
        """Return parent's opts."""
        return self.parent.opts

    def _reversed_fields(self):
        """Get fields that are reversed in type hierarchy."""
        return self.inner._reversed_fields()
