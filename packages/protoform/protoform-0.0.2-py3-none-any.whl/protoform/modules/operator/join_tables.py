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
from protoform.utils import _daft_2_protoform_type

logger = logging.getLogger(__name__)

class JoinTables(Operator):

    def do_work(self, task_info, execution_context):

        graph = execution_context['graph']

        right_table = task_info['right table']
        left_table = task_info['left table']

        join_type = task_info['join type']
        right_join_columns = [daft.col(x) for x in task_info['right columns']]
        left_join_columns = [daft.col(x) for x in task_info['left columns']]
        
        right_node = graphlib.get_node(graph, right_table)
        left_node = graphlib.get_node(graph, left_table)

        right_df = datalib.get_node_data(right_node)
        left_df = datalib.get_node_data(left_node)

        # If joined columns have same name, the columns in left table will be kept
        # If joined columns have different name, all will be kept, but right columns will be prefixed
        # with right table name to avoid collision
        prefix = right_table + "."
        
        joined_df = left_df.join(right_df,
                                 left_on = left_join_columns,
                                 right_on = right_join_columns,
                                 how = join_type,
                                 prefix = prefix)
        
        # Embed columns
        joined_table_columns_info = {}
        joined_table_column_names = joined_df.column_names
        for column_name in joined_table_column_names:
            joined_table_columns_info[column_name] = {}
            
            # Embed data type
            data_type = _daft_2_protoform_type(joined_df.schema()[column_name].dtype, None)
            if data_type is not None:
                joined_table_columns_info[column_name]['data type'] = data_type

        joined_table_name = task_info["output table name"]
        joined_description = {
            'columns':joined_table_columns_info,
            'data format':task_info["output data format"]
        }
        joined_node = graphlib.add_node(graph, joined_table_name, joined_description)
        datalib.set_node_data(joined_node, joined_df)

        # TODO:
        # will need to figure out how to specify where to write this new table

        return True
        
    # END class JoinTables
    pass