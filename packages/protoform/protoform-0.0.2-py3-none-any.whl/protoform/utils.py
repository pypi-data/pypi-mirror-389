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
import hashlib
import json
import os
import re

from string import Template
from typing import Dict, List, Iterable, Any

def _render_env_template(url: str) -> str:
    # This string template expects $ delimiter
    template = Template(url)
    pattern: re.Pattern = template.pattern

    # Extract the environment variable names specified in
    # the url
    os_envs: Iterable[re.Match] = pattern.finditer(url) # Extract os env names

    # Iterate through each os env, extract the assigned value & store for
    # substituting later. Any envs not found will be recorded & raise an exception
    error_os_envs: List[str] = []
    data: Dict[str, str] = {}
    for match in os_envs:
        os_env = match.group("named") or match.group("braced")
        if os_env:
            val = os.environ.get(os_env, None)
            if not val:
                error_os_envs.append(os_env)
            else:
                data[os_env] = str(val)

    if len(error_os_envs):
        raise Exception(f"Environment variables {', '.join(error_os_envs)} not found for SQL connection")

    return template.substitute(data)

def _dict_hash(dictionary: Dict[str, Any]) -> str:
    """MD5 hash of a dictionary."""
    dhash = hashlib.md5()
    encoded = json.dumps(dictionary, sort_keys = True).encode()
    dhash.update(encoded)
    return dhash.hexdigest()

def _protoform_2_daft_type(type: str, default = "string") -> daft.DataType:
    mapping = {
        "string": daft.DataType.string(),
        "integer": daft.DataType.int64(),
        "int": daft.DataType.int64(),
        "float": daft.DataType.float64(),
        "boolean": daft.DataType.bool(),
        "date": daft.DataType.date(),
        "timestamp": daft.DataType.timestamp(timeunit="s"),
    }
    if default is None:
        if type not in mapping:
            raise Exception(f"Unsupported data type {type}")
        return mapping[type]
    else:
        return mapping.get(type, mapping[default])
    
def _daft_2_protoform_type(type: daft.DataType, default = daft.DataType.string()) -> str:
    # Group similar data types
    integer_types = [
        daft.DataType.int8(),
        daft.DataType.int16(),
        daft.DataType.int32(),
        daft.DataType.int64(),
        daft.DataType.uint8(),
        daft.DataType.uint16(),
        daft.DataType.uint32(),
        daft.DataType.uint64()
    ]
    float_types = [
        daft.DataType.float32(),
        daft.DataType.float64()
    ]

    # Map of categories to their related types
    type_groups = {
        "string": [daft.DataType.string()],
        "integer": integer_types,
        "float": float_types,
        "boolean": [daft.DataType.bool()],
        "date": [daft.DataType.date()],
    }

    # Flatten the above into a mapping
    mapping = {dtype: name for name, types in type_groups.items() for dtype in types}

    # Timestamp needs special handling as it has parameters
    if daft.DataType.is_timestamp(type):
        return "timestamp"

    if default is None:
        if type not in mapping:
            raise Exception(f"Unsupported data type {type}")
        return mapping[type]
    else:
        return mapping.get(type, mapping[default])