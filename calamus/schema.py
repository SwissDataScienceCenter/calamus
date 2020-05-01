from marshmallow.schema import Schema, SchemaMeta, SchemaOpts
from marshmallow.fields import Field
from marshmallow.utils import missing, is_collection, RAISE, set_value, EXCLUDE, INCLUDE
from marshmallow import post_load
from collections.abc import Mapping
from marshmallow.error_store import ErrorStore

from pyld import jsonld

import inspect

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

    def __init__(
        self,
        *args,
        only=None,
        exclude=(),
        many=False,
        context=None,
        load_only=(),
        dump_only=(),
        partial=False,
        unknown=None
    ):
        super().__init__(
            *args,
            only=only,
            exclude=exclude,
            many=many,
            context=context,
            load_only=load_only,
            dump_only=dump_only,
            partial=partial,
            unknown=unknown
        )

        if not self.opts.class_type or not self.opts.mapped_type:
            raise ValueError("class_type and mapped_type have to be set on the Meta of schema {}".format(type(self)))

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

    def _deserialize(
        self,
        data: typing.Union[typing.Mapping[str, typing.Any], typing.Iterable[typing.Mapping[str, typing.Any]],],
        *args,
        error_store: ErrorStore,
        many: bool = False,
        partial=False,
        unknown=RAISE,
        index=None
    ) -> typing.Union[_T, typing.List[_T]]:
        index_errors = self.opts.index_errors
        index = index if index_errors else None
        if many:
            if not is_collection(data):
                error_store.store_error([self.error_messages["type"]], index=index)
                ret = []  # type: typing.List[_T]
            else:
                ret = [
                    typing.cast(
                        _T,
                        self._deserialize(
                            typing.cast(typing.Mapping[str, typing.Any], d),
                            error_store=error_store,
                            many=False,
                            partial=partial,
                            unknown=unknown,
                            index=idx,
                        ),
                    )
                    for idx, d in enumerate(data)
                ]
            return ret
        ret = self.dict_class()
        # Check data is a dict
        if not isinstance(data, Mapping):
            error_store.store_error([self.error_messages["type"]], index=index)
        else:
            if data.get("@context", None):
                # we got compacted jsonld, expand it
                data = jsonld.expand(data)

            partial_is_collection = is_collection(partial)
            for attr_name, field_obj in self.load_fields.items():
                field_name = field_obj.data_key if field_obj.data_key is not None else attr_name

                if getattr(field_obj, "reverse", False):
                    raw_value = data.get("@reverse", missing)
                    if raw_value is not missing:
                        raw_value = raw_value.get(field_name, missing)
                else:
                    raw_value = data.get(field_name, missing)

                if raw_value is missing:
                    # Ignore missing field if we're allowed to.
                    if partial is True or (partial_is_collection and attr_name in partial):
                        continue
                d_kwargs = {}
                # Allow partial loading of nested schemas.
                if partial_is_collection:
                    prefix = field_name + "."
                    len_prefix = len(prefix)
                    sub_partial = [f[len_prefix:] for f in partial if f.startswith(prefix)]
                    d_kwargs["partial"] = sub_partial
                else:
                    d_kwargs["partial"] = partial
                getter = lambda val: field_obj.deserialize(val, field_name, data, **d_kwargs)
                value = self._call_and_store(
                    getter_func=getter, data=raw_value, field_name=field_name, error_store=error_store, index=index,
                )
                if value is not missing:
                    key = field_obj.attribute or attr_name
                    set_value(typing.cast(typing.Dict, ret), key, value)
            if unknown != EXCLUDE:
                fields = {
                    field_obj.data_key if field_obj.data_key is not None else field_name
                    for field_name, field_obj in self.load_fields.items()
                }
                for key in set(data) - fields:
                    if key in ["@type", "@reverse"]:
                        # ignore JsonLD meta fields
                        continue

                    value = data[key]
                    if unknown == INCLUDE:
                        set_value(typing.cast(typing.Dict, ret), key, value)
                    elif unknown == RAISE:
                        error_store.store_error(
                            [self.error_messages["unknown"]], key, (index if index_errors else None),
                        )
        return ret

    @post_load
    def make_instance(self, data, **kwargs):
        const_args = inspect.signature(self.opts.mapped_type)
        keys = set(data.keys())
        args = []
        kwargs = {}
        has_kwargs = False
        for _, parameter in const_args.parameters.items():
            if parameter.kind in [inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.POSITIONAL_ONLY]:
                if parameter.name not in keys:
                    raise ValueError("Field {} not found in data {}".format(parameter.name, data))
                args.append(data[parameter.name])
                keys.remove(parameter.name)
            elif parameter.kind is inspect.Parameter.KEYWORD_ONLY:
                if parameter.name in keys:
                    kwargs[parameter.name] = data[parameter.name]
                    keys.remove(parameter.name)
            elif parameter.kind is inspect.Parameter.VAR_KEYWORD:
                has_kwargs = True
        missing_data = {k: v for k, v in data.items() if k in keys}
        if has_kwargs:
            instance = self.opts.mapped_type(*args, **kwargs, **missing_data)
        else:
            instance = self.opts.mapped_type(*args, **kwargs)

        unset_data = {}
        for key, value in missing_data.items():
            if hasattr(instance, key) and not getattr(instance, key):
                setattr(instance, key, value)
            else:
                unset_data[key] = value

        if unset_data:
            raise ValueError(
                "The following fields were not found on class {}:\n\t{}".format(
                    self.opts.mapped_type, "\n\t".join(unset_data.keys())
                )
            )

        return instance
