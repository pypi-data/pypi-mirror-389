"""Routes for the DataScribe API.

This module defines the API endpoints and their corresponding models for the DataScribe API.
"""

from datascribe_api.models import (
    DataTableColumns,
    DataTableMetadata,
    DataTableRows,
    DataTableRowsCount,
    DataTables,
    MaterialByIdResults,
    MaterialSearchResults,
)

ROUTES = {
    "get_data_tables": ("/data/data-tables", DataTables, []),
    "get_data_table": ("/data/data-table", DataTableRows, ["tableName"]),
    "get_data_tables_for_user": ("/data/data-tables-for-user", DataTables, []),
    "get_data_table_rows": ("/data/data-table-rows", DataTableRows, ["tableName", "columns"]),
    "get_data_table_columns": ("/data/data-table-columns", DataTableColumns, ["tableName"]),
    "get_data_table_metadata": ("/data/data-table-metadata", DataTableMetadata, ["tableName"]),
    "get_data_table_rows_count": ("/data/data-table-rows-count", DataTableRowsCount, ["tableName"]),
    "get_material_by_id": ("/materials", MaterialByIdResults, ["ids"]),
    "search_materials": ("/materials/search", MaterialSearchResults, []),
}
