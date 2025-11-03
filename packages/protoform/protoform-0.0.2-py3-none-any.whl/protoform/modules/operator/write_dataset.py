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

from protoform.modules.operator.common import OperatorBaseTaskInfo, underscore_to_space
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Any, Dict, List, Literal, Optional, Union

import protoform.io as iolib

from protoform.modules.common import *
from protoform.modules.operator.common import Operator

logger = logging.getLogger(__name__)


class ManifoldWriterData(BaseModel):
    database_schema: str = Field(
        ..., description="The database schema of Manifold database"
    )
    table_description: Optional[str] = None
    column_info: Optional[Dict[str, Dict]] = None


class SnowflakeWriteTableSql(BaseModel):
    action: Literal[WRITE_TABLE_TO_SQL] = Field(
        ..., description="The action to perform in Snowflake"
    )
    output_schema: str = Field(
        ...,
        description="The output schema for writing table to SQL",
        alias="output schema",
    )


class SnowflakeWriteCsvToBucket(BaseModel):
    action: Literal[WRITE_CSV_TO_BUCKET] = Field(
        ..., description="The action to perform in Snowflake"
    )
    output_schema: str = Field(
        ...,
        description="The output schema for writing CSV to bucket",
        alias="output schema",
    )


class SnowflakeWriteBucketToSql(BaseModel):
    action: Literal[WRITE_BUCKET_TO_SQL] = Field(
        ..., description="The action to perform in Snowflake"
    )
    input_schema: str = Field(
        ...,
        description="The input schema for writing bucket to SQL",
        alias="input schema",
    )
    output_schema: str = Field(
        ...,
        description="The output schema for writing bucket to SQL",
        alias="output schema",
    )


class SnowflakeMergeTable(BaseModel):
    action: Literal[MERGE_TABLE] = Field(
        ..., description="The action to perform in Snowflake"
    )
    input_schema: str = Field(
        ..., description="The input schema for merging table", alias="input schema"
    )
    output_schema: str = Field(
        ..., description="The output schema for merging table", alias="output schema"
    )


# Union of all Snowflake action models
SnowflakeActionStep = Union[
    SnowflakeWriteTableSql,
    SnowflakeWriteCsvToBucket,
    SnowflakeWriteBucketToSql,
    SnowflakeMergeTable,
]


class SnowflakeWriterData(BaseModel):
    steps: List[SnowflakeActionStep] = Field(
        ..., description="List of actions to operate for Snowflake database"
    )


class WriteDatasetTaskInfo(OperatorBaseTaskInfo):
    """
    Configuration model for the WriteDataset operator.

    This class defines the parameters required to write a dataset to a specified output destination.
    It validates the configuration and ensures all necessary fields are present and correctly typed.

    Parameters
    ----------
    output_type : Literal[DataType]
        The type of output destination (e.g., 'manifold', 'snowflake'). Determines how the tables in the dataset are written.
    if_exists : Optional[IfExists], default=EXISTS_FAIL
        Policy for handling existing data at the output location. Defaults to failing if data exists.
        This parameter only applies to output type 'sql' at the moment.
    output_source_config : Optional[Dict[str, Any]], default=None
        Configuration for the data sink (e.g., connection information).
    output_manifest_url : Union[str, None], default=None
        Location where the output manifest should be written. Will be ignored for 'snowflake' data sink.
    selected_output_table : Optional[List[str]], default=[]
        List of output tables to write. Defaults to an empty list. In case of empty list, all tables will be written.
    output_data_url : str
        URL or path where the output data will be written.
    writer_data : Optional[Dict[str, Any] | ManifoldWriterData | SnowflakeWriterData], default={}
        Additional writer-specific configuration. Type depends on `output_type`:
            - If `output_type` is 'manifold', must conform to ManifoldWriterData.
            - If `output_type` is 'snowflake', must conform to SnowflakeWriterData.

    Example
    -------
    >>> task_info = {
    ...     "output type": "csv",
    ...     "output data url": "/path/to/output/data/",
    ... }
    """

    operator: Literal["write dataset"]
    operator_type: Literal["builtin"]

    output_type: Literal[DataType]
    if_exists: Optional[IfExists] = Field(EXISTS_FAIL)
    output_source_config: Optional[Dict[str, Any]] = None
    output_manifest_url: Union[str, None]
    selected_output_table: Optional[List[str]] = Field([])
    output_data_url: str
    writer_data: Optional[Dict[str, Any] | ManifoldWriterData | SnowflakeWriterData] = (
        Field({})
    )

    # validate that if output_type is manifold, then writer_data must be a ManifoldWriterData
    @field_validator("writer_data")
    @classmethod
    def validate_writer_data(cls, v, info):
        if info.data["output_type"] == TYPE_MANIFOLD:
            ManifoldWriterData.model_validate(v)
        elif info.data["output_type"] == TYPE_SNOWFLAKE:
            SnowflakeWriterData.model_validate(v)
        return v


class WriteDataset(Operator):
    def do_work(self, task_info: dict, execution_context):
        graph = execution_context["graph"]

        # In case of a snowflake type, we're not writing a manifest for now
        if task_info["output type"] == TYPE_SNOWFLAKE:
            task_info.update({"output manifest url": None})

        # Validate the task info
        parsed = WriteDatasetTaskInfo.model_validate(task_info)

        graph_writer = iolib.GraphWriter(parsed)
        if task_info["output type"] != TYPE_SNOWFLAKE:
            graph_writer.write_manifest(graph)
        graph_writer.write_data_for_graph(graph)
        return True

    # END class WriteDataset
    pass
