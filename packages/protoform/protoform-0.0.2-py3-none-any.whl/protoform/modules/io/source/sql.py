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

import protoform.graph as graphlib

from protoform.modules.common import *
from protoform.modules.io.node import NodeReader
from protoform.modules.io.utils import _extract_db_url, _get_sql_engine
from protoform.utils import _render_env_template

import daft
import sqlalchemy
import logging

from sqlglot import exp, parse_one
from types import SimpleNamespace
from typing import Any, Optional, TypedDict, List

logger = logging.getLogger(__name__)

class SQLQueryParts(TypedDict):
    tables: List[str]
    columns: List[str]
    where: List[str]

class SqlDataNodeReader(NodeReader):

    def __init__(self, node, *args, **kwds):

        super().__init__(node, *args, **kwds)

        node_info = node.description

        table_name = node_info["stored table name"]
        self.table_name = table_name

        return

    def set_configurations(self):
        super().set_configurations()
        # Replace the placeholders in param with env vars
        configs: dict[str, Any] = self.configurations
        for param, value in configs.items():
            if type(value) == str:
                configs[param] = _render_env_template(value)
        return

    def set_url(self):
        node_info = self.node.description
        data_url = node_info["data url"]

        data_url = _render_env_template(data_url)
        self.url = data_url
        return

    def generate_query_parts_for_row_filter(self):

        node_info = self.node.description

        where_parts = []

        row_filter = node_info.get("row filter", None)
        if row_filter is None:

            # check to see if predecessor has a row_filter defined
            graph = self.node.graph
            for column_name, column_info in self.columns_info.items():
                reference = column_info.get("references", None)
                if reference is None:
                    # this column does not reference another table
                    continue

                predecessor_name, primary_column = reference.split(".")
                predecessor = graphlib.get_node(graph, predecessor_name)
                predecessor_df = predecessor.description["data"]
                filter_ids = predecessor_df.select(primary_column).to_pydict()[primary_column]

                ids_string = "'" + "','".join(filter_ids) + "'"
                where_part = f"{column_name} in ( {ids_string} )"

                where_parts.append(where_part)

        else:
            row_filter_method = node_info.get("row filter method", None)
            if row_filter_method is None:
                raise ValueError("row filter method needs to be specified")
            elif row_filter_method == 'sql query':
                where_parts.append(row_filter)
            else:
                raise NotImplementedError(f"row filter method {row_filter_method} not implemented")
        return where_parts


    def generate_query_parts(self):

        # select only the columns that we need
        columns = list(self.columns_info.keys())

        table_name = self.table_name
        tables = [table_name]

        where_parts = self.generate_query_parts_for_row_filter()

        query_parts = {
            "columns":columns,
            "tables":tables,
            "where":where_parts
        }

        return query_parts


    def _read_into_dataframe(self):
        # Database params
        url = self.url
        
        # Construct SQL query & execute to create dataframe
        query_parts: SQLQueryParts = self.generate_query_parts()
        query: str = _construct_node_reader_query(url, query_parts)
        schema = self.data_schema()

        engine: sqlalchemy.engine.base.Engine = _get_sql_engine(url, self.configurations)
        df = daft.read_sql(query, engine.connect, infer_schema = len(schema) == 0, schema = schema)    

        # in the ticket that I created, the daft team educated me on quoting
        # https://github.com/Eventual-Inc/Daft/issues/4749
        # >> In SQL, the double-quotes are used for (delimited) identifiers,
        # >> whereas single quotes are for string literals!
        where_parts = query_parts["where"]
        for where_part in where_parts:
            df = df.where(where_part)

        return df

    # END class SqlDataNodeReader
    pass


def _construct_node_reader_query(db_url: str, query_parts: SQLQueryParts) -> str:
    """
    Constructs a SQL query string by parsing the connection URL and query parameters.

    Args:
        db_url (str): The database connection URL.
        query_parts (SQLQueryParts): A dictionary defining the query structure:
            - 'tables' (List[str]): List of table names (only the first is used).
            - 'columns' (List[str]): List of column names to select. If empty, selects all columns.

    Returns:
        str: A SQL query string compatible with the target database's dialect.
    """

    # Get DB type
    parsed: SimpleNamespace = _extract_db_url(db_url)
    db = parsed.drivername
    schema = parsed.database
    dialect = parsed.dialect

    # Construct SQL query
    table_name: str = query_parts["tables"][0]
    columns: List[str] = query_parts["columns"]

    # Create table
    table = exp.Table(this = exp.to_identifier(table_name), db = exp.to_identifier(schema))

    # Build SELECT clause
    if columns:
        select = exp.select(*[exp.Column(this = exp.to_identifier(col), table = table) for col in columns]).from_(table)
    else:
        select = exp.select("*").from_(table)

    # Convert to SQL string
    return select.sql(dialect = dialect, identify = True)