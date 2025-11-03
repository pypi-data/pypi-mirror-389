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

import json as jsonlib
import logging
import os
import pyarrow as pa

import protoform.data as datalib

from protoform.modules.common import *
from protoform.modules.io.common import FileUriHandler
from protoform.modules.io.sink.csv import CsvDataNodeWriter

class ManifoldNodeWriter(CsvDataNodeWriter):
    def __init__(self, node, writer_data, *args, **kwds):
        super().__init__(node, TYPE_CSV, *args, **kwds) # because we want to write data in csv format 
        self.writer_data = writer_data
        self.type_mapping = {
            pa.string(): "VARCHAR",
            pa.int32(): "NUMBER",
            pa.int64(): "NUMBER",
            pa.float64(): "FLOAT",
            #force bool to varchar for now to support manifold platform
            #pa.bool_(): "BOOLEAN",
            pa.bool_(): "VARCHAR",
            pa.date32(): "DATE",
            pa.timestamp('s'): "TIME"
        }
        return


    def write(self, output_path):
        parent_path = FileUriHandler.generate_parent_url(output_path)
        manifest_url = FileUriHandler.generate_file_url(f"{self.node.get_name()}.csv.metadata.json", 
                                                        parent_path)
        # write the data in csv format first before we write the manifest
        super().write(output_path)

        db_schema = self.writer_data["database_schema"]
        
        # Convert Daft schema to PyArrow schema
        pyarrow_schema = self.df.select(*self.columns_info.keys()).schema().to_pyarrow_schema()

        # Extract column information from the pyarrow schema
        columns = []
        for field in pyarrow_schema:
            column_info = self.writer_data.get("column_info", {field.name: {"description": ""}})
            column_description = column_info.get(field.name, {"description":""}).get('description', "")
            columns.append({
                "name": field.name,
                "type": self.type_mapping.get(field.type, "VARCHAR"),  # Use mapping, default to VARCHAR
                "description": column_description,
                "tags": []
            })

        # Create the manifest structure
        manifest = {
            "database_schema": db_schema,
            "table": self.node.get_name(),
            "table_description": self.writer_data.get("table_description",""),  # Placeholder
            "tags": [],
            "columns": columns,
            "file_format": {
                "type": "csv", # because we inherit from CsvDataNodeWriter
                "delimiter": ",",
                "skip_header": 1,
                "null_if": ["\\N", "NULL", ""],
                "encoding": "UTF8"
            }
        }
        # create the directory if it doesn't exist
        os.makedirs(os.path.dirname(manifest_url), exist_ok=True)
        with open(manifest_url, "w") as f:
            jsonlib.dump(manifest, f, indent=4)
        return