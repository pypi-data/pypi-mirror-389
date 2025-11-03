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

import protoform.data as datalib
import protoform.graph as graphlib

from protoform.modules.common import *
from protoform.modules.operator.common import Operator

logger = logging.getLogger(__name__)

class PivotTable(Operator):
    """Operator for creating pivot tables from existing data tables.
    
    This operator transforms a table by pivoting specified columns, grouping by
    index columns, and aggregating values using a specified aggregation function.
    The result is stored as a new table in the graph.
    """

    def do_work(self, task_info, execution_context):
        """Performs the pivot table operation on the specified table.
        
        Args:
            task_info (dict): Task configuration containing:
                - table (str): Name of the source table to pivot
                - group_by (str): Columns to use as row indices
                - pivot_column (str): Columns to pivot (become new columns)
                - value_column (str): Columns containing values to aggregate
                - agg_function (str): Aggregation function to apply (e.g., 'sum', 'mean'). Full list is here https://docs.getdaft.io/en/stable/api/aggregations/
                - output_table_name (str): Name for the resulting pivot table
            execution_context (dict): Execution context containing:
                - graph: The data graph containing all tables
                
        Returns:
            bool: True if the operation completed successfully
            
        Raises:
            KeyError: If required task_info parameters are missing
            ValueError: If the specified table doesn't exist in the graph
        """

        # Access context
        graph = execution_context["graph"]
        table_name = task_info["table"]
        group_by = task_info["group by"]
        pivot_column = task_info["pivot column"]
        value_column = task_info["value column"]
        agg_function = task_info["agg function"]
        output_table_name = task_info["output table name"]
        node = graphlib.get_node(graph, table_name)
        df = datalib.get_node_data(node)

        output_df = df.pivot(
            group_by=group_by,
            pivot_col=pivot_column,
            value_col=value_column,
            agg_fn=agg_function,
            names=None,
        )
        output_table_description = {
            'columns': {col.name():{} for col in output_df.columns},
            'data format': 'csv' # TODO: data format should be applicable in the data manifest only. The WriteDataset operator should be able to handle this.
        }

        pivot_node = graphlib.add_node(graph, output_table_name, output_table_description)
        datalib.set_node_data(pivot_node, output_df)

        return True