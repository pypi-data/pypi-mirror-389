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

from protoform.modules.common import *
from protoform.modules.io.common import FileUriHandler
from protoform.modules.io.node import NodeWriter

import logging
import shutil

logger = logging.getLogger(__name__)

class ParquetDataNodeWriter(NodeWriter):
    # output_path is a pathlib object
    def __init__(self, node, *args, **kwds):
        super().__init__(node, *args, **kwds)

        node_info = node.description

        df = datalib.get_node_data(node)
        columns_info = node_info["columns"]

        self.df = df
        self.columns_info = columns_info
        self._node_writer_type = TYPE_PARQUET
        return


    def generate_data_url(self, output_path, is_parent_location=True):
        node_name = self.node.get_name()
        data_url = FileUriHandler.generate_file_url(f"{node_name}.parquet", output_path,
                                                    is_parent_location=is_parent_location)
        return data_url


    def write(self, output_path):
        logger.debug(f"writing to {output_path}")

        columns = self.columns_info.keys()
        df = self.df.select(*columns)

        parent_path = FileUriHandler.generate_parent_url(output_path)
        output_df = df.write_parquet(parent_path)

        daft_output_paths = output_df.to_pydict()["path"]

        count = len(daft_output_paths)
        if count != 1:
            logger.error("need to implement the case where parquet files are written " + count + " files")
            raise NotImplementedError

        # this handles the situation where daft writes to the directory provided
        # and names the file with randomly generated uuids
        daft_output_path = daft_output_paths[0]
        logger.debug(f"wrote to {daft_output_path}, moving to {output_path}")
        shutil.move(daft_output_path, output_path)
        return


    # END class ParquetDataNodeWriter
    pass