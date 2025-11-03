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
from protoform.modules.io.node import NodeWriter
from protoform.modules.io.utils import _extract_db_url, _get_sql_engine
from protoform.utils import _render_env_template, _dict_hash
from daft.io.sink import WriteResult, WriteResultType
from daft.recordbatch import MicroPartition, RecordBatch
from sqlalchemy.engine.url import make_url
from sqlalchemy import create_engine, inspect, text, MetaData, Index, Table
from sqlglot import exp, parse_one
from types import SimpleNamespace
from typing import Optional, TypedDict, List, Any
from sqlalchemy import text

import json
import protoform.data as datalib
import daft
import impala.dbapi
import pandas as pd
import sqlalchemy
import time
import uritools
import os
from datetime import datetime
import logging
logger = logging.getLogger(__name__)


class SqlDataNodeWriter(NodeWriter):
    def __init__(self, node, configurations = None, *args, **kwds):
        super().__init__(node, *args, **kwds)

        node_info = node.description

        df = datalib.get_node_data(node)
        columns_info = node_info["columns"]
        table_name = node_info.get("stored table name", self.node.get_name())

        self.df = df
        self.columns_info = columns_info
        self.table_name = table_name

        self._configurations = configurations
        self._node_writer_type = TYPE_SQL
        return


    def generate_data_url(self, output_path, render = False, **kwargs):
        '''
        The url provided by user is expected to already conforms to db url format, e.g. sqlite:///, mysql://
        Render environment variables if specified and check if the input url is supported
        '''
        if render:
            output_path = _render_env_template(output_path)

        # Check database type here
        # NOTE: SQLite write will fail
        parsed = uritools.urisplit(output_path)
        if parsed.scheme not in [DB_SQLITE, DB_HIVE2, DB_MYSQL, DB_SNOWFLAKE]:
            raise NotImplementedError("Writing to this SQL database is not supported yet")

        return output_path


    def generate_info_for_manifest(self, output_path, **kwargs):
        table_info = super().generate_info_for_manifest(output_path)

        # The node manifest info for sql node type might also include a field to config the data source
        configs = self._configurations
        if configs is not None and isinstance(configs, dict):
            table_info["data source config ref"] = _dict_hash(configs)

        return table_info


    def write(self, db_url: str, if_exists: IfExists = EXISTS_FAIL) -> bool:
        columns = self.columns_info.keys()
        df = self.df.select(*columns)

        # Create SQLAlchemy connection
        engine: sqlalchemy.engine.base.Engine = _get_sql_engine(db_url, self._configurations)
        with engine.begin() as connection:
            metadata = MetaData()
            metadata.reflect(bind = connection)
            is_table_exists = self.table_name in metadata.tables

            if if_exists == EXISTS_FAIL and is_table_exists:
                raise ValueError(f"Table `{self.table_name}` already exists")
            # Insert table if not exists
            if not is_table_exists:
                self._insert_table(df, connection, self.table_name)
                return True

            if if_exists == EXISTS_FAIL and is_table_exists:
                raise ValueError(f"Table `{self.table_name}` already exists")

            elif if_exists == EXISTS_MOVE:
                # Table already exists, we write the new table to database first,
                # confirm that it has been written successfully, then rename the 2 tables
                ts = str(int(time.time()))
                temp_name = f"temp_{self.table_name}_{ts}"
                new_name = f"{self.table_name}_{ts}_renamed"
                try:
                    self._insert_table(df, connection, temp_name)

                    # Confirm if success write
                    metadata = MetaData()
                    metadata.reflect(bind = connection)
                    if temp_name in metadata.tables:
                        # Move the existing table to new name
                        self._rename_table(connection, self.table_name, new_name)

                        metadata = MetaData()
                        metadata.reflect(bind = connection)
                        if new_name not in metadata.tables:
                            raise Exception("Failed to rename existing table")

                        self._rename_table(connection, temp_name, self.table_name)
                        return True

                except Exception as err:
                    logger.exception("Failed to overwrite table. Reverting old table back")
                    # This most likely to fail in pandas to_sql(), not _rename_table()
                    metadata = MetaData()
                    metadata.reflect(bind = connection)

                    if temp_name in metadata.tables:
                        self._delete_table(connection, temp_name)

                    if new_name in metadata.tables:
                        self._rename_table(connection, new_name, self.table_name)
                        
                    # TODO: We might need to handle atomicity at the task-plan level
                    
                    return False

    def _insert_table(self, df: daft.dataframe.DataFrame,
                      connection: sqlalchemy.engine.Connection,
                      table_name: str):
        """
        Inserts a Daft DataFrame into a SQL database in append mode using `pandas.DataFrame.to_sql()`.
        The insertion is done in batches and utilizes a custom insertion helper for batch insertion.

        Args:
            df (daft.dataframe.DataFrame): The Daft DataFrame to be inserted into the database.
            connection (sqlalchemy.engine.Connection): SQLAlchemy connection to the target database.
            table_name (str): Name of the target table in the database.
        """

        parsed: SimpleNamespace = _extract_db_url(connection.engine.url)
        dialect = parsed.dialect

        def _insert_helper(table: pd.io.sql.SQLTable, conn: sqlalchemy.engine.Connection, keys: List[str], data_iter: zip):
            col_str = ", ".join(map(lambda k: f"`{k}`", keys))
            placeholder_str = ", ".join([f":{k.replace(' ', '')}" for k in keys])
            query = str(parse_one(f'INSERT INTO `{table_name}` ({col_str}) VALUES ({placeholder_str})', dialect = "mysql").sql(dialect = dialect, identify = True))
            mapped_rows = list(map(lambda row: dict(zip(map(lambda k: k.replace(" ", ""), keys), row)), data_iter))
            conn.execute(text(query), mapped_rows)

        for partition in df.iter_partitions():
            # For some reason, inserting using "multi" method is extremely slow with SQLite
            # The other option is to insert 1 row at a time, which will be slow with large data
            partition.to_pandas().to_sql(table_name, connection, if_exists = "append", chunksize = 20000, method = _insert_helper)


    def _delete_table(self, connection: sqlalchemy.engine.Connection, table_name: str):
        """
        Drops a table from the SQL database if it exists.

        Args:
            connection (sqlalchemy.engine.Connection): SQLAlchemy connection to the target database.
            table_name (str): Name of the table to be dropped.
        """

        parsed: SimpleNamespace = _extract_db_url(connection.engine.url)
        db = parsed.drivername
        schema = parsed.database
        dialect = parsed.dialect

        table = exp.Table(this = exp.to_identifier(table_name), db = exp.to_identifier(schema))
        query = str(exp.Drop(this = table, kind = "TABLE", exists = True).sql(dialect = dialect, identify = True))

        connection.execute(text(query))


    def _rename_table(self, connection: sqlalchemy.engine.Connection, old_name: str, new_name: str):
        """
        Renames a table in the connected SQL database.

        Args:
            connection (sqlalchemy.engine.Connection): Active SQLAlchemy database connection.
            old_name (str): Current name of the table to be renamed.
            new_name (str): New desired name for the table.
        """

        parsed: SimpleNamespace = _extract_db_url(connection.engine.url)
        db = parsed.drivername
        schema = parsed.database
        dialect = parsed.dialect

        old_table = exp.Table(this = exp.to_identifier(old_name), db = exp.to_identifier(schema))
        new_table = exp.Table(this = exp.to_identifier(new_name), db = exp.to_identifier(schema))
        query = text(str(exp.rename_table(old_table, new_table).sql(dialect = dialect, identify = True)))

        connection.execute(query)

        # SQLite does not rename index automatically so we have to do this manually
        if db == DB_SQLITE:
            inspector = inspect(connection)
            metadata = MetaData()
            metadata.reflect(bind = connection)

            indexes = inspector.get_indexes(new_name)
            for index in indexes:
                old_index_name = index["name"]
                columns = index["column_names"]
                unique = index.get("unique", False)

                # Drop old index
                connection.execute(text(f"DROP INDEX IF EXISTS {old_index_name}"))

                # Create new index with updated name
                new_index_name = f"ix_{new_name}_index"
                new_table = Table(new_name, metadata, autoload_with = connection)
                new_index = Index(new_index_name, *[new_table.c[col] for col in columns], unique = unique)
                new_index.create(bind = connection)

    # END class SqlDataNodeWriter
