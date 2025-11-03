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

from protoform.modules.common import *
from protoform.modules.io.node import NodeReader

class CsvDataNodeReader(NodeReader):

    def __init__(self, node, *args, **kwds):

        super().__init__(node, *args, **kwds)

        node_info = node.description

        data_format = node_info["data format"]
        delimiter = ","
        if data_format == TYPE_TSV:
            delimiter = "\t"
        self.set_delimiter(delimiter)

        return


    def set_delimiter(self, delimiter):
        self._delimiter = delimiter

    def _read_into_dataframe(self):
        schema = self.data_schema()

        header_row = self.is_first_row_header()
        infer_schema = header_row

        df = daft.read_csv(self.url, delimiter=self._delimiter, infer_schema=infer_schema, schema=schema, has_headers=header_row)
        return df
