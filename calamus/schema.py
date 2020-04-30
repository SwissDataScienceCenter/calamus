from marshmallow.schema import Schema, SchemaMeta, SchemaOpts
from marshmallow.fields import Field

import typing

_T = typing.TypeVar("_T")


class JsonLDSchemaOpts(SchemaOpts):
    """ """

    def __init__(self, meta, *args, **kwargs):
        super().__init__(meta, *args, **kwargs)
        self.class_type = getattr(meta, "class_type", None)
        self.add_value_types = getattr(meta, "add_value_types", False)


class JsonLDSchema(Schema):
    """ """

    OPTIONS_CLASS = JsonLDSchemaOpts

    def _serialize(self, obj: typing.Union[_T, typing.Iterable[_T]], *, many: bool = False):
        """Serialize ``obj`` to jsonld."""
        ret = super()._serialize(obj, many=many)

        # add type
        class_type = self.opts.class_type

        if not class_type:
            raise ValueError("No class type specified for schema")

        if isinstance(class_type, list):
            ret["@type"] = [str(t) for t in class_type]
        else:
            ret["@type"] = str(class_type)

        return ret
