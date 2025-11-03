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

from sqlalchemy.engine.url import make_url
from sqlalchemy import create_engine
from types import SimpleNamespace
from typing import Optional

import protoform.data as datalib
import protoform.graph as graphlib
import ciso8601
import daft
import impala.dbapi
import logging
import sqlalchemy

logger = logging.getLogger(__name__)

def _autogen_column_schema(node):
    node_info = node.description

    autogen_info = node_info["info to autogenerate column schema"]
    source_type = autogen_info["source type"]
    if source_type != "table column":
        raise NotImplementedError("autogen column schema from other than table column not yet implemented")
    primary_table, primary_column = autogen_info["source"].split(".")
    primary_node = graphlib.get_node(node.graph, primary_table)
    primary_node_df = datalib.get_node_data(primary_node)
    primary_node_df.collect()

    default_data_type = autogen_info.get('default column data type', 'string')
    column_names = primary_node_df.to_pydict()[primary_column]
    columns_info = {}
    for column_name in column_names:
        columns_info[column_name] = {"data type":default_data_type}
    columns_info.update(autogen_info.get("columns to prepend info", {}))
    columns_info.update(autogen_info.get("columns to append info", {}))
    
    return columns_info


def _get_sql_engine(url, configurations) -> sqlalchemy.engine.base.Engine:
    parsed: SimpleNamespace = _extract_db_url(url)
    db: str = parsed.drivername
    host: Optional[str] = parsed.host
    port: Optional[int] = parsed.port

    # Create SQLAlchemy connection
    if db == DB_HIVE2:
        # Handle db/query engine that uses Thrift protocol
        def hive_connect():
            conn: impala.hiveserver2.HiveServer2Connection = impala.dbapi.connect(
                host = host,
                port = port,
                **configurations
            )
            return conn

        # Wrap the get_connection method above in sqlAlchemy engine so that daft
        # does not complain
        engine = create_engine(f"hive://", creator = hive_connect)
    elif db == DB_MYSQL:
        # SQLAlchemy defaults to using MySQLdb, a C-based MySQL driver — but it's not installed by default
        # The easiest fix is to switch to pymysql, which we already have
        engine = create_engine(url.replace("mysql://", "mysql+pymysql://"))
    else:
        engine = create_engine(url)

    return engine


def _extract_db_url(db_url) -> SimpleNamespace:
    parsed: sqlalchemy.engine.url.URL = make_url(db_url)
    db = parsed.drivername

    dict_parsed = parsed._asdict()
    dict_parsed["dialect"] = db

    # Don't specify the schema that the table comes from,
    # e.g. schema.tableA.columnB should be tableA.columnB
    # in case of sqlite
    if db == DB_SQLITE:
        dict_parsed["database"] = None
    elif db == DB_HIVE2:
        dict_parsed["dialect"] = "hive"
    elif db == "mysql+pymysql":
        dict_parsed["dialect"] = "mysql"
    elif db == "awsathena+rest":
        dict_parsed["dialect"] = "athena"

    return SimpleNamespace(**dict_parsed)


# use a more robust datetime parsing
def _parse_datetime(value: Optional[str]):
    try:
        return ciso8601.parse_datetime(value)
    except Exception as err:
        logger.debug('errored on parsing datetime from "' + value + '"')
        return None
