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

from pydantic import (
    BaseModel,
    ConfigDict,
)
from typing import List, Optional


def underscore_to_space(string: str) -> str:
    return string.replace("_", " ")

class OperatorBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=underscore_to_space, populate_by_name=True
    )

class OperatorBaseTaskInfo(OperatorBaseModel):
    predecessors: Optional[List[str]] = []


class Operator(object):
    @classmethod
    def is_graph_operator(cls):
        return False

    def __init__(self):
        self._post_run_callbacks = []
        return

    def run(self, task_info, execution_context):
        try:
            success = self.do_work(task_info, execution_context)
            if success:
                self.on_success()
            else:
                self.on_failure()
        except Exception as e:
            self.on_error(e)

        self.call_post_run_callbacks()
        return

    def do_work(self, task_info, execution_context):
        raise NotImplementedError

    def add_post_run_callback(self, callback):
        self._post_run_callbacks.append(callback)
        return

    def call_post_run_callbacks(self):
        for cb in self._post_run_callbacks:
            cb()
        return

    def on_success(self):
        return

    def on_error(self, error):
        logging.error("errored on do_work for " + self.__class__.__name__)
        raise error

    def on_failure(self):
        logging.error("failed on do_work for " + self.__class__.__name__)
        return

    pass
