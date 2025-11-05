"""View components for Tabula Mutabilis table widget.

This module provides the visual rendering components:
- TableView: Manages virtualization, scrolling, and geometry
- TablePainter: Handles canvas drawing and culling
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .model import CellValueFormatter, TableDataProvider
from .styles import TableStyleProvider


@dataclass
class ViewportBounds:
    """Represents the visible area of the table."""
    left: float
    top: float
    right: float
    bottom: float


@dataclass
class RenderContext:
    """Encapsulates all rendering dependencies for TablePainter.
    
    This eliminates data clumps by grouping related parameters
    that are passed together through multiple methods.
    """
    canvas: tk.Canvas
    view: 'TableView'
    data_provider: TableDataProvider
    style_provider: TableStyleProvider
    selection_model: 'SelectionModel'  # Forward reference
    logger: Any = None  # Optional logger for debugging


class TableView:
    """Manages table virtualization, scrolling, and geometry calculations.

    Handles coordinate transformations, visible area calculations,
    and efficient rendering with buffered culling.
    """

    def __init__(
        self,
        canvas_width: int = 800,
        canvas_height: int = 600,
        buffer_cells: int = 2,
    ) -> None:
        """Initialize the table view.

        Args:
            canvas_width: Initial canvas width
            canvas_height: Initial canvas height
            buffer_cells: Number of extra cells to render beyond viewport
        """
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.buffer_cells = buffer_cells

        # Scroll positions (in pixels)
        self._scroll_x = 0.0
        self._scroll_y = 0.0

        # Cached geometry
        self._row_heights: List[int] = []
        self._col_widths: List[int] = []
        self._header_height = 30  # Fixed header height
        self._total_width = 0.0
        self._total_height = 0.0

        # Cached row positions (y-coordinates)
        self._row_positions: List[float] = []
        # Cached column positions (x-coordinates)
        self._col_positions: List[float] = []

    def update_geometry(
        self,
        data_provider: TableDataProvider,
        style_provider: TableStyleProvider,
    ) -> None:
        """Update cached geometry information.

        Args:
            data_provider: Source of row/column counts
            style_provider: Source of row heights and column widths
        """
        row_count = data_provider.get_row_count()
        col_count = data_provider.get_column_count()

        # Update row heights
        self._row_heights = []
        for row in range(row_count):
            # For now, use default height - could be customized per row
            height = style_provider.base_styles['default'].row_height
            self._row_heights.append(height)

        # Update column widths
        self._col_widths = []
        for col in range(col_count):
            # For now, use default width - could be customized per column
            width = style_provider.base_styles['default'].col_width
            self._col_widths.append(width)

        # Calculate cumulative positions
        self._update_positions()

    def _update_positions(self) -> None:
        """Update cached position arrays."""
        # Row positions (including header)
        self._row_positions = [self._header_height]  # Start after header
        for height in self._row_heights:
            next_pos = self._row_positions[-1] + height
            self._row_positions.append(next_pos)

        # Column positions
        self._col_positions = [0.0]
        for width in self._col_widths:
            next_pos = self._col_positions[-1] + width
            self._col_positions.append(next_pos)

        # Total dimensions
        self._total_width = self._col_positions[-1] if self._col_positions else 0.0
        self._total_height = self._row_positions[-1] if self._row_positions else 0.0

    def scroll_to(self, x: float, y: float) -> None:
        """Update scroll position.

        Args:
            x: Horizontal scroll position (pixels)
            y: Vertical scroll position (pixels)
        """
        # Clamp scroll positions to valid ranges
        max_scroll_x = max(0, self._total_width - self.canvas_width)
        max_scroll_y = max(0, self._total_height - self.canvas_height)

        self._scroll_x = max(0, min(x, max_scroll_x))
        self._scroll_y = max(0, min(y, max_scroll_y))

    def get_viewport_bounds(self) -> ViewportBounds:
        """Get the current viewport bounds in table coordinates.

        Returns:
            ViewportBounds with pixel coordinates
        """
        return ViewportBounds(
            left=self._scroll_x,
            top=self._scroll_y,
            right=self._scroll_x + self.canvas_width,
            bottom=self._scroll_y + self.canvas_height,
        )

    def get_visible_rows(self) -> Tuple[int, int]:
        """Get the range of visible rows (inclusive).

        Returns:
            Tuple of (first_visible_row, last_visible_row)
        """
        viewport = self.get_viewport_bounds()

        # Find first visible row (including buffer)
        first_row = 0
        for i, y_pos in enumerate(self._row_positions[:-1]):  # Exclude last position
            if y_pos >= viewport.top - (self.buffer_cells * self._row_heights[i] if i < len(self._row_heights) else 0):
                first_row = max(0, i - self.buffer_cells)
                break

        # Find last visible row (including buffer)
        last_row = len(self._row_heights) - 1
        for i in range(len(self._row_positions) - 1):
            if self._row_positions[i] > viewport.bottom + (self.buffer_cells * self._row_heights[i] if i < len(self._row_heights) else 0):
                last_row = min(len(self._row_heights) - 1, i + self.buffer_cells - 1)
                break

        return (first_row, last_row)

    def get_visible_cols(self) -> Tuple[int, int]:
        """Get the range of visible columns (inclusive).

        Returns:
            Tuple of (first_visible_col, last_visible_col)
        """
        viewport = self.get_viewport_bounds()

        # Find first visible column (including buffer)
        first_col = 0
        for i, x_pos in enumerate(self._col_positions[:-1]):  # Exclude last position
            if x_pos >= viewport.left - (self.buffer_cells * self._col_widths[i] if i < len(self._col_widths) else 0):
                first_col = max(0, i - self.buffer_cells)
                break

        # Find last visible column (including buffer)
        last_col = len(self._col_widths) - 1
        for i in range(len(self._col_positions) - 1):
            if self._col_positions[i] > viewport.right + (self.buffer_cells * self._col_widths[i] if i < len(self._col_widths) else 0):
                last_col = min(len(self._col_widths) - 1, i + self.buffer_cells - 1)
                break

        return (first_col, last_col)

    def get_coords_for_cell(self, row: int, col: int) -> Tuple[float, float, float, float]:
        """Get screen coordinates for a cell.

        Args:
            row: Row index (0-based)
            col: Column index (0-based)

        Returns:
            Tuple of (x1, y1, x2, y2) screen coordinates
        """
        if row < 0 or row >= len(self._row_heights) or col < 0 or col >= len(self._col_widths):
            return (0, 0, 0, 0)

        x1 = self._col_positions[col] - self._scroll_x
        y1 = self._row_positions[row] - self._scroll_y
        x2 = x1 + self._col_widths[col]
        y2 = y1 + self._row_heights[row]

        return (x1, y1, x2, y2)

    def get_coords_for_header(self, col: int) -> Tuple[float, float, float, float]:
        """Get screen coordinates for a header cell.

        Args:
            col: Column index (0-based)

        Returns:
            Tuple of (x1, y1, x2, y2) screen coordinates
        """
        if col < 0 or col >= len(self._col_widths):
            return (0, 0, 0, 0)

        x1 = self._col_positions[col] - self._scroll_x
        y1 = 0  # Headers start at top
        x2 = x1 + self._col_widths[col]
        y2 = y1 + self._header_height

        return (x1, y1, x2, y2)

    def get_cell_at_coords(self, x: float, y: float) -> Optional[Tuple[int, int]]:
        """Get the cell at the given screen coordinates.

        Args:
            x: Screen x coordinate
            y: Screen y coordinate

        Returns:
            Tuple of (row, col) or None if no cell at coordinates
        """
        # Convert to table coordinates
        table_x = x + self._scroll_x
        table_y = y + self._scroll_y

        # Check if in header area
        if table_y < self._header_height:
            # Find column
            for col in range(len(self._col_widths)):
                if self._col_positions[col] <= table_x < self._col_positions[col + 1]:
                    return (-1, col)  # -1 indicates header row
            return None

        # Find row
        row = -1
        for i in range(len(self._row_heights)):
            if self._row_positions[i] <= table_y < self._row_positions[i + 1]:
                row = i
                break

        if row == -1:
            return None

        # Find column
        col = -1
        for i in range(len(self._col_widths)):
            if self._col_positions[i] <= table_x < self._col_positions[i + 1]:
                col = i
                break

        if col == -1:
            return None

        return (row, col)

    def get_total_size(self) -> Tuple[float, float]:
        """Get the total table size.

        Returns:
            Tuple of (total_width, total_height)
        """
        return (self._total_width, self._total_height)

    def update_canvas_size(self, width: int, height: int) -> None:
        """Update the canvas dimensions.

        Args:
            width: New canvas width
            height: New canvas height
        """
        self.canvas_width = width
        self.canvas_height = height


class TablePainter:
    """Handles canvas drawing and efficient rendering with culling.

    Manages canvas items, draws cells and headers, and implements
    buffered viewport culling for performance.
    """

    def __init__(self) -> None:
        """Initialize the table painter."""
        self._canvas_item_ids: Dict[str, int] = {}
        self._formatter = CellValueFormatter()

    def redraw(self, context: RenderContext) -> None:
        """Redraw the visible portion of the table.

        Args:
            context: Rendering context with all dependencies
        """
        context.logger.debug("=" * 70)
        context.logger.debug("TablePainter.redraw() called")
        context.logger.debug("=" * 70)
        
        # Clear existing items
        context.logger.debug(f"Clearing {len(self._canvas_item_ids)} existing canvas items")
        for item_id in self._canvas_item_ids.values():
            context.canvas.delete(item_id)
        self._canvas_item_ids.clear()

        # Get visible ranges
        first_row, last_row = context.view.get_visible_rows()
        first_col, last_col = context.view.get_visible_cols()
        context.logger.debug(f"Visible ranges: rows=({first_row}, {last_row}), cols=({first_col}, {last_col})")

        # Draw headers
        context.logger.debug("Drawing headers...")
        self._draw_headers(context, first_col, last_col)

        # Draw cells
        context.logger.debug("Drawing cells...")
        self._draw_cells(context, first_row, last_row, first_col, last_col)

        # Update canvas scroll region
        total_width, total_height = context.view.get_total_size()
        context.logger.debug(f"Setting scroll region to ({total_width}, {total_height})")
        context.canvas.configure(scrollregion=(0, 0, total_width, total_height))
        
        context.logger.debug(f"Redraw complete. Created {len(self._canvas_item_ids)} canvas items")
        context.logger.debug("=" * 70)

    def _draw_headers(
        self,
        context: RenderContext,
        first_col: int,
        last_col: int,
    ) -> None:
        """Draw header cells.

        Args:
            context: Rendering context with all dependencies
            first_col: First visible column
            last_col: Last visible column
        """
        headers = context.data_provider.get_column_headers()
        context.logger.debug(f"_draw_headers: headers={headers}, first_col={first_col}, last_col={last_col}")

        for col in range(max(0, first_col), min(len(headers), last_col + 1)):
            x1, y1, x2, y2 = context.view.get_coords_for_header(col)
            context.logger.debug(f"  Drawing header col={col} at coords=({x1}, {y1}, {x2}, {y2})")

            # Get header style - check for override first
            if (-1, col) in context.style_provider.style_overrides:
                style = context.style_provider.style_overrides[(-1, col)]
            else:
                style = context.style_provider.base_styles.get('header', context.style_provider.base_styles['default'])

            # Draw background
            bg_id = context.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=style.bg_color,
                outline=style.borders.get('right', ('', ''))[1] if 'right' in style.borders else '',
                width=style.borders.get('right', (1, ''))[0] if 'right' in style.borders else 1,
                tags=('header', f'header_{col}')
            )
            self._canvas_item_ids[f'header_bg_{col}'] = bg_id

            # Draw header text
            header_text = headers[col] if col < len(headers) else f'Col {col}'
            text_id = context.canvas.create_text(
                x1 + (x2 - x1) // 2, y1 + (y2 - y1) // 2,
                text=header_text,
                font=style.font,
                fill=style.text_color,
                anchor='center',
                tags=('header', f'header_{col}')
            )
            self._canvas_item_ids[f'header_text_{col}'] = text_id
            
            # Draw bottom border if specified
            if 'bottom' in style.borders:
                border_width, border_color = style.borders['bottom']
                if border_width > 0 and border_color:
                    border_id = context.canvas.create_line(
                        x1, y2, x2, y2,
                        fill=border_color,
                        width=border_width,
                        tags=('header', f'header_{col}')
                    )
                    self._canvas_item_ids[f'header_border_bottom_{col}'] = border_id

    def _draw_cells(
        self,
        context: RenderContext,
        first_row: int,
        last_row: int,
        first_col: int,
        last_col: int,
    ) -> None:
        """Draw data cells.

        Args:
            context: Rendering context with all dependencies
            first_row: First visible row
            last_row: Last visible row
            first_col: First visible column
            last_col: Last visible column
        """
        row_count = context.data_provider.get_row_count()
        col_count = context.data_provider.get_column_count()
        context.logger.debug(f"_draw_cells: row_count={row_count}, col_count={col_count}")
        context.logger.debug(f"  first_row={first_row}, last_row={last_row}, first_col={first_col}, last_col={last_col}")
        
        for row in range(max(0, first_row), min(row_count, last_row + 1)):
            # Check if this row has column spanning (category header)
            first_col_style = context.style_provider.get_effective_style(row, 0, False)
            row_spans_columns = first_col_style.span_columns if first_col_style else False
            
            for col in range(max(0, first_col), min(col_count, last_col + 1)):
                # Skip drawing columns > 0 if row spans columns
                if row_spans_columns and col > 0:
                    continue
                    
                x1, y1, x2, y2 = context.view.get_coords_for_cell(row, col)
                context.logger.debug(f"  Drawing cell ({row},{col}) at coords=({x1}, {y1}, {x2}, {y2})")

                # Check if cell is selected
                is_selected = context.selection_model.is_selected(row, col)

                # Get cell style
                style = context.style_provider.get_effective_style(row, col, is_selected)

                # Handle column spanning (for category headers)
                if style.span_columns and col == 0:
                    # Span across all columns - get coordinates from first to last column
                    _, _, x2_last, _ = context.view.get_coords_for_cell(row, col_count - 1)
                    x2 = x2_last
                
                # Draw background
                bg_id = context.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=style.bg_color,
                    outline=style.borders.get('right', ('', ''))[1] if 'right' in style.borders else '',
                    width=style.borders.get('right', (1, ''))[0] if 'right' in style.borders else 1,
                    tags=('cell', f'cell_{row}_{col}')
                )
                self._canvas_item_ids[f'cell_bg_{row}_{col}'] = bg_id

                # Draw cell text
                try:
                    value = context.data_provider.get_value(row, col)
                    display_text = self._formatter.format(value)
                except Exception:
                    display_text = "#ERROR#"

                # Handle text justification with 5px padding
                text_x = x1
                text_y = y1 + (y2 - y1) // 2

                if style.horiz_justify == 'center':
                    text_x = x1 + (x2 - x1) // 2
                    anchor = 'center'
                elif style.horiz_justify == 'e':
                    text_x = x2 - 5  # 5px right margin
                    anchor = 'e'
                else:  # 'w' or default
                    text_x = x1 + 5  # 5px left margin
                    anchor = 'w'

                text_id = context.canvas.create_text(
                    text_x, text_y,
                    text=display_text,
                    font=style.font,
                    fill=style.text_color,
                    anchor=anchor,
                    tags=('cell', f'cell_{row}_{col}')
                )
                self._canvas_item_ids[f'cell_text_{row}_{col}'] = text_id
                
                # Draw top border if specified
                if 'top' in style.borders:
                    border_width, border_color = style.borders['top']
                    if border_width > 0 and border_color:
                        border_id = context.canvas.create_line(
                            x1, y1, x2, y1,
                            fill=border_color,
                            width=border_width,
                            tags=('cell', f'cell_{row}_{col}')
                        )
                        self._canvas_item_ids[f'cell_border_top_{row}_{col}'] = border_id
                
                # Draw bottom border if specified
                # Draw it slightly above the cell bottom so next row's background doesn't cover it
                if 'bottom' in style.borders:
                    border_width, border_color = style.borders['bottom']
                    context.logger.debug(f"  Cell ({row},{col}) has bottom border: width={border_width}, color={border_color}")
                    if border_width > 0 and border_color:
                        # Draw border 1 pixel above the cell bottom to prevent overlap
                        border_y = y2 - 1
                        border_id = context.canvas.create_line(
                            x1, border_y, x2, border_y,
                            fill=border_color,
                            width=border_width,
                            tags=('cell', f'cell_{row}_{col}')
                        )
                        self._canvas_item_ids[f'cell_border_bottom_{row}_{col}'] = border_id
                        context.logger.debug(f"  Drew bottom border for cell ({row},{col}) at y={border_y}")
