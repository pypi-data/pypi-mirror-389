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

import protoform.data as datalib
import protoform.graph as graphlib

from protoform.modules.common import *
from protoform.modules.operator.common import Operator

logger = logging.getLogger(__name__)

class NormalizeString(Operator):

    def do_work(self, task_info, execution_context):
        """Performs string replacement operation with regular expression on the specified table.
        
        Args:
            task_info (dict): Task configuration containing:
                - table (str): Name of the source table to normalize
                - column (str): Columns to use as row indices
                - normalization (dict): a dictionary of values to be replaced by keys
                - graph: The data graph containing all tables
                
        Returns:
            bool: True if the operation completed successfully
            
        Raises:
            KeyError: If required task_info parameters are missing
            ValueError: If the specified table doesn't exist in the graph
        """
        def normalize(column_data, normalizations):
            return column_data.apply(lambda x: normalizations[str(x)] if str(x) in normalizations.keys() else x, return_dtype = daft.DataType.string())

        # Access context
        graph = execution_context["graph"]
        table_name = task_info["table"]
        column = task_info["column"]
        node = graphlib.get_node(graph, table_name)
        df = datalib.get_node_data(node)
        df = df.with_column(column, normalize(df[column], task_info["normalizations"]))
        datalib.set_node_data(node, df)

        return True
