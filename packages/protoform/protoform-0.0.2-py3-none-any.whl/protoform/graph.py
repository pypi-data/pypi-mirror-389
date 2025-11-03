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

import rustworkx as rx

from typing import List

class Node:
    """
    rustworkx does not actually implement a class for nodes
    so we implement this class for the objects to be set as the data payload
    that the rustworx graph stores
    """
    def __init__(self, graph, name, description):
        self.graph = graph
        self.description = description
        self.runtime_info = {}
        self.set_name(name)
        return

    def set_name(self, name):
        self.description["name"] = name
        return
    
    def get_name(self):
        return self.description["name"]
    
    pass


class Edge:
    """
    rustworkx does not actually implement a class for nodes
    so we implement this class for the objects to be set as the data payload
    that the rustworx graph stores
    """
    def __init__(self, graph, source, target, description):
        self.graph = graph
        self.source = source
        self.target = target
        self.description = description
        self.runtime_info = {}
        return
    
    pass


def create_graph():

    attrs = {
        "description":{},
        # store a dictionary for faster node query: key-value as node_name-node_index
        'node_name_idx': {},
    }
    graph = rx.PyDiGraph(attrs=attrs)
    
    return graph

def transfer_graph_attrs(src_graph, dest_graph):
    dest_graph.attrs = {}

    # TODO: implement deepcopy for description (copy.deepcopy() is not working with daft)
    dest_graph.attrs['description'] = src_graph.attrs['description']
    
    dest_graph.attrs['node_name_idx'] = {}
    for idx in dest_graph.node_indices():
        node_name = dest_graph[idx].get_name()
        dest_graph.attrs['node_name_idx'][node_name] = idx

    return

def add_node(graph, name, description):

    if name in graph.attrs['node_name_idx']:
        raise ValueError(f"Node named {name} already existed")

    node = Node(graph, name, description)
    graph.attrs['node_name_idx'][name] = graph.add_node(node)

    if description.get('is root', False) is True:
        set_node_as_root(graph, name)
    
    return node


def remove_node(graph, name):

    node_obj = None
    node_idx = None
    for idx in graph.node_indices():
        node = graph[idx]
        if node.get_name() == name:
            node_obj = node
            node_idx = idx
            break

    if node_obj is None:
        raise ValueError(f"No node named {name} found")

    # if the node is root, we need to find a new root
    if node_is_root(graph, name):
        for successor in graph.successors(node_idx):
            set_node_as_root(graph, successor.get_name())
            break
    graph.remove_node(node_idx)
    graph.attrs['node_name_idx'].pop(name)
    return

    
def add_edge(graph, source, target, description):

    source_idx = get_node_index(graph, source)
    target_idx = get_node_index(graph, target)
    edge = Edge(graph, source, target, description)
    graph.add_edge(source_idx, target_idx, edge)
    
    return edge



def remove_edge(graph, source, target):

    source_idx = get_node_index(graph, source)
    target_idx = get_node_index(graph, target)

    graph.remove_edge(source_idx, target_idx)
    
    return


def rename_node(graph, name, new_name):
    if new_name in graph.attrs['node_name_idx']:
        raise ValueError(f"Node named {new_name} already existed")
    
    node = get_node(graph, name)
    graph.attrs['node_name_idx'][new_name] = graph.attrs['node_name_idx'].pop(name)
    node.set_name(new_name)
    
    return

    

def get_node(graph, name):
    
    for idx in graph.node_indices():
        node = graph[idx]
        if node.get_name() == name:
            return node
    
    raise ValueError(f"No node named {name} found")


def get_node_index(graph, name):
    for node_idx in graph.node_indexes():
        node = graph[node_idx]
        if node.get_name() == name:
            return node_idx

    raise ValueError(f"No node named {name} found")


def node_is_root(graph, name):
    return graph.attrs["description"].get("root", None) == name


def set_node_as_root(graph, name):
    graph.attrs["description"]["root"] = name
    return

    
def get_root_node(graph):
    
    root_node_name = graph.attrs["description"].get("root", None)
    if root_node_name is None:
        raise ValueError('This graph has no root node defined')
    return get_node(graph, root_node_name)
    

def lint(graph):

    if not rx.is_directed_acyclic_graph(graph):
        raise NotImplementedError('graph is not dag')
    
    return True

    
def filter_node_by_name(graph: rx.PyDiGraph, names: List[str]) -> rx.PyDiGraph:
    if not len(names):
        raise ValueError(f"Name list must not be empty")
    
    names = set(names)
    def filter_func(node):
        name = node.description["name"]
        if name in names:
            names.remove(name)
            return True
        return False
    
    # Filter the graph & get list of indices
    indices = graph.filter_nodes(filter_func)
    
    # If a name does not exist, the length of indices & names will mismatch
    if len(names):
        raise ValueError(f"These nodes do not exist in the graph {list(names)}")
    
    # the preserve_attrs will only shallow copy the attrs from the parent graph, so we need to manually deepcopy
    subgraph = graph.subgraph(indices, preserve_attrs = False)
    transfer_graph_attrs(graph, subgraph)
    return subgraph