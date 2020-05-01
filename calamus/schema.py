from marshmallow.schema import Schema, SchemaMeta, SchemaOpts
from marshmallow.fields import Field
from marshmallow.utils import missing

import typing

_T = typing.TypeVar("_T")


class JsonLDSchemaOpts(SchemaOpts):
    """Options class for `JsonLDSchema`.
    Adds the following options:
    - ``class_type``: The RDF type(s) for this schema.
    - ``mapped_type``: The python type this schema (de-)serializes.
    - ``add_value_types``: Whether to add ``@type`` information to scalar field values.
    """

    def __init__(self, meta, *args, **kwargs):
        super().__init__(meta, *args, **kwargs)
        self.class_type = getattr(meta, "class_type", None)
        self.mapped_type = getattr(meta, "mapped_type", None)
        self.add_value_types = getattr(meta, "add_value_types", False)


class JsonLDSchema(Schema):
    """Schema for a JsonLD class.
    Example: ::
        from calamus import JsonLDSchema
        import calamus.fields as fields
        from mymodels import User
        schema = fields.Namespace("http://schema.org/")
        class UserSchema(JsonLDSchema):
            class Meta:
                class_type = schema.Person
                mapped_type = User
            _id = fields.Id()
            birth_date = fields.Date(schema.birthDate)
            name = fields.String(schema.name)
    """

    OPTIONS_CLASS = JsonLDSchemaOpts

    def _serialize(self, obj: typing.Union[_T, typing.Iterable[_T]], *, many: bool = False):
        """Serialize ``obj`` to jsonld."""
        if many and obj is not None:
            return [self._serialize(d, many=False) for d in typing.cast(typing.Iterable[_T], obj)]
        ret = self.dict_class()
        for attr_name, field_obj in self.dump_fields.items():
            value = field_obj.serialize(attr_name, obj, accessor=self.get_attribute)
            if value is missing:
                continue
            key = field_obj.data_key if field_obj.data_key is not None else attr_name
            reverse = getattr(field_obj, "reverse", False)
            if reverse:
                if "@reverse" not in ret:
                    ret["@reverse"] = self.dict_class()
                ret["@reverse"][key] = value
            else:
                ret[key] = value

        # add type
        class_type = self.opts.class_type

        if not class_type:
            raise ValueError("No class type specified for schema")

        if isinstance(class_type, list):
            ret["@type"] = [str(t) for t in class_type]
        else:
            ret["@type"] = str(class_type)

        return ret
