from typing import Any

from datascribe_api.filter import Filter
from datascribe_api.models import (
    DataTableColumns,
    DataTableMetadata,
    DataTableRows,
    DataTableRowsCount,
    DataTables,
    MaterialByIdResults,
    MaterialSearchResults,
)

class DataScribeClient:
    def __init__(self, api_key: str | None = None, base: str = "https://datascribe.cloud/") -> None:
        self._base = None
        self._session = None
        self._api_key = None
        ...
    def __enter__(self) -> DataScribeClient: ...
    def __exit__(self, *args: Any) -> None: ...
    def close(self) -> None: ...
    def _get(self, path: str, params: dict[str, Any]): ...
    def search(self, endpoint: str, **kwargs: Any) -> Any: ...
    def get_data_tables(self) -> DataTables: ...
    def get_data_table(self, tableName: str, startingRow: int = 0, numRows: int = 100) -> DataTableRows: ...
    def get_data_tables_for_user(self) -> DataTables: ...
    def get_data_table_rows(
        self,
        tableName: str,
        columns: list[str],
        startingRow: int = 0,
        numRows: int = 100,
        filters: dict[str, Any] | Filter | list[Filter] | None = None,
    ) -> DataTableRows: ...
    def get_data_table_columns(self, tableName: str) -> DataTableColumns: ...
    def get_data_table_metadata(self, tableName: str) -> DataTableMetadata: ...
    def get_data_table_rows_count(
        self, tableName: str, filters: dict[str, Any] | Filter | list[Filter] | None = None
    ) -> DataTableRowsCount: ...
    def get_material_by_id(self, ids: str, providers: list[str] | str) -> MaterialByIdResults: ...
    def search_materials(
        self,
        formula: str | None = None,
        elements: list[str] | str | None = None,
        exclude_elements: list[str] | str | None = None,
        spacegroup: str | None = None,
        props: list[str] | str | None = None,
        temperature: float | str | None = None,
        providers: list[str] | str | None = None,
        page: int = 1,
        size: int = 50,
    ) -> MaterialSearchResults: ...
