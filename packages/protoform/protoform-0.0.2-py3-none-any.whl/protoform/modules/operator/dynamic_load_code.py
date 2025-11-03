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

import daft
import logging
import importlib
import sys

import protoform.data as datalib
import protoform.graph as graphlib

from protoform.modules.common import *
from protoform.modules.operator.common import Operator

logger = logging.getLogger(__name__)

class DynamicLoadCode(Operator):

    def do_work(self, task_info, execution_context):

        table_name = task_info['table']
        graph = execution_context['graph']
        
        node = graphlib.get_node(graph, table_name)

        df = datalib.get_node_data(node)

        df_function = self.get_transform_function(task_info)
        
        df = df_function(df)
    
        datalib.set_node_data(node, df)

        return True    

    def get_transform_function(self, task_info):

        load_method = task_info['load method']

        # TODO:
        # need a way for the end user to understand that this is an arbitrary transform
        # and so the tracking of column information may no longer apply
        df_function = None
        if load_method == 'parse text':
            code = task_info['code text']
            
            # exec the code string to create a function
            exec(code, globals())
            df_function = globals()[task_info.get('function name', 'transform_df')]
            pass
        elif load_method == 'parse file':
            module_url = task_info['module url']
            module_name = "protoform_dynamic_" + task_info['module name']
            df_function_name = task_info.get('function name', 'transform_df')

            dynamic_module = self.__class__.load_module(module_url, module_name)
            df_function = getattr(dynamic_module, df_function_name)
            pass
        elif load_method == 'import module':
            module_name = task_info['module name']
            df_function_name = task_info.get('function name', 'transform_df')

            module = importlib.import_module(module_name)
            df_function = getattr(module, df_function_name)
            pass
        else:
            raise NotImplementedError

        return df_function
    
    
    @staticmethod
    def load_module(module_url, module_name=None):
        """
        reads file at module_url and loads it as a module

        :param module_url: file to load
        :param module_name: name of module to register in sys.modules
        :return: loaded module
        """

        if module_name is None:
            raise ValueError("need the name of the module to load")

        spec = importlib.util.spec_from_file_location(module_name, module_url)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        return module


    # END class DynamicLoadCode
    pass
