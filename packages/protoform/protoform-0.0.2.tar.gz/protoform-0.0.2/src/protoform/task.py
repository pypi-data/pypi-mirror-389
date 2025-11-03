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
import logging
import multiprocessing
import time


import protoform.graph as graphlib

logger = logging.getLogger(__name__)

class TaskPlanExecutor(object):


    def __init__(self, task_plan):
        self._task_plan = task_plan
        self._early_exit = False
        self._lock = multiprocessing.RLock()
        self._execution_context = {}
        return


    def execute(self):

        graph = self._task_plan
        
        nodes_dependencies = {}
        for node_idx in graph.node_indexes():
            node = graph[node_idx]
            predecessors = graph.predecessors(node_idx)
            nodes_dependencies[node] = predecessors
        self._nodes_dependencies = nodes_dependencies

        while True:
            self.submit_ready_nodes()

            if self.has_completed_execution():
                break

            if  self._early_exit:
                break

            time.sleep(0.01)
            pass
        
        return


    def has_completed_execution(self):
        completed = False
        with self._lock:
            nodes_dependencies = self._nodes_dependencies
            if len(nodes_dependencies) == 0:
                completed = True
        return completed
            
    
    def submit_ready_nodes(self):

        logger.debug("submit_ready_nodes function acquiring lock")

        with self._lock:
            nodes_to_execute = []
            nodes_dependencies = self._nodes_dependencies
            for node, node_dependencies in nodes_dependencies.items():
                if len(node_dependencies) == 0:
                    nodes_to_execute.append(node)
                pass

            for node_to_execute in nodes_to_execute:
                logger.debug(f"submitting node: {node_to_execute.get_name()}")
                self.submit_node(node_to_execute)
                logger.debug(f"submitted node: {node_to_execute.get_name()}")

        logger.debug("submit_ready_nodes no longer has lock")

        return


    def multiprocessing_cb():
        logger.debug("execution succeeded")


    def multiprocessing_error_cb(error):
        logger.debug("execution errored")
        self._early_exit = True
        raise error
        
        
    def submit_node(self, node):

        node_info = node.description

        operator = node_info['operator instance']

        operator.add_post_run_callback(functools.partial(self.on_execute_node_completed, node))

        execution_context = self._execution_context
        operator.run(node_info, execution_context)
        
        return

    
    def on_execute_node_completed(self, node):

        logger.debug(f"node has completed: {node.get_name()}")
        logger.debug("on_execute_node_completed acquiring lock")
        with self._lock:
            nodes_dependencies = self._nodes_dependencies
            del nodes_dependencies[node]

            graph = self._task_plan

            node_idx = graphlib.get_node_index(graph, node.get_name())
            for successor in graph.successors(node_idx):
                dependencies = nodes_dependencies[successor]
                dependencies.remove(node)
        logger.debug("on_execute_node_completed has released lock")
                
        return



def apply_task_plan_to_data(task_plan, data_graph, should_copy_graph=True):

    output_graph = data_graph
    if should_copy_graph is True:

        # TODO:
        # verify that the copy is what we expect
        
        # make a copy of the data graph
        output_graph = data_graph.copy()

        pass
    
    executor = TaskPlanExecutor(task_plan)
    execution_context = {
        'graph':output_graph
    }
    executor._execution_context = execution_context
    executor.execute()

    return output_graph

