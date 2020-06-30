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
"""Tests for Json-LD schema."""

import calamus.fields as fields
from calamus.schema import JsonLDSchema


def test_schema_hierarchy():
    class Entity:
        def __init__(self, _id):
            self._id = _id

    class CreativeWork(Entity):
        pass

    class Dataset(CreativeWork):
        pass

    prov = fields.Namespace("http://www.w3.org/ns/prov#")
    schema = fields.Namespace("http://schema.org/")

    class EntitySchema(JsonLDSchema):
        _id = fields.Id()

        class Meta:
            rdf_type = [prov.Entity, prov.Location]
            model = Entity

    class CreativeWorkSchema(EntitySchema):
        class Meta:
            rdf_type = schema.CreativeWork
            model = CreativeWork

    class DatasetSchema(CreativeWorkSchema):
        class Meta:
            rdf_type = schema.Dataset
            model = Dataset

    assert EntitySchema.opts.rdf_type == sorted([prov.Entity, prov.Location])
    assert CreativeWorkSchema.opts.rdf_type == sorted([prov.Entity, prov.Location, schema.CreativeWork])
    assert DatasetSchema.opts.rdf_type == sorted([prov.Entity, prov.Location, schema.CreativeWork, schema.Dataset])
