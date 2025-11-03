#   Copyright 2025 DataXight, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import functools
import importlib
import json as jsonlib
import logging
import pathlib
import uritools
import rustworkx as rx

from protoform.modules.common import *
import protoform.graph as graphlib
from protoform.modules.operator.write_dataset import WriteDatasetTaskInfo as GraphOutputInfo
from typing import Any, Optional

from protoform.modules.io.node import Writer, Reader
from protoform.modules.io.sink import CsvDataNodeWriter, ManifoldNodeWriter, ParquetDataNodeWriter, SqlDataNodeWriter, SnowflakeSqlDataNodeWriter
from protoform.modules.io.source import CsvDataNodeReader, ParquetDataNodeReader, SqlDataNodeReader

from protoform.utils import _dict_hash

logger = logging.getLogger(__name__)


class ReaderFactory:
    @staticmethod
    def get_manifest_node_data_reader(node):

        node_info = node.description
        data_format = node_info["data format"]

        node_writer = None
        if data_format in [TYPE_CSV, TYPE_TSV]:
            # NOTE:
            # at the moment daft supports only commas as the separator
            node_writer = CsvDataNodeReader(node)
        elif data_format == TYPE_PARQUET:
            node_writer = ParquetDataNodeReader(node)
        elif data_format == TYPE_SQL:
            node_writer = SqlDataNodeReader(node)
        else:
            raise NotImplementedError(f"Writer for data {data_format} not implemented")

        return node_writer

    # END class ReaderFactory
    pass


class WriterFactory:

    @staticmethod
    def get_manifest_node_data_writer(node, data_format = None, configs = None, writer_data = None):

        node_info = node.description

        # If data format not provided, use the original format of the node
        if not data_format:
            data_format = node_info["data format"]
        
        node_writer = None
        if data_format in [TYPE_CSV, TYPE_TSV]:
            # NOTE:
            # at the moment daft supports only commas as the separator
            node_writer = CsvDataNodeWriter(node, data_format)
        elif data_format == TYPE_PARQUET:
            node_writer = ParquetDataNodeWriter(node)
        elif data_format == TYPE_SQL:
            node_writer = SqlDataNodeWriter(node, configs)
        elif data_format == TYPE_MANIFOLD:
            node_writer = ManifoldNodeWriter(node, writer_data)
        elif data_format == DB_SNOWFLAKE:
            node_writer = SnowflakeSqlDataNodeWriter(node, writer_data)
        else:
            raise NotImplementedError(f"Writer for data {data_format} not implemented")

        return node_writer

    pass


class GraphWriter(Writer):

    def __init__(self, graph_output_info: GraphOutputInfo):
        self._graph_output_info: GraphOutputInfo = graph_output_info
        self._output_type = self._graph_output_info.output_type
        self._output_manifest_url = self._graph_output_info.output_manifest_url
        
        self._output_data_url = self._graph_output_info.output_data_url
        # TODO: since we have introduced the writer_data, we should sync the output_source_config with the writer_data
        self._output_source_config = self._graph_output_info.output_source_config
        self._selected_output_table = self._graph_output_info.selected_output_table
        self._if_exists = self._graph_output_info.if_exists
        # any other writer data that is needed for the writer
        self._writer_data = self._graph_output_info.writer_data

    def generate_manifest(self, graph):
        """
        This function will generate graph structure into a manifest
        that can be written to disk.

        Any wrappers around the graph structure that is needed when written to disk
        (eg, for json, need to embed as the value for a key "tables" in a dict)
        is outside the scoe of this function
        """
        tables = {}
        configs = {}
        
        if (subgraph := graph) and len(self._graph_output_info.selected_output_table):
            subgraph = graphlib.filter_node_by_name(graph, self._graph_output_info.selected_output_table)

        # Generate table manifest
        output_config = self._graph_output_info.output_source_config
        for node in subgraph.nodes():
            logger.debug(f"writing node {node.get_name()}")

            # Use this to get the writer correspond to user's desired output type, e.g. sql, csv, parquet, etc
            node_writer = WriterFactory.get_manifest_node_data_writer(node, self._output_type, output_config, self._writer_data)
            table_info = node_writer.generate_info_for_manifest(self._output_data_url, is_parent_location=True)

            tables[node.get_name()] = table_info
            pass
        
        # Generate table config manifest
        if output_config is not None and isinstance(output_config, dict):
            ref = _dict_hash(output_config)
            configs[ref] = output_config

        # Embed the two manifest & return
        return {
            "tables": tables,
            "data source config": configs
        }

    def write_manifest(self, graph):
        output_path: str = self._output_manifest_url
        parts = uritools.urisplit(output_path)

        if parts.scheme is None:
            pathobj = pathlib.Path(output_path)
            pathobj.parent.mkdir(parents=True, exist_ok=True)
            
        graph_manifest = self.generate_manifest(graph)
        with open(output_path, "w") as f:
            jsonlib.dump(graph_manifest, f)

        return

    def write_data_for_graph(self, graph):
        node_data_type = graph.attrs["node data type"]

        if node_data_type not in ["tables"]:
            raise NotImplementedError
            
        # TODO: Filter the graph might result in some columns referencing a non-existing table. There
        # are three options to handle this:
        # Option 1: Remove the reference column in the manisfest if the reference table does not exist
        # Option 2: Raise an error saying that the user cannot select only 2 tables
        # Option 3: Have the operators tolerate the case where the reference table does not exist
        if (subgraph := graph) and len(self._graph_output_info.selected_output_table):
            subgraph = graphlib.filter_node_by_name(graph, self._graph_output_info.selected_output_table)
        for node in subgraph.nodes():
            self.write_data_for_node(node)
            pass

        return

    def write_data_for_node(self, node):
        node_writer = WriterFactory.get_manifest_node_data_writer(node, self._output_type, self._output_source_config, self._writer_data)
        location_url = self._graph_output_info.output_data_url
        
        # We render the env variables in case of sql when writing to data sink
        node_name = node.get_name()
        if type(node_writer) == SqlDataNodeWriter:
            data_url = node_writer.generate_data_url(location_url, render = True)  
            logger.debug(f"writing node {node_name} to {data_url}")
            node_writer.write(data_url, self._if_exists)
        elif type(node_writer) == SnowflakeSqlDataNodeWriter:
            data_url = node_writer.generate_data_url(location_url, render = True)  
            logger.debug(f"writing node {node_name} to {data_url}")
            node_writer.write(data_url, self._graph_output_info, self._if_exists)
        else:
            data_url = node_writer.generate_data_url(location_url, is_parent_location = True)
            logger.debug(f"writing node {node_name} to {data_url}")
            node_writer.write(data_url)

    # END class GraphWriter
    pass

class GraphReader(Reader):
    # this loads the file that describes the graph
    def load_from_file(self, filename):
        with open(filename) as f:
            graph = self.load_from_stream(f)

        return graph

    # this loads the file that describes the graph
    def load_from_stream(self, filehandle):
        try:
            json = jsonlib.load(filehandle)
        except Exception:
            logger.exception("Error loading graph from stream")
            raise

        return self.parse_graph_info(json)

    # this loads the data associated with the graph
    def load_data_for_graph(self, graph):

        # sort the nodes first
        # because we need to process nodes in order
        # if one depends on another
        # eg for defining the column schema
        for node_id in rx.topological_sort(graph):
            node = graph[node_id]
            self.load_data_for_node(node)
        return


    def load_data_for_node(self, node):
        node.runtime_info["load data function"]()

    def parse_graph_info(self, json):
        graph = graphlib.create_graph()
        graph.attrs["description"] = json

        return graph

    # END class GraphReader
    pass


class ColumnMustBeUniqueKey(Exception):
    def __init__(self, column_name):
        super().__init__(f"column {column_name} needs to be defined to form a unique key")


class ManifestReader(GraphReader):
    @staticmethod
    def load_node_data(node):
        node_reader = ReaderFactory.get_manifest_node_data_reader(node)
        df = node_reader.read()

        node_info = node.description
        node_info["data"] = df
        return


    def parse_graph_info(self, json):
        graph: rx.PyDiGraph = super().parse_graph_info(json)
        tables_info: dict[str, Any] = json["tables"]
        tables_source_config: Optional[dict[str, Any]] = json.get("data source config")

        graph.attrs["node data type"] = "tables"

        # ----
        # first create the nodes
        # ----
        for table_name, table_info in tables_info.items():
            # Attach data source config to each table if config
            # exists
            config_ref: str = table_info.get("data source config ref")
            if config_ref and tables_source_config:
                source_config: dict[str, Any] =  tables_source_config[config_ref]
                table_info["data source config"] = source_config

            node = graphlib.add_node(graph, table_name, table_info)
            node.runtime_info["load data function"] = functools.partial(self.__class__.load_node_data, node)

            pass


        # -----
        # then create the edges
        # -----
        for table_name, table_info in tables_info.items():

            # we create an edge if the column schema
            # depends on another table
            # so that table needs to be loaded first
            if table_info.get("autogenerate column schema", False) is True:
                description = table_info["info to autogenerate column schema"]
                source = description["source"]
                primary_table, primary_column = source.split(".")
                graphlib.add_edge(graph, primary_table, table_name, description)
                continue


            columns_info = table_info["columns"]

            # handle the case that 2 or more columns are required
            # to uniquely identify a row in this table
            unique_key_info = table_info.get("unique key", None)
            if unique_key_info is not None:
                node = graphlib.get_node(graph, table_name)

                for column_name in unique_key_info:
                    if column_name not in columns_info:
                        raise ColumnMustBeUniqueKey(column_name)
                    pass

                pass

            for column_name, column_info in columns_info.items():
                # if a column has a "references" in the metadata
                # that means it's a foreign key
                reference = column_info.get("references")
                if reference is not None:
                    primary_table, primary_column = reference.split(".")

                    description = {
                        "primary table": primary_table,
                        "primary column": primary_column,
                        "foreign table": table_name,
                        "foreign column": column_name,
                    }

                    graphlib.add_edge(graph, primary_table, table_name, description)
                    pass

                pass

            pass


        return graph

    # END class ManifestReader
    pass


class TaskPlanReader(GraphReader):
    @staticmethod
    def load_node_data(node):
        import protoform.operator as oplib
        node_info = node.description
        operator_name = node_info["operator"]
        operator_type = node_info["operator type"]
        operator = None
        if operator_type == "dynamic":
            module_name, class_name = operator_name.rsplit(".", 1)
            theCls = getattr(importlib.import_module(module_name), class_name)
            operator = theCls()
        elif operator_type == "builtin":
            operator = oplib.MAP_OPERATORS[operator_name]()
        else:
            raise NotImplementedError(f"Operator type: {operator_type} is not supported. Change to dynamic or builtin")

        node_info["operator instance"] = operator
        return

    def parse_graph_info(self, json):
        graph = super().parse_graph_info(json)
        tasks_info = json["tasks"]
        graph.attrs["node data type"] = "tasks"

        # first create the nodes
        for task_name, task_info in tasks_info.items():
            node = graphlib.add_node(graph, task_name, task_info)
            node.runtime_info["load data function"] = functools.partial(self.__class__.load_node_data, node)
            pass

        # now process the edges
        for task_name, task_info in tasks_info.items():
            predecessors = task_info.get("predecessors", [])
            for predecessor in predecessors:
                graphlib.add_edge(graph, predecessor, task_name, {})

        return graph

    # END class TaskPlanReader
    pass
