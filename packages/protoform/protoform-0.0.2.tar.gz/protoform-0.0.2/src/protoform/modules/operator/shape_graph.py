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

import protoform.graph as graphlib

from protoform.modules.common import *
from protoform.modules.operator.common import Operator

class ShapeGraph(Operator):
    def get_function_for_step_action(self, step_action):
        functions = self.get_step_action_functions()
        return functions[step_action]


    # subclasses will override this
    def get_step_action_functions(self):
        functions = {
            'create node':self.create_node,
            'remove node':self.remove_node,
            'rename node':self.rename_node,
            'add edge':self.add_edge,
            'remove edge':self.remove_edge
        }
        return functions

    
    def do_work(self, task_info, execution_context):

        graph = execution_context['graph']
        
        step_action_functions = self.get_step_action_functions()
        
        for step_info in task_info['steps']:

            step_action = step_info['action']
            step_action_function = step_action_functions[step_action]
            step_action_function(graph, step_info)
            pass

        return True

    
    def create_node(self, graph, step_info):
        node_name = step_info['node']
        description = step_info.get('description', {})
        graphlib.add_node(graph, node_name, description)


    def remove_node(self, graph, step_info):
        node_name = step_info['node']
        graphlib.remove_node(graph, node_name)
        return
    
    def rename_node(self, graph, step_info):
        node_name = step_info['node']
        new_node_name = step_info['new node name']
        graphlib.rename_node(graph, node_name, new_node_name)
        return

    def add_edge(self, graph, step_info):
        source_name = step_info['source']
        target_name = step_info['target']
        description = step_info['description']
        graphlib.add_edge(graph, source_name, target_name, description)
        return

    def remove_edge(self, graph, step_info):
        source_name = step_info['source']
        target_name = step_info['target']
        graphlib.remove_edge(graph, source_name, target_name)
        
    
    # END class ShapeGraph
    pass