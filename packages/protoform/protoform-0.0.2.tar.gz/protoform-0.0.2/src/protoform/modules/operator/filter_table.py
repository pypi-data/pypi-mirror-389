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

import protoform.data as datalib
import protoform.graph as graphlib

from protoform.modules.common import *
from protoform.modules.operator.common import Operator

class FilterTable(Operator):

    def do_work(self, task_info, execution_context):
        graph = execution_context['graph']

        table_name = task_info['table']
        filter_string = task_info['filter']
        
        node = graphlib.get_node(graph, table_name)
        df = datalib.get_node_data(node)
        df = df.where(filter_string)

        datalib.set_node_data(node, df)
        
        return True

    # END class FilterTable
    pass
