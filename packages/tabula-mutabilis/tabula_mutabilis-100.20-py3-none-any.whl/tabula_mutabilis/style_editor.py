"""GUI Style Editor for table styles with TOML support."""

import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from pathlib import Path
from typing import Dict, Optional
import toml


class StyleTabBuilder:
    """Builds individual style tab UI components."""

    def __init__(self, notebook: ttk.Notebook, styles: Dict):
        """Initialize the tab builder.

        Args:
            notebook: Parent notebook widget
            styles: Reference to the styles dictionary
        """
        self.notebook = notebook
        self.styles = styles

    def create_style_tab(self, title: str, style_key: str) -> tuple[ttk.Frame, Dict]:
        """Create a tab for editing a specific style category.

        Args:
            title: Tab title
            style_key: Key in self.styles dict

        Returns:
            Tuple of (frame, widgets_dict)
        """
        frame = ttk.Frame(self.notebook, padding="10")
        widgets = {}

        # Background Color
        row = 0
        self._add_color_picker(
            frame, row, "Background Color:", style_key, 'bg_color', widgets)

        # Foreground Color
        row += 1
        self._add_color_picker(
            frame, row, "Text Color:", style_key, 'text_color', widgets)

        # Font Family
        row += 1
        ttk.Label(
            frame,
            text="Font Family:").grid(
            row=row,
            column=0,
            sticky=tk.W,
            pady=5)

        font_combo = ttk.Combobox(
            frame,
            values=[
                "Arial",
                "Helvetica",
                "Times New Roman",
                "Courier New",
                "Verdana",
                "Georgia"],
            width=20
        )
        font_combo.set(self.styles[style_key]['font_family'])
        font_combo.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        widgets['font_family'] = font_combo

        # Font Size
        row += 1
        ttk.Label(
            frame,
            text="Font Size:").grid(
            row=row,
            column=0,
            sticky=tk.W,
            pady=5)

        size_spin = ttk.Spinbox(frame, from_=8, to=24, width=10)
        size_spin.set(self.styles[style_key]['font_size'])
        size_spin.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        widgets['font_size'] = size_spin

        # Font Weight
        row += 1
        ttk.Label(
            frame,
            text="Font Weight:").grid(
            row=row,
            column=0,
            sticky=tk.W,
            pady=5)

        weight_combo = ttk.Combobox(
            frame,
            values=["normal", "bold"],
            width=20
        )
        weight_combo.set(self.styles[style_key]['font_weight'])
        weight_combo.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        widgets['font_weight'] = weight_combo

        # Bottom Border Width
        row += 1
        ttk.Label(
            frame,
            text="Bottom Border Width:").grid(
            row=row,
            column=0,
            sticky=tk.W,
            pady=5)

        border_width_spin = ttk.Spinbox(frame, from_=0, to=10, width=10)
        border_width_spin.set(
            self.styles[style_key].get(
                'border_bottom_width', 1))
        border_width_spin.grid(
            row=row,
            column=1,
            sticky=tk.W,
            pady=5,
            padx=(
                10,
                0))
        widgets['border_bottom_width'] = border_width_spin

        # Bottom Border Color
        row += 1
        self._add_color_picker(
            frame, row, "Bottom Border Color:", style_key, 'border_bottom_color', widgets, default='#dee2e6')

        # Preview
        row += 1
        ttk.Label(
            frame,
            text="Preview:").grid(
            row=row,
            column=0,
            sticky=tk.W,
            pady=(
                15,
                5))

        preview_frame = ttk.Frame(frame, relief=tk.SUNKEN, borderwidth=2)
        preview_frame.grid(
            row=row, column=1, sticky=tk.EW, pady=(
                15, 5), padx=(
                10, 0))

        preview_label = tk.Label(
            preview_frame,
            text="Sample Text",
            bg=self.styles[style_key]['bg_color'],
            fg=self.styles[style_key]['text_color'],
            font=(self.styles[style_key]['font_family'],
                  self.styles[style_key]['font_size'],
                  self.styles[style_key]['font_weight']),
            padx=10,
            pady=5
        )
        preview_label.pack(fill=tk.BOTH, expand=True)
        widgets['preview'] = preview_label

        # Update preview button
        row += 1
        ttk.Button(
            frame,
            text="Update Preview",
            command=lambda: self.update_preview(style_key, widgets)
        ).grid(row=row, column=1, sticky=tk.W, pady=(5, 0), padx=(10, 0))

        return frame, widgets

    def _add_color_picker(
        self,
        frame: ttk.Frame,
        row: int,
        label_text: str,
        style_key: str,
        color_key: str,
        widgets: Dict,
        default: str = None
    ):
        """Add a color picker row to the frame.

        Args:
            frame: Parent frame
            row: Grid row number
            label_text: Label text
            style_key: Style category key
            color_key: Color property key
            widgets: Widgets dictionary to update
            default: Default color if not in styles
        """
        ttk.Label(
            frame,
            text=label_text).grid(
            row=row,
            column=0,
            sticky=tk.W,
            pady=5)

        color_frame = ttk.Frame(frame)
        color_frame.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        color_value = self.styles[style_key].get(color_key, default or '#ffffff')
        color_entry = ttk.Entry(color_frame, width=15)
        color_entry.insert(0, color_value)
        color_entry.pack(side=tk.LEFT, padx=(0, 5))

        color_preview = tk.Canvas(
            color_frame,
            width=30,
            height=20,
            bg=color_value)
        color_preview.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            color_frame,
            text="Pick...",
            command=lambda: self.pick_color(color_entry, color_preview),
            width=8
        ).pack(side=tk.LEFT)

        widgets[color_key] = color_entry
        widgets[f'{color_key.split("_")[0]}_preview'] = color_preview

    def pick_color(self, entry: ttk.Entry, preview: tk.Canvas):
        """Open color picker and update entry and preview.

        Args:
            entry: Entry widget to update
            preview: Canvas widget to update
        """
        current_color = entry.get()
        color = colorchooser.askcolor(
            color=current_color, title="Choose Color")

        if color[1]:  # color[1] is the hex string
            entry.delete(0, tk.END)
            entry.insert(0, color[1])
            preview.config(bg=color[1])

    def update_preview(self, style_key: str, widgets: Dict):
        """Update the preview label with current settings.

        Args:
            style_key: Key in self.styles dict
            widgets: Dictionary of widgets for this style
        """
        try:
            bg_color = widgets['bg_color'].get()
            text_color = widgets['text_color'].get()
            font_family = widgets['font_family'].get()
            font_size = int(widgets['font_size'].get())
            font_weight = widgets['font_weight'].get()
            border_color = widgets['border_bottom_color'].get()

            widgets['preview'].config(
                bg=bg_color,
                fg=text_color,
                font=(font_family, font_size, font_weight)
            )
            widgets['bg_preview'].config(bg=bg_color)
            widgets['text_preview'].config(bg=text_color)
            widgets['border_preview'].config(bg=border_color)
        except Exception as e:
            messagebox.showerror(
                "Preview Error",
                f"Failed to update preview: {e}")


class StyleDataManager:
    """Manages style data operations including TOML load/save."""

    def __init__(self, styles: Dict):
        """Initialize the data manager.

        Args:
            styles: Reference to the styles dictionary
        """
        self.styles = styles
        self.current_file: Optional[Path] = None

    def collect_styles(self, widgets_map: Dict[str, Dict]) -> Dict:
        """Collect all style settings from the UI widgets.

        Args:
            widgets_map: Map of style_key -> widgets dict

        Returns:
            Dictionary of all styles
        """
        styles = {}

        for style_key, widgets in widgets_map.items():
            styles[style_key] = {
                'bg_color': widgets['bg_color'].get(),
                'text_color': widgets['text_color'].get(),
                'font_family': widgets['font_family'].get(),
                'font_size': int(widgets['font_size'].get()),
                'font_weight': widgets['font_weight'].get(),
                'border_bottom_width': int(widgets['border_bottom_width'].get()),
                'border_bottom_color': widgets['border_bottom_color'].get()
            }

        return styles

    def load_from_toml(self, filename: str, widgets_map: Dict[str, Dict], update_callback) -> bool:
        """Load styles from a TOML file.

        Args:
            filename: Path to TOML file
            widgets_map: Map of style_key -> widgets dict
            update_callback: Callback to update preview (style_key, widgets)

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filename, 'r') as f:
                loaded_styles = toml.load(f)

            # Update internal styles
            self.styles.update(loaded_styles)

            # Update UI widgets
            for style_key, widgets in widgets_map.items():
                if style_key in loaded_styles:
                    style = loaded_styles[style_key]

                    widgets['bg_color'].delete(0, tk.END)
                    widgets['bg_color'].insert(
                        0, style.get('bg_color', '#ffffff'))

                    widgets['text_color'].delete(0, tk.END)
                    widgets['text_color'].insert(
                        0, style.get('text_color', '#000000'))

                    widgets['font_family'].set(
                        style.get('font_family', 'Arial'))
                    widgets['font_size'].delete(0, tk.END)
                    widgets['font_size'].insert(
                        0, str(style.get('font_size', 10)))
                    widgets['font_weight'].set(
                        style.get('font_weight', 'normal'))

                    widgets['border_bottom_width'].delete(0, tk.END)
                    widgets['border_bottom_width'].insert(
                        0, str(style.get('border_bottom_width', 1)))
                    widgets['border_bottom_color'].delete(0, tk.END)
                    widgets['border_bottom_color'].insert(
                        0, style.get('border_bottom_color', '#dee2e6'))

                    update_callback(style_key, widgets)

            self.current_file = Path(filename)
            messagebox.showinfo(
                "Success", f"Loaded styles from {Path(filename).name}")
            return True

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load TOML file: {e}")
            return False

    def save_to_toml(self, filename: str, styles: Dict) -> bool:
        """Save styles to a TOML file.

        Args:
            filename: Path to save to
            styles: Styles dictionary to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filename, 'w') as f:
                f.write("# Simple Table Styles Configuration\n")
                f.write("# This file defines basic styling for table rows\n\n")
                toml.dump(styles, f)

            self.current_file = Path(filename)
            messagebox.showinfo(
                "Success", f"Saved styles to {Path(filename).name}")
            return True

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save TOML file: {e}")
            return False


class StyleEditorDialog:
    """Dialog for editing table styles with color pickers and TOML save/load."""

    def __init__(self, parent: tk.Tk):
        """Initialize the style editor dialog.

        Args:
            parent: Parent window
        """
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Simple Style Editor")
        self.dialog.geometry("600x700")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)

        # Style data structure
        self.styles = {
            'header_row': {
                'bg_color': '#2c3e50',
                'text_color': '#ecf0f1',
                'font_family': 'Arial',
                'font_size': 11,
                'font_weight': 'bold',
                'border_bottom_width': 2,
                'border_bottom_color': '#1a252f'
            },
            'even_rows': {
                'bg_color': '#ffffff',
                'text_color': '#2c3e50',
                'font_family': 'Arial',
                'font_size': 10,
                'font_weight': 'normal',
                'border_bottom_width': 1,
                'border_bottom_color': '#dee2e6'
            },
            'odd_rows': {
                'bg_color': '#f8f9fa',
                'text_color': '#2c3e50',
                'font_family': 'Arial',
                'font_size': 10,
                'font_weight': 'normal',
                'border_bottom_width': 1,
                'border_bottom_color': '#dee2e6'
            }
        }

        # Initialize helper classes
        self.data_manager = StyleDataManager(self.styles)
        self.widgets_map = {}  # Maps style_key -> widgets dict

        # Create UI
        self._create_ui()

        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (600 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (700 // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def _create_ui(self):
        """Create the dialog UI."""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Table Style Editor",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Notebook for different style categories
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create tab builder
        tab_builder = StyleTabBuilder(self.notebook, self.styles)

        # Create tabs for each style category
        for style_key, tab_title in [
            ('header_row', "Header Row"),
            ('even_rows', "Even Rows"),
            ('odd_rows', "Odd Rows")
        ]:
            frame, widgets = tab_builder.create_style_tab(tab_title, style_key)
            self.widgets_map[style_key] = widgets
            self.notebook.add(frame, text=tab_title)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # File operations
        ttk.Button(
            button_frame,
            text="Open TOML...",
            command=self.open_toml,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Save TOML...",
            command=self.save_toml,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 5))

        # Apply and Close
        ttk.Button(
            button_frame,
            text="Apply",
            command=self.apply_styles,
            width=15
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy,
            width=15
        ).pack(side=tk.RIGHT)


    def open_toml(self):
        """Open and load a TOML file."""
        filename = filedialog.askopenfilename(
            title="Open Style TOML",
            defaultextension=".toml",
            filetypes=[("TOML files", "*.toml"), ("All files", "*.*")]
        )

        if filename:
            # Create tab builder for preview updates
            tab_builder = StyleTabBuilder(self.notebook, self.styles)
            self.data_manager.load_from_toml(
                filename, self.widgets_map, tab_builder.update_preview)

    def save_toml(self):
        """Save current styles to a TOML file."""
        filename = filedialog.asksaveasfilename(
            title="Save Style TOML",
            defaultextension=".toml",
            filetypes=[("TOML files", "*.toml"), ("All files", "*.*")],
            initialfile="simple_styles.toml"
        )

        if filename:
            styles = self.data_manager.collect_styles(self.widgets_map)
            self.data_manager.save_to_toml(filename, styles)

    def apply_styles(self):
        """Apply the current styles (to be implemented by caller)."""
        try:
            styles = self.data_manager.collect_styles(self.widgets_map)
            self.styles = styles
            messagebox.showinfo(
                "Applied",
                "Styles have been updated.\n\nNote: You'll need to implement the apply logic in your application.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply styles: {e}")

    def get_styles(self) -> Dict:
        """Get the current styles.

        Returns:
            Dictionary of all styles
        """
        return self.data_manager.collect_styles(self.widgets_map)
