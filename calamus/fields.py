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
"""Marshmallow fields for use with Json-LD."""

import marshmallow.fields as fields
from marshmallow.base import SchemaABC
from marshmallow import class_registry, utils
from marshmallow.exceptions import ValidationError
import logging
import copy

import typing

logger = logging.getLogger("calamus")


class IRI(object):
    """ Represent an IRI in a namespace."""

    def __init__(self, namespace, name):
        self.namespace = namespace
        self.name = name

    def __str__(self):
        return "{namespace}{name}".format(namespace=self.namespace, name=self.name)


class Namespace(object):
    """Represents a namespace/ontology."""

    def __init__(self, namespace):
        self.namespace = namespace

    def __getattr__(self, name):
        return IRI(self, name)

    def __str__(self):
        return self.namespace


class _JsonLDField(fields.Field):
    """Internal class that enables marshmallow fields to be serialized with a JsonLD field name."""

    def __init__(self, field_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_name = field_name

        self.reverse = kwargs.get("reverse", False)

    @property
    def data_key(self):
        """Return the (expanded) JsonLD field name."""
        return str(self.field_name)

    @data_key.setter
    def data_key(self, value):
        pass


class Id(fields.String):
    """A node identifier."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def data_key(self):
        """Return the (expanded) JsonLD field name."""
        return "@id"

    @data_key.setter
    def data_key(self, value):
        pass


class String(_JsonLDField, fields.String):
    """A string field."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        value = super()._serialize(value, attr, obj, **kwargs)
        if self.parent.opts.add_value_types:
            value = {"@value": value, "@type": "http://www.w3.org/2001/XMLSchema#string"}
        return value

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, dict):
            value = value["@value"]
        return super()._deserialize(value, attr, data, **kwargs)


class Integer(_JsonLDField, fields.Integer):
    """An integer field."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        value = super()._serialize(value, attr, obj, **kwargs)
        if self.parent.opts.add_value_types:
            value = {"@value": value, "@type": "http://www.w3.org/2001/XMLSchema#integer"}
        return value

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, dict):
            value = value["@value"]
        return super()._deserialize(value, attr, data, **kwargs)


class Float(_JsonLDField, fields.Float):
    """A float field."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        value = super()._serialize(value, attr, obj, **kwargs)
        if self.parent.opts.add_value_types:
            value = {"@value": value, "@type": "http://www.w3.org/2001/XMLSchema#float"}
        return value

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, dict):
            value = value["@value"]
        return super()._deserialize(value, attr, data, **kwargs)


class DateTime(_JsonLDField, fields.DateTime):
    """A date/time field."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        value = super()._serialize(value, attr, obj, **kwargs)
        if self.parent.opts.add_value_types:
            value = {"@value": value, "@type": "http://www.w3.org/2001/XMLSchema#dateTime"}
        return value

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, dict):
            value = value["@value"]
        return super()._deserialize(value, attr, data, **kwargs)


class Nested(_JsonLDField, fields.Nested):
    """A reference to one or more nested classes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not isinstance(self.nested, list):
            self.nested = [self.nested]

    @property
    def schema(self):
        """The nested Schema object. """
        if not self._schema:
            # Inherit context from parent.
            context = getattr(self.parent, "context", {})
            self._schema = {"from": {}, "to": {}}
            for nest in self.nested:
                if isinstance(nest, SchemaABC):
                    rdf_type = str(nest.opts.rdf_type)
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

                    rdf_type = str(schema_class.opts.rdf_type)
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
                    )
                    self._schema["to"][model] = self._schema["from"][rdf_type]
        return self._schema

    def _serialize(self, nested_obj, attr, obj, many=False, **kwargs):
        # Load up the schema first. This allows a RegistryError to be raised
        # if an invalid schema name was passed
        if nested_obj is None:
            return None
        many = self.many or many
        if many:
            result = []
            for obj in nested_obj:
                if type(obj) not in self.schema["to"]:
                    ValueError("Type {} not found in field {}.{}".format(type(obj), type(self.parent), self.name))
                schema = self.schema["to"][type(obj)]
                result.append(schema.dump(obj))
            return result
        else:
            if utils.is_collection(nested_obj):
                raise ValueError("Expected single value for field {} but got a collection".format(self.name))
            if type(nested_obj) not in self.schema["to"]:
                ValueError("Type {} not found in field {}.{}".format(type(nested_obj), type(self.parent), self.name))
            schema = self.schema["to"][type(nested_obj)]
            return schema.dump(nested_obj)

    def _test_collection(self, value, many=False):
        many = self.many or many
        if many and not utils.is_collection(value):
            raise self.make_error("type", input=value, type=value.__class__.__name__)

    def _load(self, value, data, partial=None, many=False):
        many = self.many or many

        try:
            if many:
                valid_data = []
                for val in value:
                    schema = self.schema["from"][val["@type"]]
                    if not schema:
                        ValueError("Type {} not found in {}.{}".format(val["@type"], type(self.parent), self.data_key))
                    valid_data.append(schema.load(val, unknown=self.unknown, partial=partial))
            else:
                schema = self.schema["from"][value["@type"]]
                if not schema:
                    ValueError("Type {} not found in {}.{}".format(value["@type"], type(self.parent), self.data_key))
                valid_data = schema.load(value, unknown=self.unknown, partial=partial)
        except ValidationError as error:
            raise ValidationError(error.messages, valid_data=error.valid_data) from error
        return valid_data


class List(_JsonLDField, fields.List):
    """An ordered list using the ``@list`` keyword."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        value = super()._serialize(value, attr, obj, **kwargs)
        return {"@list": value}

    def _deserialize(self, value, attr, data, **kwargs) -> typing.List[typing.Any]:
        return super()._deserialize(value["@list"], attr, data, **kwargs)
