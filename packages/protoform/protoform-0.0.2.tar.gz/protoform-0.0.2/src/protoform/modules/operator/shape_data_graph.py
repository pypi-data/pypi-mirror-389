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

import copy
import daft
import logging
import rustworkx as rx

import protoform.data as datalib
import protoform.graph as graphlib

from protoform.modules.common import *
from protoform.modules.operator.shape_graph import ShapeGraph
from protoform.utils import _daft_2_protoform_type, _protoform_2_daft_type

logger = logging.getLogger(__name__)

class ShapeDataGraph(ShapeGraph):

    # subclasses will override this
    def get_step_action_functions(self):
        functions = super().get_step_action_functions()
        functions['create table'] = self.create_table
        functions['select tables'] = self.select_tables
        functions['remove table'] = self.remove_table
        functions['rename table'] = self.rename_table
        functions['copy table'] = self.copy_table
        functions['add column'] = self.add_column
        functions['remove column'] = self.remove_column
        functions['rename column'] = self.rename_column
        functions['add row'] = self.add_row
        functions['remove row'] = self.remove_row
        functions['transpose table'] = self.transpose_table
        functions['select columns'] = self.select_columns
        return functions

    def create_table(self, graph, step_info):
        table_name = step_info['table']
        columns = step_info['columns']
        
        empty_table_as_dict = {x:[] for x in columns}
        df = daft.from_pydict(empty_table_as_dict)
        
        node_description = {
            'data':df
        }

        step_info['node'] = table_name
        step_info['description'] = node_description
        self.create_node(graph, step_info)
        return


    def select_tables(self, graph, step_info):
        table_names = step_info['tables']

        topo_order = rx.topological_sort(graph)
        node_names = [graph[x].get_name() for x in topo_order]
        
        for node_name in node_names:
            # keep any tables that are in the select list
            if node_name in table_names:
                continue
            step_info['node'] = node_name
            self.remove_node(graph, step_info)
        return

    def remove_table(self, graph, step_info):
        table_name = step_info['table']
        step_info['node'] = table_name
        self.remove_node(graph, step_info)
        return
    
        
    def rename_table(self, graph, step_info):
        table_name = step_info['table']
        new_table_name = step_info['new table name']

        step_info['node'] = table_name
        step_info['new node name'] = new_table_name
        self.rename_node(graph, step_info)
        return

    def copy_table(self, graph, step_info):
        """
        Copy a table from the graph to a new table.
        The new table will be an orphan node, meaning it will not have any edges.
        The new table will have the same data, description, and edges as the original table.
        # TODO: consider copying edges as well.
        """
        source_table_name = step_info['table']
        target_table_name = step_info['new table name']
        
        # Get the source node and its data
        source_node = graphlib.get_node(graph, source_table_name)
        source_df = datalib.get_node_data(source_node)
        
        # Create a copy of the dataframe
        copied_df = source_df.select(*source_df.column_names)
        
        # Create a deep copy of the node description, but not the data
        source_description = source_node.description
        target_description = {
            'columns': copy.deepcopy(source_description.get('columns', {})),
            'data format': source_description.get('data format', 'csv')
        }
        # Copy any other fields except 'data' 
        for key, value in source_description.items():
            if key not in ['columns', 'data format', 'data']:
                target_description[key] = copy.deepcopy(value)
        
        # Add the new node to the graph
        target_node = graphlib.add_node(graph, target_table_name, target_description)
        datalib.set_node_data(target_node, copied_df)
        return

    
    def add_column(self, graph, step_info):

        table_name = step_info['table']
        column_name = step_info['new column name']
        column_info = step_info.get('column info', {})

        node = graphlib.get_node(graph, table_name)
        df = datalib.get_node_data(node)

        # Get data type from column_info and create appropriate daft literal
        data_type = column_info.get("data type", "string")
        default_value = column_info.get("default value", None)
        
        new_column_daft_dtype = _protoform_2_daft_type(data_type, default = "string")
        default_literal = daft.lit(default_value).cast(new_column_daft_dtype)
        new_df = df.with_column(column_name, default_literal)
        
        datalib.set_node_data(node, new_df)

        # TODO:
        # if the following are specified, be sure to include it
        # - is identifier
        # - is hipaa identifier
        
        # update the info that we are tracking along with the df
        node_info = node.description
        columns_info = node_info['columns']
        columns_info[column_name] = column_info

        return
    
        
    def remove_column(self, graph, step_info):
        table_name = step_info['table']
        column_name = step_info['column']

        node = graphlib.get_node(graph, table_name)

        datalib.remove_column(node, column_name)
        return
    

    def rename_column(self, graph, step_info):
        table_name = step_info['table']
        column_name = step_info['column']
        new_column_name = step_info['new column name']
        
        node = graphlib.get_node(graph, table_name)
        df = datalib.get_node_data(node)

        new_df = df.with_column_renamed(column_name, new_column_name)
        
        datalib.set_node_data(node, new_df)
        node_info = node.description
        columns_info = node_info["columns"]
        columns_info[new_column_name] = columns_info[column_name]
        del columns_info[column_name]
        return

    
    def add_row(self, graph, step_info):
        raise NotImplementedError
    
    def remove_row(self, graph, step_info):
        raise NotImplementedError
    
    def transpose_table(self, graph, step_info):
        raise NotImplementedError
    
    def select_columns(self, graph, step_info):                
        table_name = step_info['table']
        columns = step_info['columns']
        column_info = step_info.get('column info', {})

        node = graphlib.get_node(graph, table_name)
        df = datalib.get_node_data(node)
        
        # Function that helps cast columns to specified types if specified in the column_info
        def process_col(col_name):
            c = daft.col(col_name)
            if col_name in column_info and "data type" in column_info[col_name]:
                # If the data type is not supported, default to string type
                c = c.cast(_protoform_2_daft_type(column_info[col_name]["data type"], "string"))
            return c
        columns = list(map(process_col, columns))
        
        # Select only the specified columns
        new_df = df.select(*columns)
        datalib.set_node_data(node, new_df)

        # Update columns_info to only include selected columns
        node_info = node.description
        selected_columns = {}
        for col in columns:
            current_col_name = col.name()
            current_col_info = node_info['columns'][current_col_name]

            # NOTE: Update data type in graph/node state as well
            # FIXME: We need a better way to change the state of the node when state of the daft dataframe also changes                   
            current_col_info["data type"] = _daft_2_protoform_type(new_df.schema()[current_col_name].dtype, daft.DataType.string())
            selected_columns[current_col_name] = current_col_info
        node_info['columns'] = selected_columns
    
    # END class ShapeDataGraph
    pass