"""Controller components for Tabula Mutabilis table widget.

This module provides the interaction logic:
- SelectionModel: Manages cell selection state
- SetValueCommand: Undoable cell value changes
- TableController: Coordinates user interactions
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional
import tkinter as tk
from vultus_serpentis import Action, Command, CommandManager, Observable

if TYPE_CHECKING:
    from .model import TableDataProvider
    from .styles import TableStyleProvider
    from .views import TablePainter, TableView


class SelectionModel(Observable):
    """Manages table cell selection state.

    Tracks which cells are currently selected and notifies observers
    of selection changes.
    """

    def __init__(self) -> None:
        """Initialize the selection model."""
        super().__init__()
        self._selected_cells: List[tuple[int, int]] = []

    def select(self, row: int, col: int, mode: str = 'single') -> None:
        """Update the selection.

        Args:
            row: Row index
            col: Column index
            mode: Selection mode ('single', 'multi', 'range')
        """
        if mode == 'single':
            self._selected_cells = [(row, col)]
        elif mode == 'multi':
            if (row, col) not in self._selected_cells:
                self._selected_cells.append((row, col))
            else:
                self._selected_cells.remove((row, col))
        elif mode == 'range':
            # For simplicity, treat range as single for now
            self._selected_cells = [(row, col)]

        self._notify_observers(
            event_type='selection_changed',
            payload={'selected_cells': self._selected_cells.copy()}
        )

    def clear(self) -> None:
        """Clear all selections."""
        if self._selected_cells:
            self._selected_cells.clear()
            self._notify_observers(
                event_type='selection_changed',
                payload={'selected_cells': []}
            )

    def is_selected(self, row: int, col: int) -> bool:
        """Check if a cell is selected.

        Args:
            row: Row index
            col: Column index

        Returns:
            True if the cell is selected
        """
        return (row, col) in self._selected_cells

    def get_selected_cells(self) -> List[tuple[int, int]]:
        """Get all selected cells.

        Returns:
            List of (row, col) tuples
        """
        return self._selected_cells.copy()

    def get_current_selection(self) -> Optional[tuple[int, int]]:
        """Get the current/last selected cell.

        Returns:
            Tuple of (row, col) or None if no selection
        """
        return self._selected_cells[-1] if self._selected_cells else None


class SetValueCommand(Command):
    """Undoable command for setting cell values."""

    def __init__(
        self,
        data_provider: TableDataProvider,
        row: int,
        col: int,
        new_value
    ) -> None:
        """Initialize the command.

        Args:
            data_provider: The data provider to modify
            row: Row index
            col: Column index
            new_value: The new cell value
        """
        self.data_provider = data_provider
        self.row = row
        self.col = col
        self.new_value = new_value
        self.old_value = data_provider.get_value(row, col)

    def execute(self) -> bool:
        """Execute the command (set the new value).

        Returns:
            True if successful
        """
        self.data_provider.set_value(self.row, self.col, self.new_value)
        return True

    def undo(self) -> bool:
        """Undo the command (restore the old value).

        Returns:
            True if successful
        """
        self.data_provider.set_value(self.row, self.col, self.old_value)
        return True


class InsertRowCommand(Command):
    """Undoable command for inserting rows."""

    def __init__(
        self,
        data_provider: TableDataProvider,
        index: int,
        data: list
    ) -> None:
        """Initialize the command.

        Args:
            data_provider: The data provider to modify
            index: Index where row should be inserted
            data: The row data to insert
        """
        self.data_provider = data_provider
        self.index = index
        self.data = data

    def execute(self) -> bool:
        """Execute the command (insert the row).

        Returns:
            True if successful
        """
        self.data_provider.insert_row(self.index, self.data)
        return True

    def undo(self) -> bool:
        """Undo the command (delete the inserted row).

        Returns:
            True if successful
        """
        self.data_provider.delete_row(self.index)
        return True


class TableController:
    """Coordinates user interactions with the table.

    Handles mouse events, cell editing, and coordinates between
    all table components.
    """

    def __init__(
        self,
        canvas: Optional[tk.Canvas],
        view: TableView,
        data_provider: TableDataProvider,
        style_provider: TableStyleProvider,
        selection_model: SelectionModel,
        command_manager: CommandManager,
        logger
    ) -> None:
        """Initialize the table controller.

        Args:
            canvas: The table canvas
            view: The table view
            data_provider: The data provider
            style_provider: The style provider
            selection_model: The selection model
            command_manager: The command manager for undo/redo
            logger: Logger instance
        """
        self.canvas = canvas
        self.view = view
        self.data_provider = data_provider
        self.style_provider = style_provider
        self.selection_model = selection_model
        self.command_manager = command_manager
        self.logger = logger
        self._last_click_cell: Optional[tuple[int, int]] = None
        self.window_selection_enabled = False  # Window selection mode flag
        # VS Actions for external integration
        self.undo_action = Action(
            text="Undo",
            command=self.command_manager.undo,
            enabled=self.command_manager.can_undo()
        )
        self.redo_action = Action(
            text="Redo",
            command=self.command_manager.redo,
            enabled=self.command_manager.can_redo()
        )

        # State for drag operations
        self._drag_start_cell: Optional[tuple[int, int]] = None
        self._last_click_cell: Optional[tuple[int, int]] = None

        # Set up observer subscriptions
        self._setup_observers()

    def _setup_observers(self) -> None:
        """Set up observer subscriptions to model changes."""
        self.data_provider.add_observer(self._on_model_changed)
        self.style_provider.add_observer(self._on_model_changed)
        self.selection_model.add_observer(self._on_model_changed)
        self.command_manager.stack.add_observer(self._on_command_stack_changed)

    def _on_model_changed(self, **kwargs) -> None:
        """Handle model change notifications."""
        event_type = kwargs.get('event_type', 'unknown')
        self.logger.debug(f"Controller: Model changed - {event_type}")

        # Trigger redraw for events that affect display
        if event_type in ['selection_changed', 'data_sorted', 'data_changed', 
                          'row_inserted', 'row_deleted', 'column_inserted', 
                          'column_deleted', 'headers_changed']:
            self.logger.debug(f"Triggering redraw for {event_type}")
            self._trigger_redraw()

    def _on_command_stack_changed(self, **kwargs) -> None:
        """Handle command stack changes (for undo/redo actions)."""
        self.undo_action.enabled = self.command_manager.can_undo()
        self.redo_action.enabled = self.command_manager.can_redo()

        # Trigger redraw after command execution
        self._trigger_redraw()

    def _trigger_redraw(self) -> None:
        """Request a redraw from the canvas."""
        if self.canvas:
            # Post an event to trigger redraw
            self.canvas.event_generate('<<RedrawTable>>')

    def on_click(self, event) -> None:
        """Handle mouse click events.

        Args:
            event: Tkinter event
        """
        cell = self.view.get_cell_at_coords(event.x, event.y)
        if cell:
            row, col = cell
            if row >= 0:  # Not a header click
                self.logger.debug(f"Click on cell ({row}, {col})")
                
                # Check for shift key (range selection)
                if event.state & 0x0001:  # Shift key
                    if self._last_click_cell:
                        self._select_range(self._last_click_cell, (row, col))
                    else:
                        self.selection_model.select(row, col, mode='single')
                        self._last_click_cell = (row, col)
                # Check for ctrl key (multi-selection)
                elif event.state & 0x0004:  # Ctrl key
                    self.selection_model.select(row, col, mode='multi')
                    self._last_click_cell = (row, col)
                else:
                    # Single selection
                    self.selection_model.select(row, col, mode='single')
                    self._last_click_cell = (row, col)
                
                self._drag_start_cell = (row, col)

    def on_drag(self, event) -> None:
        """Handle mouse drag events for range selection.

        Args:
            event: Tkinter event
        """
        # Only allow window selection if mode is enabled
        if not self.window_selection_enabled:
            return
            
        if self._drag_start_cell is None:
            return

        cell = self.view.get_cell_at_coords(event.x, event.y)
        if cell:
            row, col = cell
            if row >= 0:  # Not a header
                self.logger.debug(f"Drag to cell ({row}, {col})")
                # Select range from drag start to current cell
                self._select_range(self._drag_start_cell, (row, col))

    def _select_range(self, start_cell: tuple[int, int], end_cell: tuple[int, int]) -> None:
        """Select a rectangular range of cells.

        Args:
            start_cell: Starting (row, col)
            end_cell: Ending (row, col)
        """
        start_row, start_col = start_cell
        end_row, end_col = end_cell
        
        # Determine bounds
        min_row = min(start_row, end_row)
        max_row = max(start_row, end_row)
        min_col = min(start_col, end_col)
        max_col = max(start_col, end_col)
        
        # Clear and select range
        self.selection_model.clear()
        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                self.selection_model.select(row, col, mode='multi')

    def on_double_click(self, event) -> None:
        """Handle double-click events for cell editing or column sorting.

        Args:
            event: Tkinter event
        """
        self.logger.info(f"Double-click event at coordinates ({event.x}, {event.y})")
        cell = self.view.get_cell_at_coords(event.x, event.y)
        self.logger.info(f"Cell at coords: {cell}")
        
        if cell:
            row, col = cell
            if row >= 0:  # Not a header - edit cell
                self.logger.info(f"Double-click on data cell ({row}, {col}) - starting edit")
                self._start_cell_editing(row, col)
            else:  # Header - sort column
                self.logger.info(f"Double-click on header column {col} - sorting")
                self._sort_by_column(col)

    def _start_cell_editing(self, row: int, col: int) -> None:
        """Start editing a cell.

        Args:
            row: Row index
            col: Column index
        """
        self.logger.info(f"=== Starting cell edit for ({row}, {col}) ===")
        
        # Get the effective style for the cell
        style = self.style_provider.get_effective_style(row, col, self.selection_model.is_selected(row, col))
        self.logger.debug(f"Got effective style: {style}")

        # Check if cell has an editor
        editor_class = style.cell_editor_class
        self.logger.info(f"Editor class for cell ({row}, {col}): {editor_class}")
        
        if editor_class is None:
            self.logger.warning(f"No editor defined for cell ({row}, {col}) - cannot edit")
            return

        # Get current value
        try:
            current_value = self.data_provider.get_value(row, col)
            self.logger.info(f"Current value: {current_value!r}")
        except Exception as e:
            self.logger.error(f"Error getting value for cell ({row}, {col}): {e}", exc_info=True)
            return

        # Create and show editor
        try:
            self.logger.debug(f"Creating editor instance: {editor_class}")
            editor = editor_class()
            
            self.logger.debug(f"Canvas: {self.canvas}")
            if self.canvas:
                toplevel = self.canvas.winfo_toplevel()
                self.logger.debug(f"Toplevel window: {toplevel}")
                
                self.logger.info(f"Showing modal editor with value: {current_value!r}")
                new_value = editor.show_modal(toplevel, current_value)
                self.logger.info(f"Editor returned value: {new_value!r}")

                # If user confirmed and value changed, create command
                if new_value is not None and new_value != current_value:
                    self.logger.info(f"Value changed from {current_value!r} to {new_value!r}, creating command")
                    command = SetValueCommand(self.data_provider, row, col, new_value)
                    self.command_manager.execute(command)
                    self.logger.info(f"Cell ({row}, {col}) updated successfully")
                else:
                    self.logger.info(f"Edit cancelled or value unchanged")
            else:
                self.logger.error("Canvas is None - cannot get toplevel window")
        except Exception as e:
            self.logger.error(f"Error editing cell ({row}, {col}): {e}", exc_info=True)

    def get_cell_at_coords(self, x: int, y: int) -> Optional[tuple[int, int]]:
        """Get the cell at the given coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Tuple of (row, col) or None
        """
        return self.view.get_cell_at_coords(x, y)

    def select_cell(self, row: int, col: int, mode: str = 'single') -> None:
        """Programmatically select a cell.

        Args:
            row: Row index
            col: Column index
            mode: Selection mode
        """
        self.selection_model.select(row, col, mode)

    def clear_selection(self) -> None:
        """Clear all selections."""
        self.selection_model.clear()

    def undo(self) -> None:
        """Undo the last action."""
        if self.command_manager.can_undo():
            self.command_manager.undo()

    def redo(self) -> None:
        """Redo the last undone action."""
        if self.command_manager.can_redo():
            self.command_manager.redo()

    def _sort_by_column(self, col: int) -> None:
        """Sort the table by the specified column.

        Toggles between ascending and descending order on repeated clicks.

        Args:
            col: Column index to sort by
        """
        # Track last sorted column and direction
        if not hasattr(self, '_last_sort_col'):
            self._last_sort_col = None
            self._last_sort_reverse = False

        # Toggle sort direction if same column
        if self._last_sort_col == col:
            self._last_sort_reverse = not self._last_sort_reverse
        else:
            self._last_sort_col = col
            self._last_sort_reverse = False

        # Check if data provider supports sorting
        if hasattr(self.data_provider, 'sort_by_column'):
            direction = "descending" if self._last_sort_reverse else "ascending"
            self.logger.info(f"Sorting by column {col} ({direction})")
            self.data_provider.sort_by_column(col, reverse=self._last_sort_reverse)
        else:
            self.logger.warning(f"Data provider does not support sorting")
