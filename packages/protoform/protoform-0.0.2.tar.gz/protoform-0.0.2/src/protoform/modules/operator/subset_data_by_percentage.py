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

import secrets

import protoform.data as datalib

from protoform.modules.common import *
from protoform.modules.operator.common import Operator

class SubsetDataByPercentage(Operator):
    def do_work(self, task_info, execution_context):

        graph = execution_context['graph']
        
        # for every outgoing from room
        # take a subset according to that
        percentage = task_info['percentage']
        seed = task_info.get('seed', secrets.randbits(64))

        datalib.subset_graph_percentage(graph, percentage, seed=seed)

        return True

    # END class SubsetDataByPercentage
    pass
