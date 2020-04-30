import marshmallow.fields as fields
import logging

logger = logging.getLogger("calamus")


class FieldName(object):
    def __init__(self, namespace, name):
        self.namespace = namespace
        self.name = name

    def __str__(self):
        return "{namespace}{name}".format(namespace=self.namespace, name=self.name)


class Namespace(object):
    def __init__(self, namespace):
        self.namespace = namespace

    def __getattr__(self, name):
        return FieldName(self, name)

    def __str__(self):
        return self.namespace


class _JsonLDField(fields.Field):
    def __init__(self, field_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_name = field_name

    @property
    def data_key(self):
        """Return the (expanded) JsonLD field name."""
        return str(self.field_name)

    @data_key.setter
    def data_key(self, value):
        pass


class Id(fields.String):
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Float(_JsonLDField, fields.Float):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Date(_JsonLDField, fields.DateTime):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Nested(_JsonLDField, fields.Nested):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class List(_JsonLDField, fields.List):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
