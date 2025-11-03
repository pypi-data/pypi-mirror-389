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

from typing import List, Literal, Optional, Union

import protoform.data as datalib
import protoform.graph as graphlib

from protoform.modules.common import *
from protoform.modules.operator.common import Operator, OperatorBaseTaskInfo


class UnPivotTableTaskInfo(OperatorBaseTaskInfo):
    operator: Literal["unpivot table"]
    operator_type: Literal["builtin"]
    table: str
    ids: Union[str, List[str]]
    values: Optional[List[str]]
    variable_name: Optional[str]
    value_name: Optional[str]
    output_table_name: str


class UnPivotTable(Operator):
    """Operator for creating pivot tables from existing data tables.

    This operator transforms a table by pivoting specified columns, grouping by
    index columns, and aggregating values using a specified aggregation function.
    The result is stored as a new table in the graph.
    """

    def do_work(self, task_info, execution_context):
        """Performs the pivot table operation on the specified table.

        Args:
            task_info (dict): Task configuration containing:
                - ids (str or list): Columns to keep as identifiers  required
                - values (list): Optional Columns to unpivot. If not specified, all columns except ids will be unpivoted. []
                - variable_name (str): Optional Name of the variable column. Defaults to "variable".
                - value_name (str):  Optional Name of the value column. Defaults to "value".  'value'
            execution_context (dict): Execution context containing:
                - graph: The data graph containing all tables

        Returns:
            bool: True if the operation completed successfully

        Raises:
            KeyError: If required task_info parameters are missing
            ValueError: If the specified table doesn't exist in the graph
        """
        
        # Validate input data
        parsed = UnPivotTableTaskInfo.model_validate(task_info)
        # Access context
        graph = execution_context["graph"]
        table_name = parsed.table
        ids = parsed.ids
        values = parsed.values
        variable_name = parsed.variable_name
        value_name = parsed.value_name
        output_table_name = parsed.output_table_name
        node = graphlib.get_node(graph, table_name)
        df = datalib.get_node_data(node)

        output_df = df.unpivot(
            ids, values, variable_name=variable_name, value_name=value_name
        )
        output_table_description = {
            "columns": {col.name(): {} for col in output_df.columns},
            "data format": "csv",  # TODO: data format should be applicable in the data manifest only. The WriteDataset operator should be able to handle this.
        }

        unpivot_node = graphlib.add_node(
            graph, output_table_name, output_table_description
        )
        datalib.set_node_data(unpivot_node, output_df)

        return True
