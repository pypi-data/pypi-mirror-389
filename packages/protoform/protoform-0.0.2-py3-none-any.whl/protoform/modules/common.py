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

from typing import Literal

# Input/Output type
TYPE_TABLE = "table"
TYPE_PARQUET = "parquet"
TYPE_TSV = "tsv"
TYPE_CSV = "csv"
TYPE_SQL = "sql"
TYPE_MANIFOLD = "manifold"
TYPE_BUCKET = 'bucket'
TYPE_SNOWFLAKE = "snowflake"

# write data action type
ACTION_WRITE = "write"
ACTION_MERGE = "merge"

# Database
DB_LOCAL = "local"
DB_HIVE2 = "hive2"
DB_MYSQL = "mysql"
DB_SQLITE = "sqlite"
DB_SNOWFLAKE = "snowflake"

# Operator when writing to existing output
EXISTS_MOVE = "move"
EXISTS_REPLACE = "replace"
EXISTS_FAIL = "fail"

#snowflake actions
WRITE_TABLE_TO_SQL = "write table to sql"
WRITE_CSV_TO_BUCKET = "write csv to bucket"
WRITE_BUCKET_TO_SQL = "write bucket to sql"
MERGE_TABLE = "merge table"

# Custom types
IfExists = Literal[EXISTS_MOVE, EXISTS_REPLACE, EXISTS_FAIL]
DataType = Literal[TYPE_TABLE, TYPE_PARQUET, TYPE_TSV, TYPE_CSV, TYPE_SQL, TYPE_MANIFOLD, TYPE_BUCKET, TYPE_SNOWFLAKE]
DatabaseType = Literal[DB_LOCAL, DB_HIVE2, DB_MYSQL, DB_SQLITE, DB_SNOWFLAKE]
ActionType = Literal[ACTION_WRITE, ACTION_MERGE]
ActionSnowflakeType = Literal[WRITE_TABLE_TO_SQL, WRITE_CSV_TO_BUCKET, WRITE_BUCKET_TO_SQL, MERGE_TABLE]

