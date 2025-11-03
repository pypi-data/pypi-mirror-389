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


#!/usr/bin/env python3

import argparse
import logging
import pathlib
import sys

import protoform.io as iolib
import protoform.task as tasklib


def parse_args():
    parser = argparse.ArgumentParser(
        description='Execute a task plan on a data graph'
    )
    parser.add_argument(
        '--task-plan',
        required=True,
        type=pathlib.Path,
        help='Path to the task plan JSON file'
    )
    parser.add_argument(
        '--data-graph',
        required=True,
        type=pathlib.Path,
        help='Path to the data graph JSON file'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set the logging level'
    )
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # AWS libraries
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    try:
        # Load task plan
        logging.info(f"Loading task plan from {args.task_plan}")
        task_reader = iolib.TaskPlanReader()
        task_graph = task_reader.load_from_file(args.task_plan)
        task_reader.load_data_for_graph(task_graph)
        
        # Load data graph
        logging.info(f"Loading data graph from {args.data_graph}")
        manifest_reader = iolib.ManifestReader()
        data_graph = manifest_reader.load_from_file(args.data_graph)
        manifest_reader.load_data_for_graph(data_graph)
        
        # Execute task plan
        logging.info("Executing task plan")
        output_graph = tasklib.apply_task_plan_to_data(task_graph, data_graph)
        
        logging.info("Task plan execution completed successfully")
        return 0
        
    except Exception as e:
        logging.error(f"Error executing task plan: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main()) 
