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
import os
import pyarrow.csv as pa_csv

import protoform.data as datalib

from protoform.modules.common import *
from protoform.modules.io.common import FileUriHandler
from protoform.modules.io.node import NodeWriter

logger = logging.getLogger(__name__)

class CsvDataNodeWriter(NodeWriter):
    # output_path is a pathlib object
    def __init__(self, node, format_type = TYPE_CSV, *args, **kwds):

        super().__init__(node, *args, **kwds)
        node_info = node.description

        df = datalib.get_node_data(node)
        columns_info = node_info["columns"]

        self.df = df
        self.columns_info = columns_info
        self._node_writer_type = format_type
        return

    def generate_data_url(self, output_path, is_parent_location=True):
        node_name = self.node.get_name()
        data_url = FileUriHandler.generate_file_url(f"{node_name}.{self._node_writer_type}", 
                                                    output_path, 
                                                    is_parent_location=is_parent_location)
        return data_url

    def write(self, output_path):
        logger.debug(f"writing to {output_path}")

        columns = self.columns_info.keys()
        df = self.df.select(*columns)

        # Make sure the output directory exists
        parent_path = FileUriHandler.generate_parent_url(output_path)
        if not os.path.exists(parent_path):
            os.makedirs(parent_path)

        total_rows = 0
        schema = df.schema().to_pyarrow_schema()
        delimiter = "," if self._node_writer_type == TYPE_CSV else "\t"
        write_options: pa_csv.WriteOptions = pa_csv.WriteOptions(delimiter = delimiter) 
        with pa_csv.CSVWriter(output_path, schema, write_options = write_options) as writer:
            for i, batch in enumerate(df.to_arrow_iter()):
                writer.write_batch(batch)
                logger.debug(f"Processed batch {i}, wrote {batch.num_rows} rows to {output_path}")
                total_rows += batch.num_rows

        logger.debug(f"Wrote {total_rows} rows to {output_path}")

        return

    # END class CsvDataNodeWriter
    pass