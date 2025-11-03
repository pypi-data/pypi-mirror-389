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
import datetime
import hashlib
import logging
import rustworkx as rx

import protoform.data as datalib
import protoform.graph as graphlib

from protoform.modules.common import *
from protoform.modules.operator.common import Operator

logger = logging.getLogger(__name__)

@daft.udf(return_dtype=daft.DataType.int32())
def compute_hipaa_datetime_offset(x: daft.Series, salt=b''):
    if type(salt) == str:
        salt = salt.encode()
        
    offset_values = []
    for v in x.to_pylist():
        if v is None:
            offset_values.append(None)
            continue
        # use the last 32 bytes so that we use different ones than the hash function
        # so that it's not easy to compute offset from the hash
        offset = (int.from_bytes(hashlib.blake2b(v.encode(), salt=salt).digest()[-32:], byteorder='big') % 365) + 1
        offset_values.append(str(offset))
        pass
    
    return offset_values

@daft.udf(return_dtype=daft.DataType.string())
def compute_hipaa_hash(x: daft.Series, salt=b''):
    if type(salt) == str:
        salt = salt.encode()

    hashed_values = []
    for v in x.to_pylist():
        if v is None:
            hashed_values.append(None)
            continue
        # use the 1st 16 hex chars (ie 1st 32 bytes) so that we use different ones
        # than the timestamp shift function so its not easy to compute offset from the hash
        hashed = hashlib.blake2b(v.encode(), salt=salt).hexdigest()[:16]
        hashed_values.append(hashed)

    return hashed_values

def compute_time_shift(values_to_shift: daft.Series, shift_values: daft.Series):
    shifted_values = []
    for a, b in zip(values_to_shift.to_pylist(), shift_values.to_pylist()):
        if a is None:
            shifted_values.append(a)
            continue
        if b is None:
            b = 1
        b = datetime.timedelta(days=b)
        shifted = a + b
        shifted_values.append(shifted)
    return shifted_values
    
# while daft requires casting of return value (need to verify?)
# under the covers it call the same Python function
@daft.udf(return_dtype=daft.DataType.date())
def compute_date_shift(values_to_shift: daft.Series, shift_values: daft.Series):
    return compute_time_shift(values_to_shift, shift_values)    

# while daft requires casting of return value (need to verify?)
# under the covers it call the same Python function
@daft.udf(return_dtype=daft.DataType.timestamp(timeunit='s'))
def compute_timestamp_shift(values_to_shift: daft.Series, shift_values: daft.Series):
    return compute_time_shift(values_to_shift, shift_values)

@daft.udf(return_dtype=daft.DataType.string())
def hipaa_obfuscate_zip_code(values: daft.Series):
    least_populous_zips = [
        '036', '692', '878', '059', '790', '879',
        '063', '821','884', '102','823','890',
        '203','830','893','556','831']
    obfuscated = []
    for value in values.to_pylist():
        if value[:3] in least_populous_zips:
            obfuscated.append('00000')
        else:
            obfuscated.append(value[:3]+'00')
    return obfuscated

class HipaaDeidentifier(Operator):
    def do_work(self, task_info, execution_context):
        graph = execution_context['graph']
        self.deidentify_graph(graph, task_info)
        return True

    def deidentify_graph(self, graph, task_info):

        self.compute_deid_info(graph, task_info)
        salt = task_info['salt']

        node_ids = rx.topological_sort(graph)
        
        for node_id in node_ids:
            node = graph[node_id]
            self.deidentify_node(graph, node, task_info)
            pass

        return
    
    # this function computes the info needed to deidentify for each case
    # so that longitudinal records can be kept intact
    # using the seed, typically the mrn of the patient or study id of the participant
    # a new id and the time offset associated with that id is computed
    def compute_deid_info(self, graph, task_info):
        salt = task_info['salt']

        node = graphlib.get_root_node(graph)
        node_df = datalib.get_node_data(node)

        node_info = node.description        
        columns_info = node_info['columns']

        
        deid_info = task_info.get('table deid info', None)
        if deid_info is None:
            # we are at the root
            deid_info = {}
            task_info['table deid info'] = deid_info

            
        # this is assuming that we're looking at the root node
        # find the column that has the attribute "is HIPAA deidentifier seed":true
        hipaa_seed_column = None
        for column_name, column_info in columns_info.items():
            if column_info.get('is HIPAA deidentifier seed', False) is True:
                hipaa_seed_column = column_name
                break
        if hipaa_seed_column is None:
            raise ValueError('cannot find HIPAA deidentifier seed')

        hipaa_seed_mapping = node_df.select(
            hipaa_seed_column,
            compute_hipaa_hash(node_df[hipaa_seed_column], salt=salt).alias('deidentified id'),
            compute_hipaa_datetime_offset(node_df[hipaa_seed_column], salt=salt).alias('datetime offset'))

        deid_info['graph'] = hipaa_seed_mapping
        return
        
    def deidentify_node(self, graph, node, task_info):
        node_df = datalib.get_node_data(node)
        node_info = node.description        
        columns_info = node_info['columns']

        salt = task_info['salt']
        deid_info = task_info['table deid info']

        joined_df = None
        if graphlib.node_is_root(graph, node.get_name()):
            # this block deidentifies the root node of the graph
            # by using source_deid_df,
            # which contains info that was previously computed for the graph's root id,
            # ie the hipaa hash and the datetime offset
            
            id_column = None
            for column_name, column_info in columns_info.items():
                # this column is the key
                # (assumption is that the key is a single column at the root)
                if column_info.get('is key', False) is True:
                    id_column = column_name
                    break
                pass
            source_deid_df = deid_info['graph']
            joined_df = node_df.join(source_deid_df,
                                     how='left',
                                     left_on=[id_column],
                                     right_on=[id_column])

        else:
            has_join = False
            # inspect the incoming edges
            # to fine one that has the datetime offset
            in_columns = []
            node_idx = graphlib.get_node_index(graph, node.get_name())
            for source_idx, node_idx, in_edge in graph.in_edges(node_idx):
                edge_info = in_edge.description

                source_table = edge_info['primary table']

                source_deid_df = deid_info.get(source_table, None)
                if source_deid_df is None:
                    continue
                if 'datetime offset' not in source_deid_df.column_names:
                    continue

                source_column = edge_info['primary column']
                target_column = edge_info['foreign column']

                # join together so that we know the datetime offset for every trow
                node_df = node_df.join(source_deid_df,
                                       how='left',
                                       left_on=[target_column],
                                       right_on=[source_column])
                has_join = True

            if has_join:
                joined_df = node_df
                
        if joined_df is None:
            logger.info(f"Node ({node.get_name()}) does not seem to need deidentification")
            # this is because this node does not need to be deidentified
            return
        
        # this block sets up to perform the actual deidentification
        columns_to_select = []
        columns_to_remove = []
        for column_name, column_info in columns_info.items():
            daft_expr = daft.col(column_name)
            if column_info.get('is HIPAA identifier', False) is True:
                data_type = column_info.get('data type', 'string')
                if data_type in ['date']:
                    logger.debug("shifting times for column: "+column_name)
                    daft_expr = compute_date_shift(daft.col(column_name), daft.col('datetime offset'))
                elif data_type in ['timestamp']:
                    logger.debug("shifting times for column: "+column_name)
                    daft_expr = compute_timestamp_shift(daft.col(column_name), daft.col('datetime offset'))
                elif column_info.get("HIPAA identifier type", None) == "zip code":
                    logger.debug("obfuscating zip code")
                    daft_expr = hipaa_obfuscate_zip_code(daft_expr)
                elif column_info.get('is key', False) is True:
                    # determine whether the column is a key
                    # if so, then compute the hash
                    daft_expr = compute_hipaa_hash(daft.col(column_name), salt=salt)
                else:
                    # otherwise, just delete the column
                    daft_expr = None
                    columns_to_remove.append(column_name)
                pass
            if daft_expr is not None:
                columns_to_select.append(daft_expr)
            pass

        datalib.set_node_data(node, joined_df.select(*columns_to_select))
        [datalib.remove_column(node, x) for x in columns_to_remove]
        
        # now we want to create a mapping of columns which are primary keys for other tables
        # to the datetime offset, so that the value can be properly propagated to them
        #
        # find the columns with outgoing edges
        out_columns = []
        node_idx = graphlib.get_node_index(graph, node.get_name())
        for node_idx, target_idx, out_edge in graph.out_edges(node_idx):
            # edge_info = out_edge['description']
            edge_info = out_edge.description
            source_column = edge_info['primary column']
            out_columns.append(source_column)
            pass
        out_columns = list(set(out_columns))

        select_columns = [daft.col('datetime offset')]
        select_columns += [daft.col(x) for x in out_columns]
        hipaa_mapping = joined_df.select(*select_columns)
        deid_info[node.get_name()] = hipaa_mapping

        return