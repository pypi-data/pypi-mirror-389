"""Main widget classes for Tabula Mutabilis table widget.

This module provides the primary user-facing components:
- TabulaMutabilis: The main table widget
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from vultus_serpentis import EventBus

from .controllers import SelectionModel, TableController
from .model import InMemoryDataProvider, TableDataProvider
from .styles import TableStyleProvider
from .views import RenderContext, TablePainter, TableView


class TabulaMutabilis(ttk.Frame):
    """The main table widget for Tkinter applications.

    A comprehensive table widget with TTK Bootstrap integration,
    virtual scrolling, cell editing, and undo/redo support.
    """

    def __init__(
        self,
        parent,
        data_provider: Optional[TableDataProvider] = None,
        vs_event_bus: Optional[EventBus] = None,
        logger=None,
        **kwargs
    ) -> None:
        """Initialize the table widget.

        Args:
            parent: Parent widget
            data_provider: Optional data provider (creates InMemoryDataProvider if None)
            vs_event_bus: Optional Vultus Serpentis event bus
            logger: Optional logger instance
            **kwargs: Additional Frame options
        """
        # Extract data_provider from kwargs if it was passed as keyword argument
        # This is needed because ttk.Frame also accepts **kwargs
        print(f"DEBUG TabulaMutabilis.__init__: BEFORE - data_provider param = {type(data_provider).__name__ if data_provider else 'None'}")
        print(f"DEBUG TabulaMutabilis.__init__: BEFORE - kwargs = {kwargs}")
        if 'data_provider' in kwargs:
            print(f"DEBUG: Found data_provider in kwargs!")
            data_provider = kwargs.pop('data_provider')
        
        print(f"DEBUG TabulaMutabilis.__init__: AFTER - parent={type(parent).__name__}, data_provider={type(data_provider).__name__ if data_provider else 'None'}")
        print(f"DEBUG TabulaMutabilis.__init__: AFTER - kwargs={kwargs}")
        super().__init__(parent, **kwargs)

        # Store references
        self.logger = logger or self._get_default_logger()
        self.vs_event_bus = vs_event_bus or EventBus.default()

        # Query TTK Bootstrap theme
        self.style = ttk.Style(self)
        theme_colors, theme_fonts = self._query_theme()

        # Create components
        print(f"DEBUG TabulaMutabilis.__init__: data_provider argument = {type(data_provider).__name__ if data_provider else 'None'}")
        self.data_provider = data_provider or InMemoryDataProvider()
        print(f"DEBUG TabulaMutabilis.__init__: self.data_provider = {type(self.data_provider).__name__}")
        self.style_provider = TableStyleProvider(theme_colors, theme_fonts)
        self.selection_model = SelectionModel()
        self.view = TableView()
        self.painter = TablePainter()

        # Create command manager (using VS default)
        from vultus_serpentis import CommandManager
        self.command_manager = CommandManager.default()

        # Create controller
        self.controller = TableController(
            canvas=None,  # Will set after creating canvas
            view=self.view,
            data_provider=self.data_provider,
            style_provider=self.style_provider,
            selection_model=self.selection_model,
            command_manager=self.command_manager,
            logger=self.logger
        )

        # Create UI
        self._create_ui()

        # Connect controller to canvas
        self.controller.canvas = self.canvas

        # Set up theme change monitoring
        self._setup_theme_monitoring()

        # Initial geometry update and redraw
        self._update_geometry()
        self._redraw()

    def _get_default_logger(self):
        """Get a default logger instance."""
        import logging
        logger = logging.getLogger('TabulaMutabilis')
        if not logger.handlers:
            logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed diagnostics
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def _query_theme(self) -> tuple[dict[str, str], dict[str, str]]:
        """Query the current TTK Bootstrap theme for colors and fonts.

        Returns:
            Tuple of (theme_colors, theme_fonts) dictionaries
        """
        theme_colors = {}
        theme_fonts = {}

        # Query colors
        try:
            theme_colors['fg'] = self.style.lookup('.', 'foreground') or '#000000'
            theme_colors['bg'] = self.style.lookup('.', 'background') or '#FFFFFF'
            theme_colors['primary'] = self.style.lookup('TButton', 'background', ['pressed']) or '#0078D4'
            theme_colors['primary_fg'] = '#FFFFFF'  # Usually white for dark buttons
            theme_colors['secondary'] = self.style.lookup('TFrame', 'background') or '#F3F2F1'
        except Exception:
            # Fallback colors
            theme_colors = {
                'fg': '#000000',
                'bg': '#FFFFFF',
                'primary': '#0078D4',
                'primary_fg': '#FFFFFF',
                'secondary': '#F3F2F1'
            }

        # Query fonts
        try:
            theme_fonts['body'] = self.style.lookup('TLabel', 'font') or ('TkDefaultFont', 10)
            theme_fonts['header'] = self.style.lookup('TLabel', 'font') or ('TkDefaultFont', 10, 'bold')
        except Exception:
            # Fallback fonts
            theme_fonts = {
                'body': ('TkDefaultFont', 10),
                'header': ('TkDefaultFont', 10, 'bold')
            }

        return theme_colors, theme_fonts

    def _create_ui(self) -> None:
        """Create the user interface components."""
        # Create main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create canvas
        self.canvas = tk.Canvas(
            self.main_frame,
            bg=self.style_provider.theme_colors.get('bg', '#FFFFFF'),
            highlightthickness=0
        )

        # Create scrollbars
        self.v_scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self._on_vscroll)
        self.h_scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.HORIZONTAL, command=self._on_hscroll)

        # Layout with scrollbars
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW)
        self.v_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self.h_scrollbar.grid(row=1, column=0, sticky=tk.EW)

        # Configure grid weights
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Connect canvas to scrollbars
        self.canvas.configure(
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set
        )

        # Bind canvas events
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.bind('<Button-1>', self.controller.on_click)
        self.canvas.bind('<B1-Motion>', self.controller.on_drag)
        self.canvas.bind('<Double-Button-1>', self.controller.on_double_click)
        self.canvas.bind('<<RedrawTable>>', lambda e: self._redraw())

        # Bind mouse wheel for scrolling
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)

    def _setup_theme_monitoring(self) -> None:
        """Set up monitoring for theme changes."""
        # TTK Bootstrap doesn't have built-in theme change events,
        # so we'll rely on manual theme updates via update_theme()
        pass

    def update_theme(self) -> None:
        """Update the widget when theme changes."""
        theme_colors, theme_fonts = self._query_theme()
        self.style_provider.update_theme(theme_colors, theme_fonts)

        # Update canvas background
        self.canvas.configure(bg=theme_colors.get('bg', '#FFFFFF'))

        # Trigger redraw
        self._redraw()

    def _on_canvas_configure(self, event) -> None:
        """Handle canvas resize events."""
        self.view.update_canvas_size(event.width, event.height)
        self._redraw()

    def _on_vscroll(self, action, position, unit=None) -> None:
        """Handle vertical scrolling."""
        if action == 'moveto':
            total_height = self.view.get_total_size()[1]
            if total_height > 0:
                scroll_y = float(position) * total_height
                self.view.scroll_to(self.view._scroll_x, scroll_y)
                self._redraw()

    def _on_hscroll(self, action, position, unit=None) -> None:
        """Handle horizontal scrolling."""
        if action == 'moveto':
            total_width = self.view.get_total_size()[0]
            if total_width > 0:
                scroll_x = float(position) * total_width
                self.view.scroll_to(scroll_x, self.view._scroll_y)
                self._redraw()

    def _on_mousewheel(self, event) -> None:
        """Handle mouse wheel scrolling."""
        # Scroll vertically
        scroll_amount = -event.delta // 120 * 20  # 20 pixels per wheel click
        new_scroll_y = self.view._scroll_y + scroll_amount
        self.view.scroll_to(self.view._scroll_x, new_scroll_y)
        self._redraw()

    def _update_geometry(self) -> None:
        """Update view geometry."""
        self.view.update_geometry(self.data_provider, self.style_provider)

    def _redraw(self) -> None:
        """Redraw the table."""
        context = RenderContext(
            canvas=self.canvas,
            view=self.view,
            data_provider=self.data_provider,
            style_provider=self.style_provider,
            selection_model=self.selection_model,
            logger=self.logger
        )
        self.painter.redraw(context)

    # Public API methods

    @property
    def undo_action(self):
        """Get the undo action for integration with menus/toolbars."""
        return self.controller.undo_action

    @property
    def redo_action(self):
        """Get the redo action for integration with menus/toolbars."""
        return self.controller.redo_action

    def set_data(self, data: list[list], headers: Optional[list[str]] = None) -> None:
        """Set table data.

        Args:
            data: List of rows, where each row is a list of values
            headers: Optional column headers
        """
        if isinstance(self.data_provider, InMemoryDataProvider):
            if headers:
                self.data_provider.set_column_headers(headers)
            # Clear existing data
            while self.data_provider.get_row_count() > 0:
                self.data_provider.delete_row(0)
            # Add new data
            for row_data in data:
                self.data_provider.insert_row(self.data_provider.get_row_count(), row_data)

            self._update_geometry()
            self._redraw()

    def get_selected_cell(self) -> Optional[tuple[int, int]]:
        """Get the currently selected cell.

        Returns:
            Tuple of (row, col) or None if no selection
        """
        # SelectionModel would need a method to get current selection
        # For now, return None
        return None

    def scroll_to_cell(self, row: int, col: int) -> None:
        """Scroll to make a cell visible.

        Args:
            row: Row index
            col: Column index
        """
        x1, y1, x2, y2 = self.view.get_coords_for_cell(row, col)
        # Center the cell in the viewport
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        viewport_width = self.view.canvas_width
        viewport_height = self.view.canvas_height

        scroll_x = center_x - viewport_width / 2
        scroll_y = center_y - viewport_height / 2

        self.view.scroll_to(scroll_x, scroll_y)
        self._redraw()

    def clear_selection(self) -> None:
        """Clear all cell selections."""
        self.selection_model.clear()
        self._redraw()

    def refresh(self) -> None:
        """Force a complete refresh of the table."""
        print(f"DEBUG TabulaMutabilis.refresh(): data_provider={type(self.data_provider).__name__}, row_count={self.data_provider.get_row_count()}")
        self._update_geometry()
        self._redraw()
