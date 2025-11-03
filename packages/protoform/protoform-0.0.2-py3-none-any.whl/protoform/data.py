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

import logging

import daft

import protoform.graph as graphlib




def get_node_data(node):
    return node.description["data"]


def set_node_data(node, data):
    node.description["data"] = data
    return


def get_node_keys(node):
    """
    This function returns all of the keys of the node, which includes
    - primary key,
    - foreign key, which references a column in a different table,
    - unique key (defined via multiple columns), typically in lieu of primary key
    """
    node_info = node.description
    
    keys = {}

    # handle the case that 2 or more columns are required
    # to uniquely identify a row in this table
    unique_key_info = node_info.get('unique key', None)
    if unique_key_info is not None:
        keys["unique"] = unique_key_info

    columns_info = node_info['columns']
    primary_keys = []
    foreign_keys = []
    for column_name, column_info in columns_info.items():
        if column_info.get('is key') is not None:
            keys_to_append = primary_keys
            if column_info.get('references') is not None:
                keys_to_append = foreign_keys
            keys_to_append.append(column_name)
    keys['primary'] = primary_keys
    keys['foreign'] = foreign_keys
            
    return keys
    
    


def subset_graph_percentage(graph, percentage, seed=None):

    # get the root
    root_node = graphlib.get_root_node(graph)

    subset_node_data_percentage(root_node, percentage, seed=seed)
    subset_successors(graph, root_node, transitive=True)

    return


def subset_successors(graph, node, transitive=False):

    node_df = get_node_data(node)
    node_index = graphlib.get_node_index(graph, node.get_name())
    
    successors = graph.successors(node_index)
    for successor in successors:

        # need to get the edge that connects them
        successor_idx = graphlib.get_node_index(graph, successor.get_name())
        edge = graph.get_edge_data(node_index, successor_idx)

        # there's an assumption here that the key is a single column
        source_column = edge.description["primary column"]
        column_to_filter = edge.description["foreign column"]

        successor_df = get_node_data(successor)

        column_names = successor_df.column_names
        
        joined_df = successor_df.join(node_df,
                                      how="right",
                                      left_on=daft.col(column_to_filter),
                                      right_on=daft.col(source_column)).select(*column_names)
        set_node_data(successor, joined_df)

        continue
    
    # do this for the next set of successors
    if transitive:
        for processed in successors:
            subset_successors(graph, processed, transitive=True)
            pass
        pass
    
    return


def subset_node_data_percentage(node, percentage, seed=None):
    node_df = get_node_data(node)
    sampled_df = node_df.sample(percentage, seed=seed)
    
    set_node_data(node, sampled_df)
    return


def filter_node_data(node, column_to_filter, values_to_filter):
    
    node_df = get_node_data(node)
    
    filtered_df = node_df.filter(node_df[column_to_filter].is_in(values_to_filter))
    set_node_data(node, filtered_df)
    
    return
    
def remove_column(node, column_name):

    df = get_node_data(node)

    # TODO:
    # if this column is an edge
    # an exception needs to be raised
    # because the edge should be removed first
    new_df = df.exclude(column_name)
        
    set_node_data(node, new_df)

    # update the info that we are tracking along with the df
    node_info = node.description    
    columns_info = node_info['columns']
    del columns_info[column_name]
    return

