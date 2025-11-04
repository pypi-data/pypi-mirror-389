"""DataScribe API Models.

This module defines the Pydantic models used for interacting with the DataScribe API.
These models represent the structure of data returned by the API endpoints.
"""

from collections.abc import Iterator
from datetime import datetime
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, RootModel


class DatabaseSchemaColumn(BaseModel):
    """Represents a column in a database schema.

    Attributes:
        column_name (str): The name of the column.
        column_type (str): The type of the column (e.g., VARCHAR, INT).
        nullable (bool): Indicates whether the column can contain NULL values.
        default_value (Any | None): The default value for the column, if any.
        type_options (dict[str, Any] | None): Additional type-specific options for the column.
        metadata (dict[str, Any] | None): Metadata associated with the column.
    """

    column_name: str
    column_type: str
    nullable: bool
    default_value: Any | None = None
    type_options: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class DatabaseSchema(BaseModel):
    """Represents a database schema.

    Attributes:
        table_name (str): The name of the table in the schema.
        description (str): A description of the table.
        columns (list[DatabaseSchemaColumn]): A list of columns in the table.
    """

    table_name: str
    description: str
    columns: list[DatabaseSchemaColumn]


class DataTableColumn(BaseModel):
    """Represents a column in a data table.

    Attributes:
        column_name (str): The name of the column.
        data_type (str): The data type of the column.
        is_nullable (bool): Indicates whether the column can contain NULL values.
        column_default (Any | None): The default value for the column, if any.
        numeric_precision (int | None): The numeric precision of the column, if applicable.
        numeric_scale (int | None): The numeric scale of the column, if applicable.
        character_maximum_length (int | None): The maximum length for character data, if applicable.
        ordinal_position (int | None): The position of the column in the table.
    """

    column_name: str
    data_type: str
    is_nullable: str
    column_default: Any | None = None
    numeric_precision: int | None = None
    numeric_scale: int | None = None
    character_maximum_length: int | None = None
    ordinal_position: int | None = None


class DataTableColumns(BaseModel):
    """Represents the columns of a data table.

    Attributes:
        table_name (str): The name of the table.
        display_name (str): The display name of the table.
        columns (list[DataTableColumn]): A list of columns in the table.
    """

    table_name: str
    display_name: str
    columns: list[DataTableColumn]

    def __len__(self) -> int:
        """Return the number of columns."""
        return len(self.columns)

    def to_dataframe(self) -> pd.DataFrame:
        """Return columns as a pandas DataFrame."""
        return pd.DataFrame([col.model_dump() for col in self.columns])

    def to_list(self) -> list[Any]:
        """Return column names as a list."""
        return [col.column_name for col in self.columns]


class DataTableRowsCount(BaseModel):
    """Represents the count of rows in a data table.

    Attributes:
        total_rows (int): The number of rows in the table.
    """

    total_rows: int

    def to_dataframe(self) -> pd.DataFrame:
        """Return row count as a pandas DataFrame."""
        return pd.DataFrame([self.model_dump()])

    def to_list(self) -> list[Any]:
        """Return row count as a list."""
        return [self.total_rows]


class DataTableRow(BaseModel):
    """Represents the rows of a data table."""

    model_config = ConfigDict(extra="allow")


class DataTableRows(RootModel):
    """Represents the rows of a data table."""

    root: list[DataTableRow]

    def __iter__(self) -> Iterator[DataTableRow]:
        return iter(self.root)

    def __getitem__(self, item: int) -> DataTableRow:
        return self.root[item]

    def __len__(self) -> int:
        """Return the number of rows."""
        return len(self.root)

    def to_dataframe(self) -> pd.DataFrame:
        """Return rows as a pandas DataFrame."""
        return pd.DataFrame([row.model_dump() for row in self.root])

    def to_list(self) -> list[Any]:
        """Return rows as a list of dicts."""
        return [row.model_dump() for row in self.root]


class DataTableMetadata(BaseModel):
    """Represents metadata for a data table.

    Attributes:
        table_name (str): The name of the table.
        display_name (str): The display name of the table.
        user_id (int): The ID of the user associated with the table.
        created_on (str): The creation timestamp of the table.
        last_updated (str): The last update timestamp of the table.
        table_type (str): The type of the table (e.g., temporary, permanent).
        visibility (str): The visibility of the table (e.g., public, private).
        database_schema (DatabaseSchema): The schema of the database associated with the table.
    """

    table_name: str
    display_name: str
    user_id: int
    created_on: datetime
    last_updated: datetime
    table_type: str
    visibility: str
    database_schema: DatabaseSchema

    def to_dataframe(self) -> pd.DataFrame:
        """Return metadata as a pandas DataFrame."""
        return pd.DataFrame([self.model_dump()])

    def to_list(self) -> list[Any]:
        """Return metadata as a list of dicts."""
        return [self.model_dump()]


class DataTable(BaseModel):
    """Represents a data table.

    Attributes:
        user_id (int): The ID of the user associated with the table.
        table_name (str): The name of the table.
        display_name (str): The display name of the table.
        database_schema (DatabaseSchema): The schema of the database associated with the table.
        created_on (str): The creation timestamp of the table.
        last_updated (str): The last update timestamp of the table.
        table_type (str): The type of the table (e.g., temporary, permanent).
        visibility (str): The visibility of the table (e.g., public, private).
    """

    table_name: str
    display_name: str
    user_id: int
    database_schema: DatabaseSchema
    created_on: datetime
    last_updated: datetime
    table_type: str
    visibility: str


class DataTables(RootModel):
    """Represents the rows of a data table."""

    root: list[DataTable]

    def __iter__(self) -> Iterator[DataTable]:
        return iter(self.root)

    def __getitem__(self, item: int) -> DataTable:
        return self.root[item]

    def __len__(self) -> int:
        """Return the number of tables."""
        return len(self.root)

    def to_dataframe(self) -> pd.DataFrame:
        """Return tables as a pandas DataFrame."""
        return pd.DataFrame([table.model_dump() for table in self.root])

    def to_list(self) -> list[Any]:
        """Return tables as a list of dicts."""
        return [table.model_dump() for table in self.root]


class Provenance(BaseModel):
    """Represents the provenance information for a material.

    Attributes:
        provider (str): The name of the data provider or source.
        id (str): The unique identifier of the material in the provider's database.
    """

    provider: str
    id: str


class MaterialSummary(BaseModel):
    """Represents a summary of material information.

    Attributes:
        material_id (str): The unique identifier for the material.
        formula (str): The chemical formula of the material.
        elements (List[str]): List of element symbols present in the material.
        systems (List[str]): List of crystal systems associated with the material.
        key_props (Dict[str, Any]): Dictionary of key material properties (e.g., bandgap, formation energy).
        provenance (List[Provenance]): List of provenance information for the material.
    """

    material_id: str
    formula: str
    elements: list[str]
    systems: list[str]
    key_props: dict[str, Any]
    provenance: list[Provenance]


class MaterialSearchResults(BaseModel):
    """Represents the results of a material search operation.

    Attributes:
        results (List[MaterialSummary]): List of material summary objects returned by the search.
        total (int): Total number of materials found in the search.
    """

    results: list[MaterialSummary]
    total: int

    def to_dataframe(self) -> pd.DataFrame:
        """Return search results as a pandas DataFrame."""
        return pd.DataFrame([summary.model_dump() for summary in self.results])

    def to_list(self) -> list[Any]:
        """Return search results as a list of dicts."""
        return [summary.model_dump() for summary in self.results]


class MaterialData(BaseModel):
    """Represents a Material's information."""

    model_config = ConfigDict(extra="allow")


class MaterialByIdResult(BaseModel):
    """Represents a single material result from a provider for a material ID lookup.

    Attributes:
        provider (str): The name of the data provider (e.g., 'materials_project', 'aflow').
        id (str): The unique identifier of the material.
        data (dict[str, Any]): The raw material document returned by the provider.
    """

    provider: str
    id: str
    data: MaterialData


class MaterialByIdResults(BaseModel):
    """Represents the results of a material ID lookup across multiple providers.

    Attributes:
        results (List[MaterialByIdResult]): List of results from each provider.
        total (int): Total number of materials found across all providers.
    """

    results: list[MaterialByIdResult]
    total: int

    def to_dataframe(self) -> pd.DataFrame:
        """Return results as a pandas DataFrame."""
        return pd.DataFrame([result.model_dump() for result in self.results])

    def to_list(self) -> list[Any]:
        """Return results as a list of dicts."""
        return [result.model_dump() for result in self.results]
