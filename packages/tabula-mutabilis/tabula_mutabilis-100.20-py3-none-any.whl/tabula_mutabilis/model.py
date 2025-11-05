"""Data models for Tabula Mutabilis table widget.

This module provides the core data abstractions:
- CellValueFormatter: Converts Python types to display strings
- CellStyle: Styling information for cells
- TableDataProvider: Abstract interface for table data
- InMemoryDataProvider: Concrete implementation using tablib
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

import tablib
from vultus_serpentis import Observable


class CellValueFormatter:
    """Converts various Python types to display strings for table cells."""

    def __init__(
        self,
        date_format: str = "%Y-%m-%d",
        datetime_format: str = "%Y-%m-%d %H:%M:%S",
        decimal_places: int = 2,
        none_display: str = "",
    ) -> None:
        """Initialize the formatter with display options.

        Args:
            date_format: strftime format for date objects
            datetime_format: strftime format for datetime objects
            decimal_places: Number of decimal places for floats
            none_display: String to display for None values
        """
        self.date_format = date_format
        self.datetime_format = datetime_format
        self.decimal_places = decimal_places
        self.none_display = none_display

    def format(self, value: Any) -> str:
        """Convert a value to its display string.

        Args:
            value: The value to format

        Returns:
            String representation suitable for display
        """
        if value is None:
            return self.none_display
        if isinstance(value, bool):
            return "True" if value else "False"
        if isinstance(value, datetime):
            return value.strftime(self.datetime_format)
        if isinstance(value, date):
            return value.strftime(self.date_format)
        if isinstance(value, float):
            return f"{value:.{self.decimal_places}f}"
        if isinstance(value, Decimal):
            return f"{value:.{self.decimal_places}f}"
        return str(value)


@dataclass
class CellStyle:
    """Styling information for a table cell."""

    font: tuple[str, int] = ("TkDefaultFont", 10)
    text_color: str = "#000000"
    bg_color: str = "#FFFFFF"
    row_height: int = 25
    col_width: int = 100
    horiz_justify: str = "w"  # 'w', 'center', 'e'
    vert_justify: str = "center"  # 'n', 'center', 's'
    borders: dict[str, tuple[int, str]] = field(default_factory=dict)
    visibility: bool = True
    cell_editor_class: Optional[type] = None
    span_columns: bool = False  # If True, cell spans all columns in the row

    def copy(self, **overrides: Any) -> CellStyle:
        """Create a copy of this style with optional overrides.

        Args:
            **overrides: Fields to override in the copy

        Returns:
            New CellStyle instance
        """
        data = {
            "font": self.font,
            "text_color": self.text_color,
            "bg_color": self.bg_color,
            "row_height": self.row_height,
            "col_width": self.col_width,
            "horiz_justify": self.horiz_justify,
            "vert_justify": self.vert_justify,
            "borders": self.borders.copy(),
            "visibility": self.visibility,
            "cell_editor_class": self.cell_editor_class,
            "span_columns": self.span_columns,
        }
        data.update(overrides)
        return CellStyle(**data)


class TableDataProvider(Observable, abc.ABC):
    """Abstract interface for table data.

    Inherits from Observable to notify observers of data changes.
    All mutation methods must call _notify_observers() after changes.
    """

    @abc.abstractmethod
    def get_row_count(self) -> int:
        """Return the number of rows in the table."""
        ...

    @abc.abstractmethod
    def get_column_count(self) -> int:
        """Return the number of columns in the table."""
        ...

    @abc.abstractmethod
    def get_value(self, row: int, col: int) -> Any:
        """Get the value at the specified cell.

        Args:
            row: Row index (0-based)
            col: Column index (0-based)

        Returns:
            The cell value
        """
        ...

    @abc.abstractmethod
    def set_value(self, row: int, col: int, value: Any) -> None:
        """Set the value at the specified cell.

        Must call self._notify_observers(event_type='data_changed', payload={...})
        after updating the value.

        Args:
            row: Row index (0-based)
            col: Column index (0-based)
            value: The new value
        """
        ...

    @abc.abstractmethod
    def get_column_headers(self) -> list[str]:
        """Return the column headers."""
        ...

    @abc.abstractmethod
    def set_column_headers(self, headers: list[str]) -> None:
        """Set the column headers.

        Must call self._notify_observers() after updating.

        Args:
            headers: List of header strings
        """
        ...

    @abc.abstractmethod
    def insert_row(self, index: int, data: list[Any]) -> None:
        """Insert a new row at the specified index.

        Must call self._notify_observers() after insertion.

        Args:
            index: Position to insert (0-based)
            data: List of values for the new row
        """
        ...

    @abc.abstractmethod
    def delete_row(self, index: int) -> None:
        """Delete the row at the specified index.

        Must call self._notify_observers() after deletion.

        Args:
            index: Row index to delete (0-based)
        """
        ...

    @abc.abstractmethod
    def insert_column(self, index: int, header: str, default_value: Any = None) -> None:
        """Insert a new column at the specified index.

        Must call self._notify_observers() after insertion.

        Args:
            index: Position to insert (0-based)
            header: Column header
            default_value: Default value for existing rows
        """
        ...

    @abc.abstractmethod
    def delete_column(self, index: int) -> None:
        """Delete the column at the specified index.

        Must call self._notify_observers() after deletion.

        Args:
            index: Column index to delete (0-based)
        """
        ...


class InMemoryDataProvider(TableDataProvider):
    """Concrete implementation of TableDataProvider using tablib.Dataset."""

    def __init__(self, headers: Optional[list[str]] = None, data: Optional[list[list[Any]]] = None) -> None:
        """Initialize the data provider.

        Args:
            headers: Optional list of column headers
            data: Optional initial data as list of rows
        """
        super().__init__()
        self.dataset = tablib.Dataset()
        if headers:
            self.dataset.headers = headers
        if data:
            for row in data:
                self.dataset.append(row)
        self._formatter = CellValueFormatter()

    def get_row_count(self) -> int:
        """Return the number of rows."""
        return len(self.dataset)

    def get_column_count(self) -> int:
        """Return the number of columns."""
        return len(self.dataset.headers) if self.dataset.headers else 0

    def get_value(self, row: int, col: int) -> Any:
        """Get the value at the specified cell."""
        if row < 0 or row >= self.get_row_count():
            raise IndexError(f"Row index {row} out of range")
        if col < 0 or col >= self.get_column_count():
            raise IndexError(f"Column index {col} out of range")
        return self.dataset[row][col]

    def set_value(self, row: int, col: int, value: Any) -> None:
        """Set the value at the specified cell."""
        if row < 0 or row >= self.get_row_count():
            raise IndexError(f"Row index {row} out of range")
        if col < 0 or col >= self.get_column_count():
            raise IndexError(f"Column index {col} out of range")

        # tablib doesn't support direct cell assignment, so we need to update the row
        row_data = list(self.dataset[row])
        row_data[col] = value
        self.dataset[row] = tuple(row_data)

        self._notify_observers(
            event_type="data_changed",
            payload={"row": row, "col": col, "value": value}
        )

    def get_column_headers(self) -> list[str]:
        """Return the column headers."""
        return list(self.dataset.headers) if self.dataset.headers else []

    def set_column_headers(self, headers: list[str]) -> None:
        """Set the column headers."""
        self.dataset.headers = headers
        self._notify_observers(
            event_type="headers_changed",
            payload={"headers": headers}
        )

    def insert_row(self, index: int, data: list[Any]) -> None:
        """Insert a new row at the specified index."""
        if index < 0 or index > self.get_row_count():
            raise IndexError(f"Row index {index} out of range")

        # Ensure data matches column count
        col_count = self.get_column_count()
        if len(data) < col_count:
            data = list(data) + [None] * (col_count - len(data))
        elif len(data) > col_count:
            data = data[:col_count]

        self.dataset.insert(index, data)
        self._notify_observers(
            event_type="row_inserted",
            payload={"index": index, "data": data}
        )

    def delete_row(self, index: int) -> None:
        """Delete the row at the specified index."""
        if index < 0 or index >= self.get_row_count():
            raise IndexError(f"Row index {index} out of range")

        del self.dataset[index]
        self._notify_observers(
            event_type="row_deleted",
            payload={"index": index}
        )

    def insert_column(self, index: int, header: str, default_value: Any = None) -> None:
        """Insert a new column at the specified index."""
        col_count = self.get_column_count()
        if index < 0 or index > col_count:
            raise IndexError(f"Column index {index} out of range")

        # Create column data with default values
        col_data = [default_value] * self.get_row_count()

        # Update headers
        headers = self.get_column_headers()
        headers.insert(index, header)

        # Rebuild dataset with new column
        new_data = []
        for row_idx in range(self.get_row_count()):
            row = list(self.dataset[row_idx])
            row.insert(index, col_data[row_idx])
            new_data.append(row)

        self.dataset = tablib.Dataset(*new_data, headers=headers)
        self._notify_observers(
            event_type="column_inserted",
            payload={"index": index, "header": header}
        )

    def delete_column(self, index: int) -> None:
        """Delete the column at the specified index."""
        if index < 0 or index >= self.get_column_count():
            raise IndexError(f"Column index {index} out of range")

        # Update headers
        headers = self.get_column_headers()
        del headers[index]

        # Rebuild dataset without the column
        new_data = []
        for row_idx in range(self.get_row_count()):
            row = list(self.dataset[row_idx])
            del row[index]
            new_data.append(row)

        self.dataset = tablib.Dataset(*new_data, headers=headers)
        self._notify_observers(
            event_type="column_deleted",
            payload={"index": index}
        )

    def get_formatter(self) -> CellValueFormatter:
        """Get the value formatter for this provider."""
        return self._formatter

    def set_formatter(self, formatter: CellValueFormatter) -> None:
        """Set a custom value formatter.

        Args:
            formatter: The formatter to use
        """
        self._formatter = formatter
        self._notify_observers(
            event_type="formatter_changed",
            payload={"formatter": formatter}
        )

    def sort_by_column(self, col: int, reverse: bool = False) -> None:
        """Sort the data by the specified column.

        Args:
            col: Column index to sort by
            reverse: If True, sort in descending order
        """
        if col < 0 or col >= self.get_column_count():
            raise IndexError(f"Column index {col} out of range")

        # Get all rows as tuples
        rows = [tuple(row) for row in self.dataset]

        # Sort by the specified column
        # Handle None values by putting them at the end
        def sort_key(row):
            val = row[col] if col < len(row) else None
            if val is None:
                return (1, "")  # Put None values at end
            # Try to convert to comparable type
            try:
                # If it's a number, use it directly
                if isinstance(val, (int, float)):
                    return (0, val)
                # Try to convert string to number
                return (0, float(val))
            except (ValueError, TypeError):
                # Fall back to string comparison
                return (0, str(val).lower())

        sorted_rows = sorted(rows, key=sort_key, reverse=reverse)

        # Rebuild dataset with sorted data
        headers = list(self.dataset.headers) if self.dataset.headers else None
        self.dataset = tablib.Dataset(*sorted_rows, headers=headers)

        self._notify_observers(
            event_type="data_sorted",
            payload={"column": col, "reverse": reverse}
        )