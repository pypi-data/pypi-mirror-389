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

import copy
import daft

import protoform.data as datalib
from protoform.modules.io.utils import _autogen_column_schema, _parse_datetime
from protoform.utils import _protoform_2_daft_type

class Writer:
    pass

class Reader:
    pass

class NodeWriter(Writer):

    def __init__(self, node, *args, **kwds):
        self.node = node
        self._node_writer_type = None # Overwrite this in child class
        
        return

    def generate_info_for_manifest(self, output_path, is_parent_location = True):
        node = self.node
        node_info = node.description

        table_info = {}
        if "is root" in node_info:
            table_info["is root"] = node_info["is root"]

        table_info["data format"] = self._node_writer_type

        data_url = self.generate_data_url(output_path, is_parent_location = is_parent_location)
        table_info["data url"] = data_url

        # generate the columns info
        node_df = datalib.get_node_data(node)
        node_columns_info = node_info["columns"]
        output_columns_info = {}
        for column_name in node_df.column_names:
            if column_name not in node_columns_info:
                continue
            output_columns_info[column_name] = node_columns_info[column_name]
            pass
        table_info["columns"] = output_columns_info

        return table_info

    pass

class NodeReader:

    def __init__(self, node, *args, **kwds):

        self.node = node

        self.set_url()
        self.set_configurations()

        node_info = node.description

        # check whether we need to autogen the column schema
        data_first_row_is_header = True
        if node_info.get("autogenerate column schema", False) is True:
            data_first_row_is_header = False
            columns_info = _autogen_column_schema(node)
            node_info["columns"] = columns_info
            pass
        self.set_is_first_row_header(data_first_row_is_header)

        columns_info = node_info["columns"]
        self.columns_info = columns_info

        return

    def set_configurations(self):
        node_info = self.node.description
        # Do deep copy so that it does not render the object's env var placeholder
        # with real env value
        self.configurations = copy.deepcopy(node_info.get("data source config", {}))
        return

    def set_url(self):
        node_info = self.node.description
        data_url = node_info["data url"]
        self.url = data_url
        return

    def set_is_first_row_header(self, header_row):
        self._is_first_row_header = header_row
        return

    def is_first_row_header(self):
        return self._is_first_row_header

    def data_schema(self):
        schema = {}
        for column_name, column_info in self.columns_info.items():           
            data_type = column_info.get("data type", "string")
            if data_type == "timestamp":
                # for timestamp, we will first read it as string, then convert it later
                # this is because daft's timestamp parsing is not very robust
                schema[column_name] = daft.DataType.string()
            else:
                schema[column_name] = _protoform_2_daft_type(data_type, "string")    
        return schema

    def _read_into_dataframe(self):
        raise NotImplementedError("This function needs to be implemented by subclasses")

    def read(self):
        df = self._read_into_dataframe()

        # now try to convert to actual timetamp format
        # at the same time, also only include columns that were specified in the manifest
        columns_to_select = []
        columns_to_parse = {}
        for column_name, column_info in self.columns_info.items():
            data_type = column_info.get("data type", "string")
            if data_type != "timestamp":
                columns_to_select.append(daft.col(column_name))
                continue
            parsed_name = column_name + "_parsed"
            columns_to_parse[parsed_name] = daft.col(column_name).apply(_parse_datetime, 
                                                                        return_dtype=daft.DataType.timestamp(timeunit="s"))
            columns_to_select.append(daft.col(parsed_name).alias(column_name))

        # If a node does not have schema, then we don't need to parse any columns and we will select all columns
        # However, in this case, columns_to_select will be empty and calling .select() with empty list will cause error
        if len(columns_to_select) > 0:
            df = df.with_columns(columns_to_parse).select(*columns_to_select)

        return df

    pass