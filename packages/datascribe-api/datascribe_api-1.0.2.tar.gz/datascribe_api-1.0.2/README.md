<div align="center">

# DataScribe API Client

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://opensource.org/license/gpl-3-0)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Platforms](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey)
[![Tests](https://github.com/DataScribe-Cloud/datascribe_api/actions/workflows/test.yml/badge.svg)](https://github.com/DataScribe-Cloud/datascribe_api/actions/workflows/test.yml)

[![DOI](https://zenodo.org/badge/1024595385.svg)](https://doi.org/10.5281/zenodo.17090844)

`datascribe_api` is a Python client for interacting with the DataScribe API. It allows users to search for data tables and their metadata, automating data retrieval and analysis workflows.

<p>
  <a href="https://github.com/DataScribe-Cloud/datascribe_api/issues/new?labels=bug">Report a Bug</a> |
  <a href="https://github.com/DataScribe-Cloud/datascribe_api/issues/new?labels=enhancement">Request a Feature</a> |
<a href="https://datascribe-cloud.github.io/datascribe_api/">Documentation</a>
</p>

</div>

---

## Features

- Search and retrieve data tables and metadata from the DataScribe API
- Simple Python interface for querying endpoints
- Automatic model mapping for API responses
- Context manager support for resource management

---

## Installation

You can use pip to install the `datascribe_api` package directly from PyPI:

```sh
pip install datascribe_api
```

---

## Quick Start

### Python Client Usage
To get started with the `datascribe_api`, you can use the following example to retrieve and print the names of data tables available to the user:
```python
from datascribe_api import DataScribeClient

with DataScribeClient(api_key="YOUR_API_TOKEN") as client:
    tables = client.get_data_tables_for_user()
    for table in tables:
        print(f"Table Name: {table.display_name}")
```

Make sure to replace the `DataScribeClient` initialization with your actual API key or store it in an environment variable named `DATASCRIBE_API_TOKEN` for authentication.

### API Endpoints

Below is a list of all available endpoints in the DataScribe API Python client:

| Endpoint Name             | HTTP Path                   | Parameters                                                                                 | Description                               |
|---------------------------|-----------------------------|--------------------------------------------------------------------------------------------|-------------------------------------------|
| get_data_tables           | /data/data-tables           | –                                                                                          | List all data tables (admin only)         |
| get_data_tables_for_user  | /data/data-tables-for-user  | –                                                                                          | List data tables available to the user    |
| get_data_table            | /data/data-table            | tableName, startingRow, numRows                                                            | Get rows from a data table                |
| get_data_table_rows       | /data/data-table-rows       | tableName, columns, startingRow , numRows, filters                                         | Get rows from a data table (with columns) |
| get_data_table_rows_count | /data/data-table-rows-count | tableName, filters                                                                         | Get row count for a data table            |
| get_data_table_columns    | /data/data-table-columns    | tableName                                                                                  | Get columns of a data table               |
| get_data_table_metadata   | /data/data-table-metadata   | tableName                                                                                  | Get metadata for a data table             |
| get_material_by_id        | /materials                  | ids, providers                                                                             | Get material by IDs                       |
| search_materials          | /materials/search           | formula, elements, exclude_elements, spacegroup, props, temperature, providers, page, size | Search for materials                      |

---


### Filtering Data with the Filter Class

The `datascribe_api` package provides a powerful and expressive `Filter` class for building complex queries in a Pythonic way. Filters can be passed to API methods as dictionaries, single `Filter` objects, or lists of `Filter` objects (for AND logic).

#### Basic Usage

```python
from datascribe_api import DataScribeClient
from datascribe_api.filter import Filter

with DataScribeClient(api_key="YOUR_API_TOKEN") as client:
    filters = Filter("age") > 30
    rows = client.get_data_table_rows(tableName="users", columns=["age", "name"], filters=filters)
    for row in rows:
        print(row)
```

#### Supported Filter Operations

- **Equality and Comparison**
  ```python
  Filter("age") == 25
  Filter("score") != 100
  Filter("height") > 170
  Filter("height") >= 180
  Filter("height") < 200
  Filter("height") <= 160
  ```

- **IN and NOT IN**
  ```python
  Filter("status").in_(["active", "pending"])
  Filter("role").not_in(["guest", "banned"])
  ```

- **LIKE and ILIKE (case-insensitive LIKE)**
  ```python
  Filter("name").like("%John%")
  Filter("email").ilike("%@gmail.com")
  ```

- **IS NULL and IS NOT NULL**
  ```python
  Filter("deleted_at").is_null()
  Filter("deleted_at").is_not_null()
  ```

#### Combining Multiple Filters (AND logic)

You can pass a list of filters to combine them with AND logic:

```python
filters = [
    Filter("age") > 18,
    Filter("status") == "active",
    Filter("country").in_(["US", "CA"])
]
rows = client.get_data_table_rows(tableName="users", columns=["age", "status", "country"], filters=filters)
```

#### Passing Filters as Dictionaries

You can also pass filters as plain dictionaries if you prefer:

```python
filters = {"column": "age", "operator": ">", "value": 21}
rows = client.get_data_table_rows(tableName="users", columns=["age"], filters=filters)
```

---

### CLI Usage

You can also use the command-line interface to interact with the DataScribe API. Here are some examples:

```sh
# List all data tables for the authenticated user
datascribe_cli data-tables-for-user
```

```sh
# Retrieve rows from the data table named m3gnet_mpf
datascribe_cli data-table --table-name m3gnet_mpf
```

See the [CLI documentation](README_CLI.md) for more commands and options.

---

## License

This project is licensed under the GNU GPLv3 License. See the [LICENSE](./LICENSE) file for details.
