# -*- coding: utf-8 -*-
#
# Copyright 2020- Swiss Data Science Center (SDSC)
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
"""Neo4J connection utils."""
import json
import requests

from urllib.parse import quote

import py2neo
from py2neo import Graph
from py2neo.database.work import ClientError

from . import CalamusDbBackend


class CalamusNeo4JBackend(CalamusDbBackend):
    """Neo4J backend for Calamus."""

    def __init__(self, auth={"user": "neo4j", "pass": "test"}, host="localhost", bolt_port=7687, http_port=7474):
        self.auth = auth
        self.bolt_url = f"bolt://{auth['user']}:{auth['pass']}@{host}:{bolt_port}"
        self.http_url = f"http://{auth['user']}:{auth['pass']}@{host}:{http_port}"

        self.graph = None

    def initialize(self):
        """Initialize the Neo4J graph."""
        # TODO: provide options for adding extra configs
        self.graph = Graph(self.bolt_url)
        try:
            # initialize the config
            self.graph.call.n10s.graphconfig.init({"handleVocabUris": "KEEP"})

            # set URI constraint
            res = self.graph.run(
                """
            CREATE CONSTRAINT n10s_unique_uri ON (r:Resource)
            ASSERT r.uri IS UNIQUE;
            """
            )
        # TODO: handle the client error in a more specific way
        except ClientError:
            pass

        ## Comment: seems like setting prefixes is maybe not something we'd want to do
        # initialize prefixes
        #     g.call.n10s.nsprefixes.add("prov", "http://www.w3.org/ns/prov#")
        #     g.call.n10s.nsprefixes.add("renku", "https://swissdatasciencecenter.github.io/renku-ontology#")
        #     g.call.n10s.nsprefixes.add("wfprov", "http://purl.org/wf4ever/wfprov#")
        return self.graph

    def commit(self, entity, schema):
        """Commit an object to Neo4J using the schema."""
        # TODO: use automatic schema retrieval
        # schema = _model_registry[entity.__class__]
        if not self.graph:
            raise RuntimeError("The graph must first be initialized.")

        res = self.graph.run(
            "call n10s.rdf.import.inline('{jsonld}', \"JSON-LD\")".format(jsonld=schema().dumps(entity))
        )
        return res

    def fetch_by_id(self, identifier):
        """Fetch an entity by id from Neo4J using the provided schema."""
        if not self.graph:
            raise RuntimeError("The graph must first be initialized.")

        # cypher = f"""
        # MATCH path=((n {{uri: "{identifier}"}}) -[*1..]-> ()) RETURN path
        # """

        cypher = f"""
        MATCH path=((n {{uri: "{identifier}"}}) -[*0..1]-> ()) RETURN path
        """

        payload = {"cypher": cypher, "format": "JSON-LD"}

        data = requests.post(
            f"{self.http_url}/rdf/neo4j/cypher", data=json.dumps(payload), auth=tuple(self.auth.values())
        ).json()

        # grab just the data we asked for - depending on the node, we might have a @graph or just
        # data for the single node
        if data and '@graph' in data:
            data = [x for x in data.get('@graph') if x.get('@id') == identifier].pop()

        return data
