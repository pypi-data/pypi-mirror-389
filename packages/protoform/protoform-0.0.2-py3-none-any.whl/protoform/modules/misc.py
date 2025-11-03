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


import daft

def remove_ethnicity(df): 
    select_columns = [] 
    column_names = df.column_names 
    for column_name in column_names: 
        col_expr = daft.col(column_name) 
        if column_name == 'ETHNICITY':
            col_expr = daft.lit('').alias('ETHNICITY') 
        select_columns.append(col_expr) 
    df = df.select(*select_columns) 
    return df
