"""Tabula Mutabilis: A Python library for pretty tables in Tkinter.

Tabula Mutabilis provides a comprehensive table widget for Tkinter applications
with TTK Bootstrap integration, virtual scrolling, cell editing, and undo/redo support.

Basic Usage:
    import tkinter as tk
    from tkinter import ttk
    import ttkbootstrap as tb
    from tabula_mutabilis import TabulaMutabilis

    # Create app
    root = tb.Window(themename="cosmo")
    table = TabulaMutabilis(root)

    # Set data
    data = [
        ["Alice", 25, "Engineer"],
        ["Bob", 30, "Designer"],
        ["Charlie", 35, "Manager"]
    ]
    headers = ["Name", "Age", "Role"]
    table.set_data(data, headers)

    table.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
"""

__version__ = "0.1.0"

# Main widget
from .widgets import TabulaMutabilis

# Data management
from .model import (
    CellValueFormatter,
    CellStyle,
    TableDataProvider,
    InMemoryDataProvider,
)

# Styling
from .styles import TableStyleProvider

# Cell editors
from .editors import (
    AbstractCellEditor,
    SimpleTextCellEditor,
    BooleanEditor,
    ColorEditor,
    DateTimeEditor,
    FilePathEditor,
    FolderPathEditor,
    EnumEditor,
)

# Controllers (for advanced usage)
from .controllers import (
    SelectionModel,
    SetValueCommand,
    InsertRowCommand,
    TableController,
)

# Views (for advanced usage)
from .views import RenderContext

# Property grid (NEW)
from .property_grid import (
    Property,
    PropertyCategory,
    PropertyGridDataProvider,
    PropertyGridWidget,
)

__all__ = [
    # Version
    "__version__",

    # Main widget
    "TabulaMutabilis",

    # Data management
    "CellValueFormatter",
    "CellStyle",
    "TableDataProvider",
    "InMemoryDataProvider",

    # Styling
    "TableStyleProvider",

    # Cell editors
    "AbstractCellEditor",
    "SimpleTextCellEditor",

    # Controllers
    "SelectionModel",
    "SetValueCommand",
    "InsertRowCommand",
    "TableController",
    
    # Views
    "RenderContext",

    # Property grid (NEW)
    "Property",
    "PropertyCategory", 
    "PropertyGridDataProvider",
    "PropertyGridWidget",
]
