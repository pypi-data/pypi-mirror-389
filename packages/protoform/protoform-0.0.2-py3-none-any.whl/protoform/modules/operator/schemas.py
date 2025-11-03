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

from protoform.modules.common import *
from protoform.modules.operator.common import (
    OperatorBaseModel,
    OperatorBaseTaskInfo,
    underscore_to_space,
)
from protoform.modules.operator.unpivot_table import UnPivotTableTaskInfo as UnPivotTable
from protoform.modules.operator.write_dataset import WriteDatasetTaskInfo as WriteDataset

from pydantic import (
    Field,
    field_validator,
    ConfigDict,
)
from typing import Any, Optional, List, Dict, Union, Literal, Annotated


class LoadDataset(OperatorBaseTaskInfo):
    operator: Literal["load dataset"]
    operator_type: Literal["builtin"]
    manifest_url: str


# Start ShapeDataGraph
class CreateTable(OperatorBaseModel):
    action: Literal["create table"]
    table: str
    columns: List[str]


class SelectTables(OperatorBaseModel):
    action: Literal["select tables"]
    tables: List[str]


class RemoveTable(OperatorBaseModel):
    action: Literal["remove table"]
    table: str


class RenameTable(OperatorBaseModel):
    model_config = ConfigDict(
        alias_generator=underscore_to_space, populate_by_name=True
    )
    action: Literal["rename table"]
    table: str
    new_table_name: str


class CopyTable(OperatorBaseModel):
    model_config = ConfigDict(
        alias_generator=underscore_to_space, populate_by_name=True
    )
    action: Literal["copy table"]
    table: str
    new_table_name: str


class ColumnInfo(OperatorBaseModel):
    model_config = ConfigDict(
        alias_generator=underscore_to_space, populate_by_name=True
    )
    data_type: Optional[
        Literal["int", "integer", "float", "boolean", "date", "timestamp"]
    ] = None
    default_value: Optional[Any] = None


class AddColumn(OperatorBaseModel):
    model_config = ConfigDict(
        alias_generator=underscore_to_space, populate_by_name=True
    )
    action: Literal["add column"]
    table: str
    new_column_name: str
    column_info: Optional[Dict[str, ColumnInfo]] = None


class RemoveColumn(OperatorBaseModel):
    action: Literal["remove column"]
    table: str
    column: str


class RenameColumn(OperatorBaseModel):
    model_config = ConfigDict(
        alias_generator=underscore_to_space, populate_by_name=True
    )
    action: Literal["rename column"]
    table: str
    column: str
    new_column_name: str


class AddRow(OperatorBaseModel):
    action: Literal["add row"]
    pass


class RemoveRow(OperatorBaseModel):
    action: Literal["remove row"]
    pass


class TransposeTable(OperatorBaseModel):
    action: Literal["transpose table"]
    pass


class SelectColumns(OperatorBaseModel):
    model_config = ConfigDict(
        alias_generator=underscore_to_space, populate_by_name=True
    )
    action: Literal["select columns"]
    table: str
    columns: List[str]
    column_info: Optional[Dict[str, ColumnInfo]] = None


# End ShapeDataGraph


class ShapeDataGraph(OperatorBaseTaskInfo):
    operator: Literal["shape data"]
    operator_type: Literal["builtin"]
    steps: List[
        Annotated[
            Union[
                CreateTable,
                SelectTables,
                RemoveTable,
                RenameTable,
                CopyTable,
                AddColumn,
                RemoveColumn,
                RenameColumn,
                AddRow,
                RemoveRow,
                TransposeTable,
                SelectColumns,
            ],
            Field(discriminator="action"),
        ]
    ]


class SubsetDataByPercentage(OperatorBaseTaskInfo):
    operator: Literal["subset graph by percentage"]
    operator_type: Literal["builtin"]
    percentage: int
    seed: int


class HipaaDeidentifier(OperatorBaseTaskInfo):
    operator: Literal["hipaa deidentify"]
    operator_type: Literal["builtin"]
    table_deid_info: Optional[str] = None
    salt: str


class JoinTables(OperatorBaseTaskInfo):
    operator: Literal["join tables"]
    operator_type: Literal["builtin"]
    left_table: str
    right_table: str
    join_type: Literal["inner", "left", "right", "outer", "anti", "semi", "cross"]
    left_columns: List[str]
    right_columns: List[str]
    output_table_name: str
    output_data_format: str


class FilterTable(OperatorBaseTaskInfo):
    operator: Literal["filter table"]
    operator_type: Literal["builtin"]
    table: str
    filter: str


# Start DynamicLoadCode
class ParseText(OperatorBaseModel):
    code_text: str
    function_name: Optional[str]


class ImportModule(OperatorBaseModel):
    module_name: str
    function_name: Optional[str]


class ParseFile(ImportModule):
    module_url: str


# End DynamicLoadCode


class DynamicLoadCode(OperatorBaseTaskInfo):
    operator: Literal["dynamic load code"]
    operator_type: Literal["builtin"]
    code_text: Optional[str] = None
    function_name: Optional[str] = None
    module_name: Optional[str] = None
    module_url: Optional[str] = None
    load_method: Literal["parse text", "import module", "parse file"]

    @field_validator("load_method")
    @classmethod
    def validate_load_method(cls, v, info):
        if v == "parse text":
            ParseText.model_validate(info.data)
        elif v == "import module":
            ImportModule.model_validate(info.data)
        elif v == "parse file":
            ParseFile.model_validate(info.data)
        else:
            raise ValueError("Not found load method: " + v)
        return v


class PivotTable(OperatorBaseTaskInfo):
    operator: Literal["pivot table"]
    operator_type: Literal["builtin"]
    table: str
    group_by: Union[str, List[str]]
    pivot_column: str
    value_column: str
    output_table_name: str
    agg_function: str


class NormalizeString(OperatorBaseTaskInfo):
    operator: Literal["normalize string"]
    operator_type: Literal["builtin"]
    table: str
    column: str
    normalizations: Dict[str, Any]


class Operator(OperatorBaseModel):
    tasks: Dict[
        str,
        Annotated[
            Union[
                LoadDataset,
                ShapeDataGraph,
                SubsetDataByPercentage,
                HipaaDeidentifier,
                JoinTables,
                WriteDataset,
                FilterTable,
                DynamicLoadCode,
                PivotTable,
                UnPivotTable,
                NormalizeString,
            ],
            Field(discriminator="operator"),
        ],
    ]
