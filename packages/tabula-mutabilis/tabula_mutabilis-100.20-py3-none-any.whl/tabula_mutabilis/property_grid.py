"""Property grid module for tabula_mutabilis.

Provides a two-column property editor widget with:
- Left column: Property names (read-only)
- Right column: Property values (editable/non-editable)
- Non-editable properties have gray background
- Type-aware editor assignment
- Property change notifications
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Type, Callable, List, Union

# Import Observable from vultus_serpentis
try:
    # Try relative import for when used as part of package
    from ..vultus_serpentis.common import Observable
except ImportError:
    # Fallback for direct execution/testing
    import sys
    import os
    local_packages = os.path.join(os.path.dirname(__file__), '..', '..', 'Local Packages')
    if local_packages not in sys.path:
        sys.path.insert(0, local_packages)
    from vultus_serpentis.common import Observable

# Import TabulaMutabilis at module level to avoid import issues
from .widgets import TabulaMutabilis


@dataclass
class Property:
    """Represents a single property in the grid.

    A property has a name (displayed in left column) and value (displayed in right column).
    Properties can be editable or read-only, with optional validation and custom editors.
    """

    # Core attributes
    name: str                           # Display name (left column)
    value: Any                          # Current value (right column)
    editable: bool = True               # Can user edit?

    # Optional attributes
    property_type: Optional[Type] = None  # int, str, bool, etc.
    editor: Optional[Any] = None        # Custom editor instance
    validator: Optional[Callable] = None  # Validation function
    default_value: Any = None           # For reset functionality

    # Metadata
    category: Optional[str] = None      # Group name
    description: Optional[str] = None   # Tooltip/help text
    display_format: Optional[str] = None  # For formatting display

    # Internal
    _observers: List[Callable] = field(default_factory=list)

    def set_value(self, new_value):
        """Set value with validation and notification."""
        if not self.editable:
            raise ValueError(f"Property '{self.name}' is not editable")

        if self.validator and not self.validator(new_value):
            raise ValueError(f"Invalid value for '{self.name}'")

        old_value = self.value
        self.value = new_value
        self._notify_observers(old_value, new_value)

    def reset_to_default(self):
        """Reset to default value."""
        if self.default_value is not None:
            self.set_value(self.default_value)

    def add_observer(self, observer: Callable):
        """Add observer for property changes."""
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: Callable):
        """Remove observer."""
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_observers(self, old_value, new_value):
        """Notify all observers of value change."""
        for observer in self._observers:
            observer(self, old_value, new_value)


@dataclass
class PropertyCategory:
    """Groups related properties together.

    Categories allow logical grouping of properties (e.g., "General", "Appearance", "Layout").
    Categories can be expanded/collapsed in future enhancements.
    """

    name: str                           # Category display name
    properties: List[Property] = field(default_factory=list)
    expanded: bool = True               # Collapsed/expanded state (future use)
    style: Optional[Any] = None         # Category header style (future use)

    def add_property(self, prop: Property):
        """Add property to this category."""
        prop.category = self.name
        self.properties.append(prop)

    def get_property(self, name: str) -> Optional[Property]:
        """Get property by name within this category."""
        return next((p for p in self.properties if p.name == name), None)

    def remove_property(self, name: str):
        """Remove property from this category."""
        self.properties = [p for p in self.properties if p.name != name]


class PropertyGridDataProvider:
    """Data provider for property grid.

    Manages properties and categories, implementing the TableDataProvider interface.
    Handles property CRUD operations and formatting for display.
    
    Note: This implements the TableDataProvider interface but uses a custom
    internal structure optimized for property grids.
    """

    def __init__(self):
        # Observable pattern
        self._observers: List[Callable] = []
        
        # Property storage
        self._properties: List[Property] = []
        self._categories: dict[str, PropertyCategory] = {}
        self._flat_list: List[Union[PropertyCategory, Property]] = []
        self._use_categories: bool = False
        
        # Initialize flat list
        self._rebuild_flat_list()
    
    # Observable pattern methods
    def add_observer(self, observer: Callable) -> None:
        """Add an observer for change notifications."""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer: Callable) -> None:
        """Remove an observer."""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, *args, **kwargs) -> None:
        """Notify all observers of changes."""
        for observer in self._observers[:]:
            observer(*args, **kwargs)

    # TableDataProvider interface
    def get_row_count(self) -> int:
        count = len(self._flat_list)
        print(f"DEBUG PropertyGridDataProvider.get_row_count() called: returning {count}")
        print(f"  _flat_list: {[type(item).__name__ for item in self._flat_list]}")
        return count

    def get_column_count(self) -> int:
        return 2  # Name and Value columns

    def get_column_name(self, col: int) -> str:
        return "Property" if col == 0 else "Value"
    
    def get_column_headers(self) -> list[str]:
        """Return column headers."""
        return ["Property", "Value"]
    
    def set_column_headers(self, headers: list[str]) -> None:
        """Set column headers (not supported for property grid)."""
        pass  # Property grid has fixed headers

    def get_value(self, row: int, col: int) -> str:
        item = self._flat_list[row]
        if isinstance(item, PropertyCategory):
            return item.name if col == 0 else ""
        else:  # Property
            if col == 0:
                return item.name + ":"  # Add colon after property name
            else:
                return self._format_value(item)

    def set_value(self, row: int, col: int, value: str):
        if col != 1:
            return  # Only value column is editable

        item = self._flat_list[row]
        if isinstance(item, Property):
            item.set_value(value)
            self._notify_observers("property_changed", item)

    # Property management
    def add_property(self, name: str, value: Any, **kwargs) -> Property:
        """Add a property to the grid."""
        prop = Property(name=name, value=value, **kwargs)
        self._properties.append(prop)
        self._rebuild_flat_list()
        self._notify_observers("property_added", prop)
        return prop

    def add_category(self, name: str) -> PropertyCategory:
        """Add a property category."""
        category = PropertyCategory(name=name)
        self._categories[name] = category
        self._use_categories = True
        # Don't rebuild here - wait until properties are added
        # self._rebuild_flat_list()
        return category

    def get_property(self, name: str) -> Optional[Property]:
        """Get property by name."""
        return next((p for p in self._properties if p.name == name), None)

    def remove_property(self, name: str):
        """Remove a property."""
        self._properties = [p for p in self._properties if p.name != name]
        self._rebuild_flat_list()
        self._notify_observers("property_removed", name)

    def clear(self):
        """Remove all properties and categories."""
        print(f"DEBUG PropertyGridDataProvider.clear() called!")
        import traceback
        traceback.print_stack()
        self._properties.clear()
        self._categories.clear()
        self._flat_list.clear()
        self._use_categories = False

    def _rebuild_flat_list(self):
        """Rebuild flat list for rendering."""
        self._flat_list.clear()

        if self._use_categories:
            print(f"DEBUG PropertyGrid: Rebuilding with categories (use_categories={self._use_categories})")
            print(f"DEBUG PropertyGrid: Number of categories: {len(self._categories)}")
            for category in self._categories.values():
                print(f"DEBUG PropertyGrid:   Category '{category.name}': expanded={category.expanded}, {len(category.properties)} properties")
                if category.expanded:
                    self._flat_list.append(category)
                    self._flat_list.extend(category.properties)
                    print(f"DEBUG PropertyGrid:     Added category + {len(category.properties)} properties to flat list")
            print(f"DEBUG PropertyGrid: Final flat list length: {len(self._flat_list)}")
        else:
            self._flat_list.extend(self._properties)

    def _format_value(self, prop: Property) -> str:
        """Format property value for display."""
        if prop.display_format:
            return prop.display_format.format(prop.value)
        return str(prop.value)

    # Required TableDataProvider methods (not really used for property grid)
    def insert_row(self, index: int, data: list[Any]) -> None:
        """Insert row (not supported for property grid)."""
        pass  # Property grid doesn't support arbitrary row insertion
    
    def delete_row(self, index: int) -> None:
        """Delete row (not supported for property grid)."""
        pass  # Property grid doesn't support arbitrary row deletion
    
    def insert_column(self, index: int, header: str, default_value: Any = None) -> None:
        """Insert column (not supported for property grid)."""
        pass  # Property grid has fixed columns
    
    def delete_column(self, index: int) -> None:
        """Delete column (not supported for property grid)."""
        pass  # Property grid has fixed columns

    # Property iteration
    def __iter__(self):
        """Iterate over all properties."""
        return iter(self._properties)

    def __len__(self) -> int:
        """Return number of properties."""
        return len(self._properties)


class PropertyGridWidget:
    """Property grid widget with automatic styling and editor assignment.

    Extends the table widget to provide property grid functionality:
    - Automatic styling for editable/non-editable properties
    - Type-aware editor assignment
    - Property change notifications
    - Clean API for property management
    """

    def __init__(self, parent, property_provider: PropertyGridDataProvider):
        # Import editors here to avoid circular imports
        from .editors import SimpleTextCellEditor
        import ttkbootstrap as tb

        self.property_provider = property_provider
        self.parent = parent
        
        print(f"DEBUG PropertyGridWidget.__init__: property_provider = {type(property_provider).__name__}")
        print(f"DEBUG PropertyGridWidget: TabulaMutabilis class = {TabulaMutabilis}")
        print(f"DEBUG PropertyGridWidget: TabulaMutabilis.__init__ signature = {TabulaMutabilis.__init__.__code__.co_varnames[:5]}")
        
        # Get theme colors from ttkbootstrap
        try:
            style = tb.Style.get_instance()
            self.theme_primary = style.colors.primary
        except:
            self.theme_primary = "#0d6efd"  # Default blue if theme not available

        # Create the underlying table widget
        print(f"DEBUG PropertyGridWidget: About to create TabulaMutabilis with provider {type(property_provider).__name__}")
        # WORKAROUND: Create table without provider, then manually set it
        self.table_widget = TabulaMutabilis(parent)
        print(f"DEBUG PropertyGridWidget: Created TabulaMutabilis, initial data_provider is {type(self.table_widget.data_provider).__name__}")
        # Manually replace the data_provider
        self.table_widget.data_provider = property_provider
        self.table_widget.controller.data_provider = property_provider
        print(f"DEBUG PropertyGridWidget: Manually set data_provider to {type(self.table_widget.data_provider).__name__}")
        
        # Set column widths to fill canvas (40% property names, 60% values)
        # Bind to both Configure and Map events to catch all resize scenarios
        self.table_widget.canvas.bind('<Configure>', self._on_resize, add='+')
        self.table_widget.bind('<Map>', self._on_resize, add='+')

        # Apply initial styling
        self._apply_property_grid_styles()
        self._assign_cell_editors()

        # Listen for property changes
        property_provider.add_observer(self._on_property_changed)
        
        # Set up right-click context menu
        self._setup_context_menu()
        
        # Force initial column width calculation after a short delay
        self.table_widget.after(100, self._on_resize)
    
    def _setup_context_menu(self):
        """Set up right-click context menu for property values."""
        import tkinter as tk
        
        # Create context menu
        self.context_menu = tk.Menu(self.table_widget, tearoff=0)
        self.context_menu.add_command(label="Edit Property", command=self._edit_property)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy", command=self._copy_value)
        
        # Bind right-click to show menu
        self.table_widget.canvas.bind('<Button-3>', self._show_context_menu)
    
    def _show_context_menu(self, event):
        """Show context menu on right-click."""
        # Convert canvas coordinates to row/col
        canvas_x = self.table_widget.canvas.canvasx(event.x)
        canvas_y = self.table_widget.canvas.canvasy(event.y)
        
        # Find which cell was clicked
        result = self.table_widget.view.get_cell_at_coords(canvas_x, canvas_y)
        
        # Only show menu if clicking on value column (col 1)
        if result is not None:
            row, col = result
            if col == 1 and row >= 0:
                self._context_menu_row = row
                self._context_menu_col = col
                
                # Show the menu at cursor position
                try:
                    self.context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    self.context_menu.grab_release()
    
    def _edit_property(self):
        """Edit the property value using the cell editor."""
        if hasattr(self, '_context_menu_row') and hasattr(self, '_context_menu_col'):
            row = self._context_menu_row
            col = self._context_menu_col
            
            # Check if the property is editable
            item = self.property_provider._flat_list[row]
            if isinstance(item, Property) and not item.editable:
                print(f"Property '{item.name}' is not editable")
                return
            
            # Trigger the cell editor through the controller
            self.table_widget.controller._start_cell_editing(row, col)
    
    def _copy_value(self):
        """Copy the property value to clipboard."""
        if hasattr(self, '_context_menu_row') and hasattr(self, '_context_menu_col'):
            row = self._context_menu_row
            col = self._context_menu_col
            
            # Get the value
            value = self.property_provider.get_value(row, col)
            
            # Copy to clipboard
            self.table_widget.clipboard_clear()
            self.table_widget.clipboard_append(value)
            
            print(f"Copied to clipboard: {value}")
    
    def _on_resize(self, event=None):
        """Handle widget resize to adjust column widths and redraw."""
        # Get canvas width (subtract scrollbar width if present)
        canvas_width = self.table_widget.canvas.winfo_width()
        
        print(f"DEBUG _on_resize called: canvas_width={canvas_width}")
        
        if canvas_width > 10:  # Only if canvas has been sized
            # The padx margins are applied outside the canvas, so use full canvas width
            # Just subtract a small amount for scrollbar if present
            usable_width = canvas_width - 20
            
            # Set column widths: 40% for property names, 60% for values
            name_width = int(usable_width * 0.4)
            value_width = int(usable_width * 0.6)
            
            print(f"DEBUG _on_resize: usable_width={usable_width}, name_width={name_width}, value_width={value_width}")
            print(f"DEBUG _on_resize: BEFORE - view._col_widths={self.table_widget.view._col_widths}")
            
            # IMPORTANT: Set widths AFTER update_geometry, because update_geometry resets them!
            # First update geometry (which resets widths to defaults)
            self.table_widget._update_geometry()
            
            # Then override with our custom widths
            self.table_widget.view._col_widths = [name_width, value_width]
            
            print(f"DEBUG _on_resize: AFTER - view._col_widths={self.table_widget.view._col_widths}")
            
            # Update positions based on new widths
            self.table_widget.view._update_positions()
            
            # Redraw with the new widths
            self.table_widget._redraw()
            
            print(f"DEBUG _on_resize: Complete")

    def _apply_property_grid_styles(self):
        """Apply visual styles to property grid."""
        from .styles import CellStyle

        # Standard 1-pixel black borders for regular cells
        standard_borders = {
            'right': (1, '#000000'),
            'bottom': (1, '#000000')
        }
        
        # 4-pixel theme-colored border for top of category header
        category_top_borders = {
            'right': (1, '#000000'),
            'bottom': (1, '#000000'),
            'top': (4, self.theme_primary)
        }

        # Style for non-editable properties
        readonly_style = CellStyle(
            bg_color="#f0f0f0",  # Light gray
            text_color="#808080",  # Darker gray text
            font=("Arial", 10),
            row_height=35,
            borders=standard_borders
        )

        # Style for property names (left column)
        name_style = CellStyle(
            bg_color="#e8e8e8",  # Slightly darker gray
            text_color="#000000",
            font=("Arial", 10, "bold"),
            row_height=35,
            borders=standard_borders
        )
        
        # Style for editable property values
        value_style = CellStyle(
            bg_color="#ffffff",
            text_color="#000000",
            font=("Arial", 10),
            row_height=35,
            borders=standard_borders
        )

        # Style for category headers - with theme color background and bold text
        category_style = CellStyle(
            bg_color=self.theme_primary,
            text_color="#ffffff",  # White text on theme color
            font=("Arial", 11, "bold"),
            row_height=35,
            borders=category_top_borders,
            span_columns=True  # Span both columns
        )

        # Apply styles to each row
        for row in range(self.property_provider.get_row_count()):
            item = self.property_provider._flat_list[row]

            if isinstance(item, PropertyCategory):
                # Category header style - spans both columns
                self.table_widget.style_provider.set_cell_override(row, 0, category_style)
                self.table_widget.style_provider.set_cell_override(row, 1, category_style)

            elif isinstance(item, Property):
                # Property name column
                self.table_widget.style_provider.set_cell_override(row, 0, name_style)

                # Property value column (gray if not editable, white if editable)
                if not item.editable:
                    self.table_widget.style_provider.set_cell_override(row, 1, readonly_style)
                else:
                    self.table_widget.style_provider.set_cell_override(row, 1, value_style)
    
    def _is_last_property_in_category(self, row: int) -> bool:
        """Check if the property at row is the last one in its category."""
        if row >= len(self.property_provider._flat_list) - 1:
            return True  # Last row overall
        
        current_item = self.property_provider._flat_list[row]
        next_item = self.property_provider._flat_list[row + 1]
        
        # If next item is a category header, current property is last in its group
        return isinstance(next_item, PropertyCategory)

    def _assign_cell_editors(self):
        """Assign appropriate editors to editable properties."""
        from .editors import SimpleTextCellEditor
        from .styles import CellStyle
        
        for row in range(self.property_provider.get_row_count()):
            item = self.property_provider._flat_list[row]

            if isinstance(item, Property) and item.editable:
                # Get the current style for this cell
                current_style = self.table_widget.style_provider.get_effective_style(row, 1, False)
                
                # Use custom editor if specified
                if item.editor:
                    # If editor is an instance, get its class
                    if isinstance(item.editor, type):
                        editor = item.editor
                    else:
                        editor = type(item.editor)
                else:
                    # Auto-assign based on type
                    editor = self._get_editor_for_type(item.property_type)
                    
                    # Special case: detect color values even without explicit type
                    if editor is None or editor.__name__ == 'SimpleTextCellEditor':
                        if self._detect_color_property(item.value):
                            from .editors import ColorEditor
                            editor = ColorEditor

                if editor:
                    # Get existing style and add editor
                    existing_style = self.table_widget.style_provider.get_effective_style(row, 1, False)
                    new_style = existing_style.copy(cell_editor_class=editor)
                    self.table_widget.style_provider.set_cell_override(row, 1, new_style)

    def _get_editor_for_type(self, prop_type):
        """Auto-select editor based on property type.
        
        Automatically assigns specialized editors based on the property type:
        - bool: BooleanEditor (radio buttons)
        - datetime/date: DateTimeEditor (date/time picker)
        - str starting with '#' (color): ColorEditor (color picker)
        - int/float: SimpleTextCellEditor (with numeric validation)
        - default: SimpleTextCellEditor
        """
        from .editors import SimpleTextCellEditor, BooleanEditor, ColorEditor, DateTimeEditor
        from datetime import datetime, date
        
        if prop_type is bool:
            return BooleanEditor
        elif prop_type in (datetime, date):
            return DateTimeEditor
        elif prop_type is int or prop_type is float:
            # For numeric types, use text editor (could add NumericEditor later)
            return SimpleTextCellEditor
        else:
            # Default to text editor
            return SimpleTextCellEditor
    
    def _detect_color_property(self, value: Any) -> bool:
        """Detect if a value looks like a color (hex string)."""
        if isinstance(value, str):
            return value.startswith('#') and len(value) in (7, 9)  # #RRGGBB or #RRGGBBAA
        return False

    def _on_property_changed(self, event_type, property_obj):
        """Handle property change notifications."""
        if event_type == "property_changed":
            # Refresh the display
            self.table_widget.refresh()

            # Generate custom event for external listeners
            self.table_widget.event_generate("<<PropertyChanged>>",
                                           data={"property": property_obj})

    # Delegate methods to underlying table widget
    def pack(self, **kwargs):
        """Pack the widget."""
        self.table_widget.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the widget."""
        self.table_widget.grid(**kwargs)

    def place(self, **kwargs):
        """Place the widget."""
        self.table_widget.place(**kwargs)

    def refresh(self):
        """Refresh the widget display."""
        print(f"DEBUG PropertyGridWidget.refresh(): row_count={self.property_provider.get_row_count()}")
        self.table_widget.refresh()
        print(f"DEBUG PropertyGridWidget.refresh(): After table refresh")
        self._apply_property_grid_styles()  # Re-apply styles after refresh
        print(f"DEBUG PropertyGridWidget.refresh(): After apply styles")
        self._assign_cell_editors()  # Re-assign editors
        print(f"DEBUG PropertyGridWidget.refresh(): After assign editors")
        # Redraw again to show the applied styles and editors
        self.table_widget._redraw()
        print(f"DEBUG PropertyGridWidget.refresh(): After final redraw")
        # Trigger resize to maintain column widths after refresh
        self._on_resize()
        print(f"DEBUG PropertyGridWidget.refresh(): After resize")

    def get_property(self, name: str) -> Optional[Property]:
        """Get property by name."""
        return self.property_provider.get_property(name)

    def set_property_value(self, name: str, value: Any):
        """Set property value by name."""
        prop = self.get_property(name)
        if prop:
            prop.set_value(value)

    def bind(self, sequence, func, add=None):
        """Bind event handler."""
        return self.table_widget.bind(sequence, func, add)

    def unbind(self, sequence, funcid=None):
        """Unbind event handler."""
        return self.table_widget.unbind(sequence, funcid)
