"""Cell editors for Tabula Mutabilis table widget.

This module provides cell editing abstractions:
- AbstractCellEditor: Base class for cell editors
- SimpleTextCellEditor: Modal text editor with validation
"""

from __future__ import annotations

import abc
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional

from vultus_serpentis.validation import ValidationResult, Validator


class AbstractCellEditor(abc.ABC):
    """Abstract base class for cell editors.

    Cell editors are responsible for showing a modal dialog to edit cell values.
    They must integrate with TTK Bootstrap themes and support validation.
    """

    def __init__(self, validator: Optional[Validator] = None) -> None:
        """Initialize the cell editor.

        Args:
            validator: Optional validator for input validation
        """
        self.validator = validator

    @abc.abstractmethod
    def show_modal(self, parent_window: tk.Tk, initial_value: Any) -> Optional[Any]:
        """Show a modal dialog to edit the cell value.

        Args:
            parent_window: The parent window (usually the table's toplevel)
            initial_value: The current cell value

        Returns:
            The new value if user confirms, None if cancelled
        """
        ...


class SimpleTextCellEditor(AbstractCellEditor):
    """A simple modal text editor for cell values.

    Shows a modal dialog with a text entry field, OK/Cancel buttons,
    and validation feedback.
    """

    def __init__(
        self,
        validator: Optional[Validator] = None,
        title: str = "Edit Cell",
        width: int = 300,
        height: int = 150,
    ) -> None:
        """Initialize the text cell editor.

        Args:
            validator: Optional validator for input
            title: Dialog window title
            width: Dialog width in pixels
            height: Dialog height in pixels
        """
        super().__init__(validator)
        self.title = title
        self.width = width
        self.height = height

    def show_modal(self, parent_window: tk.Tk, initial_value: Any) -> Optional[Any]:
        """Show the modal text editor dialog.

        Args:
            parent_window: Parent window for the dialog
            initial_value: Current cell value to edit

        Returns:
            New value if confirmed, None if cancelled
        """
        # Create modal dialog
        dialog = tk.Toplevel(parent_window)
        dialog.title(self.title)
        dialog.geometry(f"{self.width}x{self.height}")
        dialog.resizable(False, False)
        dialog.transient(parent_window)
        dialog.grab_set()

        # Center the dialog on parent
        dialog.withdraw()  # Hide while calculating position
        dialog.update_idletasks()

        parent_x = parent_window.winfo_rootx()
        parent_y = parent_window.winfo_rooty()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()

        x = parent_x + (parent_width // 2) - (self.width // 2)
        y = parent_y + (parent_height // 2) - (self.height // 2)

        dialog.geometry(f"+{x}+{y}")
        dialog.deiconify()

        # Result variable
        result = {"value": None, "confirmed": False}

        # Create UI components
        self._create_ui(dialog, initial_value, result)

        # Wait for dialog to close
        parent_window.wait_window(dialog)

        return result["value"] if result["confirmed"] else None

    def _create_ui(self, dialog: tk.Toplevel, initial_value: Any, result: dict) -> None:
        """Create the dialog user interface.

        Args:
            dialog: The dialog window
            initial_value: Initial value to display
            result: Dict to store the result
        """
        # Main frame with padding
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Label
        ttk.Label(main_frame, text="Value:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        # Entry field
        value_var = tk.StringVar(value=str(initial_value) if initial_value is not None else "")
        entry = ttk.Entry(main_frame, textvariable=value_var)
        entry.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 10))
        entry.focus_set()
        entry.select_range(0, tk.END)

        # Validation feedback label (initially hidden)
        feedback_var = tk.StringVar()
        feedback_label = ttk.Label(main_frame, textvariable=feedback_var, foreground="red")
        feedback_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        feedback_label.grid_remove()  # Hide initially

        # Button frame with extra bottom padding
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky=tk.E, pady=(0, 10))

        # OK button
        ok_button = ttk.Button(
            button_frame,
            text="OK",
            command=lambda: self._on_ok(dialog, value_var.get(), result, feedback_var, feedback_label)
        )
        ok_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Cancel button
        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=lambda: self._on_cancel(dialog, result)
        )
        cancel_button.pack(side=tk.RIGHT)

        # Bind Enter key to OK
        dialog.bind(
            "<Return>",
            lambda e: self._on_ok(dialog, value_var.get(), result, feedback_var, feedback_label)
        )
        dialog.bind("<Escape>", lambda e: self._on_cancel(dialog, result))

    def _on_ok(
        self,
        dialog: tk.Toplevel,
        value_str: str,
        result: dict,
        feedback_var: tk.StringVar,
        feedback_label: ttk.Label
    ) -> None:
        """Handle OK button click.

        Args:
            dialog: The dialog window
            value_str: String value from entry
            result: Result dict to update
            feedback_var: Variable for feedback text
            feedback_label: Label for feedback display
        """
        # Validate input if validator is set
        if self.validator:
            try:
                # Try to convert string to appropriate type
                # For now, just validate the string
                validation_result = self.validator.validate(value_str)
                if not validation_result.is_valid:
                    feedback_var.set(validation_result.message)
                    feedback_label.grid()  # Show feedback
                    return
            except Exception as e:
                feedback_var.set(f"Validation error: {str(e)}")
                feedback_label.grid()
                return

        # Hide feedback if validation passed
        feedback_label.grid_remove()

        # Convert string back to appropriate type if possible
        value = self._convert_value(value_str)

        result["value"] = value
        result["confirmed"] = True
        dialog.destroy()

    def _on_cancel(self, dialog: tk.Toplevel, result: dict) -> None:
        """Handle Cancel button click.

        Args:
            dialog: The dialog window
            result: Result dict to update
        """
        result["confirmed"] = False
        dialog.destroy()

    def _convert_value(self, value_str: str) -> Any:
        """Convert string input to appropriate Python type.

        This is a simple conversion - in a real implementation,
        you might want more sophisticated type detection.

        Args:
            value_str: String value to convert

        Returns:
            Converted value
        """
        if not value_str.strip():
            return None

        # Try int
        try:
            return int(value_str)
        except ValueError:
            pass

        # Try float
        try:
            return float(value_str)
        except ValueError:
            pass

        # Try bool
        lower_str = value_str.lower()
        if lower_str in ('true', 'false'):
            return lower_str == 'true'

        # Default to string
        return value_str


class BooleanEditor(AbstractCellEditor):
    """A modal editor for boolean values with radio buttons.
    
    Shows a simple dialog with True/False radio buttons.
    """
    
    def __init__(self, title: str = "Edit Boolean", width: int = 300, height: int = 150) -> None:
        """Initialize the boolean editor.
        
        Args:
            title: Dialog window title
            width: Dialog width in pixels
            height: Dialog height in pixels
        """
        super().__init__()
        self.title = title
        self.width = width
        self.height = height
    
    def show_modal(self, parent_window: tk.Tk, initial_value: Any) -> Optional[Any]:
        """Show the modal boolean editor dialog.
        
        Args:
            parent_window: Parent window for the dialog
            initial_value: Current boolean value
            
        Returns:
            New boolean value if confirmed, None if cancelled
        """
        # Create modal dialog
        dialog = tk.Toplevel(parent_window)
        dialog.title(self.title)
        dialog.geometry(f"{self.width}x{self.height}")
        dialog.resizable(False, False)
        dialog.transient(parent_window)
        dialog.grab_set()
        
        # Center the dialog
        dialog.withdraw()
        dialog.update_idletasks()
        
        parent_x = parent_window.winfo_rootx()
        parent_y = parent_window.winfo_rooty()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()
        
        x = parent_x + (parent_width // 2) - (self.width // 2)
        y = parent_y + (parent_height // 2) - (self.height // 2)
        
        dialog.geometry(f"+{x}+{y}")
        dialog.deiconify()
        
        # Result variable
        result = {"value": None, "confirmed": False}
        
        # Parse initial value
        if isinstance(initial_value, bool):
            initial_bool = initial_value
        elif isinstance(initial_value, str):
            initial_bool = initial_value.lower() in ('true', '1', 'yes')
        else:
            initial_bool = bool(initial_value)
        
        # Create UI with grid layout
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid columns for consistent sizing
        main_frame.columnconfigure(0, weight=0, minsize=100)
        main_frame.columnconfigure(1, weight=1)
        
        # Label
        ttk.Label(main_frame, text="Select value:").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        # Radio buttons
        bool_var = tk.BooleanVar(value=initial_bool)
        ttk.Radiobutton(main_frame, text="True", variable=bool_var, value=True).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=3)
        ttk.Radiobutton(main_frame, text="False", variable=bool_var, value=False).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=3)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky=tk.E, pady=(20, 0))
        
        def on_ok():
            result["value"] = bool_var.get()
            result["confirmed"] = True
            dialog.destroy()
        
        def on_cancel():
            result["confirmed"] = False
            dialog.destroy()
        
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT)
        
        dialog.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_cancel())
        
        parent_window.wait_window(dialog)
        return result["value"] if result["confirmed"] else None


class ColorEditor(AbstractCellEditor):
    """A modal editor for color values with color picker.
    
    Shows a color chooser dialog.
    """
    
    def __init__(self, title: str = "Choose Color") -> None:
        """Initialize the color editor.
        
        Args:
            title: Dialog window title
        """
        super().__init__()
        self.title = title
    
    def show_modal(self, parent_window: tk.Tk, initial_value: Any) -> Optional[Any]:
        """Show the color picker dialog.
        
        Args:
            parent_window: Parent window for the dialog
            initial_value: Current color value (hex string like "#FF0000")
            
        Returns:
            New color hex string if confirmed, None if cancelled
        """
        from tkinter import colorchooser
        
        # Parse initial color
        initial_color = str(initial_value) if initial_value else "#FFFFFF"
        
        # Show color chooser
        color = colorchooser.askcolor(
            color=initial_color,
            title=self.title,
            parent=parent_window
        )
        
        # color is ((r, g, b), "#RRGGBB") or (None, None) if cancelled
        if color[1]:
            return color[1]  # Return hex string
        return None


class DateTimeEditor(AbstractCellEditor):
    """A modal editor for date/datetime values.
    
    Shows a dialog with date/time entry fields.
    """
    
    def __init__(
        self,
        title: str = "Edit Date/Time",
        width: int = 350,
        height: int = 200,
        include_time: bool = True
    ) -> None:
        """Initialize the datetime editor.
        
        Args:
            title: Dialog window title
            width: Dialog width in pixels
            height: Dialog height in pixels
            include_time: Whether to include time fields
        """
        super().__init__()
        self.title = title
        self.width = width
        self.height = height
        self.include_time = include_time
    
    def show_modal(self, parent_window: tk.Tk, initial_value: Any) -> Optional[Any]:
        """Show the modal datetime editor dialog.
        
        Args:
            parent_window: Parent window for the dialog
            initial_value: Current datetime value (string or datetime object)
            
        Returns:
            New datetime string if confirmed, None if cancelled
        """
        from datetime import datetime
        
        # Create modal dialog
        dialog = tk.Toplevel(parent_window)
        dialog.title(self.title)
        dialog.geometry(f"{self.width}x{self.height}")
        dialog.resizable(False, False)
        dialog.transient(parent_window)
        dialog.grab_set()
        
        # Center the dialog
        dialog.withdraw()
        dialog.update_idletasks()
        
        parent_x = parent_window.winfo_rootx()
        parent_y = parent_window.winfo_rooty()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()
        
        x = parent_x + (parent_width // 2) - (self.width // 2)
        y = parent_y + (parent_height // 2) - (self.height // 2)
        
        dialog.geometry(f"+{x}+{y}")
        dialog.deiconify()
        
        # Parse initial value
        if isinstance(initial_value, datetime):
            dt = initial_value
        elif isinstance(initial_value, str):
            try:
                # Try common formats
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%m/%d/%Y %H:%M:%S"]:
                    try:
                        dt = datetime.strptime(initial_value, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    dt = datetime.now()
            except:
                dt = datetime.now()
        else:
            dt = datetime.now()
        
        # Result variable
        result = {"value": None, "confirmed": False}
        
        # Create UI with grid layout
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid columns for consistent sizing
        main_frame.columnconfigure(0, weight=0, minsize=60)
        main_frame.columnconfigure(1, weight=1)
        
        # Date fields
        ttk.Label(main_frame, text="Date:").grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        date_frame = ttk.Frame(main_frame)
        date_frame.grid(row=0, column=1, sticky=tk.EW, pady=(0, 8))
        
        year_var = tk.StringVar(value=str(dt.year))
        month_var = tk.StringVar(value=str(dt.month).zfill(2))
        day_var = tk.StringVar(value=str(dt.day).zfill(2))
        
        ttk.Label(date_frame, text="Year:", width=6).grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(date_frame, textvariable=year_var, width=8).grid(row=0, column=1, sticky=tk.W, padx=(0, 15))
        ttk.Label(date_frame, text="Month:", width=6).grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        ttk.Entry(date_frame, textvariable=month_var, width=5).grid(row=0, column=3, sticky=tk.W, padx=(0, 15))
        ttk.Label(date_frame, text="Day:", width=6).grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        ttk.Entry(date_frame, textvariable=day_var, width=5).grid(row=0, column=5, sticky=tk.W)
        
        # Time fields (if enabled)
        hour_var = tk.StringVar(value=str(dt.hour).zfill(2))
        minute_var = tk.StringVar(value=str(dt.minute).zfill(2))
        second_var = tk.StringVar(value=str(dt.second).zfill(2))
        
        if self.include_time:
            ttk.Label(main_frame, text="Time:").grid(row=1, column=0, sticky=tk.W, pady=(0, 8))
            
            time_frame = ttk.Frame(main_frame)
            time_frame.grid(row=1, column=1, sticky=tk.EW, pady=(0, 8))
            
            ttk.Label(time_frame, text="Hour:", width=6).grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
            ttk.Entry(time_frame, textvariable=hour_var, width=5).grid(row=0, column=1, sticky=tk.W, padx=(0, 15))
            ttk.Label(time_frame, text="Min:", width=6).grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
            ttk.Entry(time_frame, textvariable=minute_var, width=5).grid(row=0, column=3, sticky=tk.W, padx=(0, 15))
            ttk.Label(time_frame, text="Sec:", width=6).grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
            ttk.Entry(time_frame, textvariable=second_var, width=5).grid(row=0, column=5, sticky=tk.W)
        
        # Feedback label
        feedback_var = tk.StringVar()
        feedback_label = ttk.Label(main_frame, textvariable=feedback_var, foreground="red")
        feedback_label.grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        feedback_label.grid_remove()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, sticky=tk.E)
        
        def on_ok():
            try:
                year = int(year_var.get())
                month = int(month_var.get())
                day = int(day_var.get())
                
                if self.include_time:
                    hour = int(hour_var.get())
                    minute = int(minute_var.get())
                    second = int(second_var.get())
                    new_dt = datetime(year, month, day, hour, minute, second)
                    result["value"] = new_dt.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    new_dt = datetime(year, month, day)
                    result["value"] = new_dt.strftime("%Y-%m-%d")
                
                result["confirmed"] = True
                dialog.destroy()
            except ValueError as e:
                feedback_var.set(f"Invalid date/time: {str(e)}")
                feedback_label.grid()
        
        def on_cancel():
            result["confirmed"] = False
            dialog.destroy()
        
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT)
        
        dialog.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_cancel())
        
        parent_window.wait_window(dialog)
        return result["value"] if result["confirmed"] else None


class FilePathEditor(AbstractCellEditor):
    """A modal editor for file paths with browse button.
    
    Shows a dialog with text entry and a browse button to select files.
    """
    
    def __init__(
        self,
        title: str = "Select File",
        width: int = 500,
        height: int = 150,
        file_types: Optional[list[tuple[str, str]]] = None,
        initial_dir: Optional[str] = None
    ) -> None:
        """Initialize the file path editor.
        
        Args:
            title: Dialog window title
            width: Dialog width in pixels
            height: Dialog height in pixels
            file_types: List of (description, pattern) tuples for file filter
                       e.g., [("Text files", "*.txt"), ("All files", "*.*")]
            initial_dir: Initial directory for file browser
        """
        super().__init__()
        self.title = title
        self.width = width
        self.height = height
        self.file_types = file_types or [("All files", "*.*")]
        self.initial_dir = initial_dir
    
    def show_modal(self, parent_window: tk.Tk, initial_value: Any) -> Optional[Any]:
        """Show the modal file path editor dialog.
        
        Args:
            parent_window: Parent window for the dialog
            initial_value: Current file path value
            
        Returns:
            New file path if confirmed, None if cancelled
        """
        from tkinter import filedialog
        import os
        
        # Create modal dialog
        dialog = tk.Toplevel(parent_window)
        dialog.title(self.title)
        dialog.geometry(f"{self.width}x{self.height}")
        dialog.resizable(False, False)
        dialog.transient(parent_window)
        dialog.grab_set()
        
        # Center the dialog
        dialog.withdraw()
        dialog.update_idletasks()
        
        parent_x = parent_window.winfo_rootx()
        parent_y = parent_window.winfo_rooty()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()
        
        x = parent_x + (parent_width // 2) - (self.width // 2)
        y = parent_y + (parent_height // 2) - (self.height // 2)
        
        dialog.geometry(f"+{x}+{y}")
        dialog.deiconify()
        
        # Result variable
        result = {"value": None, "confirmed": False}
        
        # Parse initial value
        initial_path = str(initial_value) if initial_value else ""
        
        # Create UI with grid layout
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid columns for consistent sizing
        main_frame.columnconfigure(0, weight=0, minsize=80)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=0)
        
        # File path label and entry
        ttk.Label(main_frame, text="File Path:").grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        path_var = tk.StringVar(value=initial_path)
        path_entry = ttk.Entry(main_frame, textvariable=path_var)
        path_entry.grid(row=0, column=1, sticky=tk.EW, padx=(0, 8), pady=(0, 8))
        
        def browse():
            # Determine initial directory
            if path_var.get() and os.path.exists(os.path.dirname(path_var.get())):
                init_dir = os.path.dirname(path_var.get())
            elif self.initial_dir and os.path.exists(self.initial_dir):
                init_dir = self.initial_dir
            else:
                init_dir = os.path.expanduser("~")
            
            # Show file dialog
            filename = filedialog.askopenfilename(
                parent=dialog,
                title=self.title,
                initialdir=init_dir,
                filetypes=self.file_types
            )
            
            if filename:
                path_var.set(filename)
        
        ttk.Button(main_frame, text="Browse...", command=browse, width=12).grid(row=0, column=2, sticky=tk.W, pady=(0, 8))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=3, sticky=tk.E, pady=(15, 0))
        
        def on_ok():
            result["value"] = path_var.get()
            result["confirmed"] = True
            dialog.destroy()
        
        def on_cancel():
            result["confirmed"] = False
            dialog.destroy()
        
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT)
        
        dialog.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_cancel())
        
        parent_window.wait_window(dialog)
        return result["value"] if result["confirmed"] else None


class FolderPathEditor(AbstractCellEditor):
    """A modal editor for folder paths with browse button.
    
    Shows a dialog with text entry and a browse button to select folders.
    """
    
    def __init__(
        self,
        title: str = "Select Folder",
        width: int = 500,
        height: int = 150,
        initial_dir: Optional[str] = None
    ) -> None:
        """Initialize the folder path editor.
        
        Args:
            title: Dialog window title
            width: Dialog width in pixels
            height: Dialog height in pixels
            initial_dir: Initial directory for folder browser
        """
        super().__init__()
        self.title = title
        self.width = width
        self.height = height
        self.initial_dir = initial_dir
    
    def show_modal(self, parent_window: tk.Tk, initial_value: Any) -> Optional[Any]:
        """Show the modal folder path editor dialog.
        
        Args:
            parent_window: Parent window for the dialog
            initial_value: Current folder path value
            
        Returns:
            New folder path if confirmed, None if cancelled
        """
        from tkinter import filedialog
        import os
        
        # Create modal dialog
        dialog = tk.Toplevel(parent_window)
        dialog.title(self.title)
        dialog.geometry(f"{self.width}x{self.height}")
        dialog.resizable(False, False)
        dialog.transient(parent_window)
        dialog.grab_set()
        
        # Center the dialog
        dialog.withdraw()
        dialog.update_idletasks()
        
        parent_x = parent_window.winfo_rootx()
        parent_y = parent_window.winfo_rooty()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()
        
        x = parent_x + (parent_width // 2) - (self.width // 2)
        y = parent_y + (parent_height // 2) - (self.height // 2)
        
        dialog.geometry(f"+{x}+{y}")
        dialog.deiconify()
        
        # Result variable
        result = {"value": None, "confirmed": False}
        
        # Parse initial value
        initial_path = str(initial_value) if initial_value else ""
        
        # Create UI with grid layout
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid columns for consistent sizing
        main_frame.columnconfigure(0, weight=0, minsize=80)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=0)
        
        # Folder path label and entry
        ttk.Label(main_frame, text="Folder Path:").grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        path_var = tk.StringVar(value=initial_path)
        path_entry = ttk.Entry(main_frame, textvariable=path_var)
        path_entry.grid(row=0, column=1, sticky=tk.EW, padx=(0, 8), pady=(0, 8))
        
        def browse():
            # Determine initial directory
            if path_var.get() and os.path.exists(path_var.get()):
                init_dir = path_var.get()
            elif self.initial_dir and os.path.exists(self.initial_dir):
                init_dir = self.initial_dir
            else:
                init_dir = os.path.expanduser("~")
            
            # Show folder dialog
            foldername = filedialog.askdirectory(
                parent=dialog,
                title=self.title,
                initialdir=init_dir
            )
            
            if foldername:
                path_var.set(foldername)
        
        ttk.Button(main_frame, text="Browse...", command=browse, width=12).grid(row=0, column=2, sticky=tk.W, pady=(0, 8))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=3, sticky=tk.E, pady=(15, 0))
        
        def on_ok():
            result["value"] = path_var.get()
            result["confirmed"] = True
            dialog.destroy()
        
        def on_cancel():
            result["confirmed"] = False
            dialog.destroy()
        
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT)
        
        dialog.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_cancel())
        
        parent_window.wait_window(dialog)
        return result["value"] if result["confirmed"] else None


class EnumEditor(AbstractCellEditor):
    """A modal editor for enum/dropdown values.
    
    Shows a dialog with a combobox to select from predefined options.
    """
    
    def __init__(
        self,
        options: list[str],
        title: str = "Select Value",
        width: int = 350,
        height: int = 150,
        allow_custom: bool = False
    ) -> None:
        """Initialize the enum editor.
        
        Args:
            options: List of valid options to choose from
            title: Dialog window title
            width: Dialog width in pixels
            height: Dialog height in pixels
            allow_custom: If True, allows entering custom values not in the list
        """
        super().__init__()
        self.options = options
        self.title = title
        self.width = width
        self.height = height
        self.allow_custom = allow_custom
    
    def show_modal(self, parent_window: tk.Tk, initial_value: Any) -> Optional[Any]:
        """Show the modal enum editor dialog.
        
        Args:
            parent_window: Parent window for the dialog
            initial_value: Current value
            
        Returns:
            New value if confirmed, None if cancelled
        """
        # Create modal dialog
        dialog = tk.Toplevel(parent_window)
        dialog.title(self.title)
        dialog.geometry(f"{self.width}x{self.height}")
        dialog.resizable(False, False)
        dialog.transient(parent_window)
        dialog.grab_set()
        
        # Center the dialog
        dialog.withdraw()
        dialog.update_idletasks()
        
        parent_x = parent_window.winfo_rootx()
        parent_y = parent_window.winfo_rooty()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()
        
        x = parent_x + (parent_width // 2) - (self.width // 2)
        y = parent_y + (parent_height // 2) - (self.height // 2)
        
        dialog.geometry(f"+{x}+{y}")
        dialog.deiconify()
        
        # Result variable
        result = {"value": None, "confirmed": False}
        
        # Parse initial value
        initial_str = str(initial_value) if initial_value else ""
        
        # Create UI with grid layout
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid columns for consistent sizing
        main_frame.columnconfigure(0, weight=0, minsize=80)
        main_frame.columnconfigure(1, weight=1)
        
        # Label and combobox
        ttk.Label(main_frame, text="Select value:").grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        value_var = tk.StringVar(value=initial_str)
        combo = ttk.Combobox(
            main_frame,
            textvariable=value_var,
            values=self.options,
            state='normal' if self.allow_custom else 'readonly'
        )
        combo.grid(row=0, column=1, sticky=tk.EW, pady=(0, 8))
        combo.focus_set()
        
        # Feedback label
        feedback_var = tk.StringVar()
        feedback_label = ttk.Label(main_frame, textvariable=feedback_var, foreground="red")
        feedback_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 8))
        feedback_label.grid_remove()  # Hide initially
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=tk.E, pady=(15, 0))
        
        def on_ok():
            selected = value_var.get()
            
            # Validate if not allowing custom values
            if not self.allow_custom and selected not in self.options:
                feedback_var.set(f"Please select a value from the list")
                feedback_label.grid()
                return
            
            result["value"] = selected
            result["confirmed"] = True
            dialog.destroy()
        
        def on_cancel():
            result["confirmed"] = False
            dialog.destroy()
        
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT)
        
        dialog.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_cancel())
        
        parent_window.wait_window(dialog)
        return result["value"] if result["confirmed"] else None
