# protoform

[![Release](https://img.shields.io/github/v/release/dataxight/protoform)](https://img.shields.io/github/v/release/dataxight/protoform)
[![Build status](https://img.shields.io/github/actions/workflow/status/dataxight/protoform/main.yml?branch=main)](https://github.com/dataxight/protoform/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/dataxight/protoform/branch/main/graph/badge.svg)](https://codecov.io/gh/dataxight/protoform)
[![Commit activity](https://img.shields.io/github/commit-activity/m/dataxight/protoform)](https://img.shields.io/github/commit-activity/m/dataxight/protoform)
[![License](https://img.shields.io/github/license/dataxight/protoform)](https://img.shields.io/github/license/dataxight/protoform)

shaping data

- **Github repository**: <https://github.com/dataxight/protoform/>
- **Documentation** <https://dataxight.github.io/protoform/>

## Getting started with your project

## Concept of protoform

protoform is a data operation management system implemented in python using a graph and network (python-igraph) to handle the manipulation of data structure. protoform leverages tasks and performed operations to the data graph by these steps.
- Define the source of data (for instance from sql database, csv file).
- Define the tasks.
- Convert the source of data and tasks to a graph (data graph and task graph) 
- Execute protoform.
protoform will digest the tasks and independently operate in parallel (unless you define dependencies) then apply those tasks to the raw data, and export new data.

## Working modules

- `cli` : captures the arguments of task and data paths and executes operations regarding the task plans.
- `io` : converts tasks to task graphs, reads input data (csv, tsv, parquet, and sql), converts the data to data graph, exports the objects to graph, csv file, or pushes to sql database.
- `operator` : contains a list of operations what to do to the data.
- `data` : implements data operation classes.
- `graph` : implements graph classs.

## Installation

- **Installation guide** <https://github.com/dataxight/protoform/wiki/Installation>

## Execution
- You need to prepare two files:
> 1. task manifest file (such as task.json). Follow an instruction how to but a task graph here: <https://github.com/dataxight/protoform/wiki/Execution-Graph-Specification>
> 2. data manifest file (such as data.json). Follow an instruction how to but a data graph here: <https://github.com/dataxight/protoform/wiki/Data-Graph-Specification>
- Run the first command

```bash
protoform --task-plan task.json --data-graph data.json
```

---

Repository initiated with [fpgmaas/cookiecutter-poetry](https://github.com/fpgmaas/cookiecutter-poetry).
