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

from sqlalchemy import text
from snowflake.connector.errors import ProgrammingError
from snowflake.connector.pandas_tools import pd_writer

from protoform.modules.operator.write_dataset import WriteDatasetTaskInfo as GraphOutputInfo
from protoform.modules.io.sink.sql import SqlDataNodeWriter
from protoform.modules.io.utils import _get_sql_engine
from sqlalchemy import text

import json
import protoform.data as datalib
import daft
import sqlalchemy
from datetime import datetime
import os
import logging
import snowflake

logger = logging.getLogger(__name__)

class SnowflakeSqlDataNodeWriter(SqlDataNodeWriter):
    def __init__(self, node, configurations = None, *args, **kwds):
        super().__init__(node, *args, **kwds)

        node_info = node.description

        df = datalib.get_node_data(node)
        columns_info = node_info["columns"]
        table_name = node_info.get("name", self.node.get_name())

        self.df = df
        self.columns_info = columns_info
        self.table_name = table_name

        self._configurations = configurations


    def write(self, db_url: str, graph_output_info: GraphOutputInfo, if_exists: IfExists = EXISTS_FAIL) -> bool:
        # Create SQLAlchemy connection
        engine: sqlalchemy.engine.base.Engine = _get_sql_engine(db_url, self._configurations)
        #sqlalchemy by default set num_statements to None, need to overwrite method to set num_statements to zero
        from sqlalchemy import event

        @event.listens_for(engine, 'do_execute')
        def do_execute(cursor, statement, parameters, context):
            return cursor.execute(statement, parameters, num_statements=0)

        with engine.connect() as connection:
            for step in graph_output_info.writer_data["steps"]:
                if step['action'] == WRITE_TABLE_TO_SQL:
                    columns = self.columns_info.keys()
                    df = self.df.select(*columns)
                    self._write_graph_to_snowflake_table(df, db_url, if_exists, step['output schema'])
                elif step['action'] == WRITE_CSV_TO_BUCKET:
                    self._write_csv_to_snowflake_bucket(connection, step['output schema'])
                elif step['action'] == WRITE_BUCKET_TO_SQL:
                    self._write_bucket_to_snowflake_sql(connection, step['input schema'], step['output schema'])
                elif step['action'] == MERGE_TABLE:
                    self._merge_snowflake_table(connection, step['input schema'], step['output schema'])
                else:
                    raise NotImplementedError("This action to snowflake is not supported yet")            
        return True
    
    
    def _insert_table(self, df: daft.dataframe.DataFrame,
                      connection: sqlalchemy.engine.Connection,
                      table_name: str):
        if_exists = 'replace'
        today = datetime.today().strftime("%Y%m%d")
        for partition in df.iter_partitions():
            # For some reason, inserting using "multi" method is extremely slow with SQLite
            # The other option is to insert 1 row at a time, which will be slow with large data
            # Change column names to uppercase
            p = partition.to_pandas()
            p['version'] = today
            # Convert all column names to uppercase
            p.columns = p.columns.str.upper()
            p.to_sql(table_name, connection, schema=self.output_schema.upper(), if_exists = if_exists, index=False, method = pd_writer)
            if_exists = 'append'
    
    
    def _rename_table(self, connection: sqlalchemy.engine.Connection, old_name: str, new_name: str):
        queries = [f"ALTER TABLE {old_name} RENAME TO {new_name};"]
        self._write_snowflake(connection, queries)


    def _write_graph_to_snowflake_table(self, df: daft.dataframe.DataFrame,
                      db_url: str,
                      if_exists: bool,
                      output_schema: str):
        self.output_schema = output_schema
        super().write(db_url,if_exists)


    def _write_snowflake(self, connection: sqlalchemy.engine.Connection, queries: list) -> bool:
        try:
            result = connection.execute(text('\n'.join(queries)))
            for row in result:
                logger.info(row)
            return True
        except ProgrammingError as e:
            logger.exception(f"Error connecting to Snowflake: {e}")
            return False


    def _write_csv_to_snowflake_bucket(self, connection: sqlalchemy.engine.Connection, output_schema: str):
        
        queries = [
            f"PUT file://data/{self.table_name}/{self.table_name}.csv @{os.environ['SNOWFLAKE_OUTPUT_DATABASE_NAME']}.{os.environ['SNOWFLAKE_STAGE']}.\"{output_schema}\"/ OVERWRITE = TRUE;"
        ]
        self._write_snowflake(connection, queries)


    def _write_bucket_to_snowflake_sql(self, connection: sqlalchemy.engine.Connection,
                      input_schema:str, output_schema: str):
        with open(f"data/{self.table_name}/{self.table_name}.csv.metadata.json", 'r') as f:
            data = json.load(f)
            #Treat the "BEGIN TRANSACTION => COMMIT" block as a single logical unit
            queries = [
                f"BEGIN TRANSACTION;",
                f"CREATE OR REPLACE TABLE {os.environ['SNOWFLAKE_OUTPUT_DATABASE_NAME']}.{output_schema}.{self.table_name} ({','.join([d.get('name')+' '+d.get('type') for d in data['columns']])});",
                f"COPY INTO {os.environ['SNOWFLAKE_OUTPUT_DATABASE_NAME']}.{output_schema}.{self.table_name} FROM @{os.environ['SNOWFLAKE_INPUT_DATABASE_NAME']}.{os.environ['SNOWFLAKE_STAGE']}.{input_schema}/{self.table_name}.csv.gz FILE_FORMAT = (TYPE = CSV SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '\"');",
                f"ALTER TABLE {os.environ['SNOWFLAKE_OUTPUT_DATABASE_NAME']}.{output_schema}.{self.table_name} SET COMMENT = '{input_schema}';"
                f"ROLLBACK;"
             ]
            self._write_snowflake(connection, queries)


    def _merge_snowflake_table(self, connection: sqlalchemy.engine.Connection,
                      input_schema:str, output_schema: str):
        with open(f"data/{self.table_name}/{self.table_name}.csv.metadata.json", 'r') as f:
            data = json.load(f)
            queries = [
                f"BEGIN TRANSACTION;",
                f"""
                DELETE FROM {os.environ['SNOWFLAKE_OUTPUT_DATABASE_NAME']}.{output_schema}.{self.table_name} AS T
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM {os.environ['SNOWFLAKE_INPUT_DATABASE_NAME']}.{input_schema}.{self.table_name} AS S
                    WHERE {' AND '.join(['T.'+d.get('name')+' = S.'+d.get('name') for d in data['columns']])}
                );
                """,
                f"""  MERGE INTO {os.environ['SNOWFLAKE_OUTPUT_DATABASE_NAME']}.{output_schema}.{self.table_name} AS T
                USING {os.environ['SNOWFLAKE_INPUT_DATABASE_NAME']}.{input_schema}.{self.table_name} AS S
                ON {' AND '.join(['T.'+d.get('name')+' = S.'+d.get('name') for d in data['columns']])}
                WHEN NOT MATCHED THEN INSERT ({','.join([d.get('name') for d in data['columns']])}) VALUES ({','.join(['S.'+d.get('name') for d in data['columns']])});""",
                f"ALTER TABLE {os.environ['SNOWFLAKE_OUTPUT_DATABASE_NAME']}.{output_schema}.{self.table_name} SET COMMENT = '{input_schema}';"
                f"ROLLBACK;"
                ]
            self._write_snowflake(connection, queries)