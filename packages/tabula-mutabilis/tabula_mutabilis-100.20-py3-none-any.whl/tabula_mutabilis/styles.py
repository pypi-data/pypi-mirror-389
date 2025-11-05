"""Style management for Tabula Mutabilis table widget.

This module provides styling abstractions:
- TableStyleProvider: Manages cell styles with theme integration
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
import tkinter as tk

from vultus_serpentis import Observable

from .model import CellStyle


class TableStyleProvider(Observable):
    """Manages styling for table cells with theme integration.

    Provides base styles, rule-based overrides, and theme-aware defaults.
    Supports live theme changes through observer pattern.
    """

    def __init__(self, theme_colors: Dict[str, str], theme_fonts: Dict[str, str]) -> None:
        """Initialize the style provider with theme data.

        Args:
            theme_colors: Dict mapping color names to hex values
            theme_fonts: Dict mapping font names to font specs
        """
        super().__init__()
        self.theme_colors = theme_colors.copy()
        self.theme_fonts = theme_fonts.copy()

        # Style storage
        self.base_styles: Dict[str, CellStyle] = {}
        self.style_rules: Dict[str, Any] = {}
        self.style_overrides: Dict[Tuple[int, int], CellStyle] = {}
        self.style_cache: Dict[Tuple[int, int, bool], CellStyle] = {}

        # Initialize with theme defaults
        self.load_defaults_from_theme()

    def load_defaults_from_theme(self) -> None:
        """Load default styles from the current theme.

        Creates base styles for 'default', 'header', 'selected', and 'zebra'.
        """
        # Default cell style
        self.base_styles['default'] = CellStyle(
            font=self._parse_font_spec(self.theme_fonts.get('body', 'TkDefaultFont 10')),
            text_color=self.theme_colors.get('fg', '#000000'),
            bg_color=self.theme_colors.get('bg', '#FFFFFF'),
            row_height=25,
            col_width=100,
            horiz_justify='w',
            vert_justify='center',
        )

        # Header style
        self.base_styles['header'] = CellStyle(
            font=self._parse_font_spec(self.theme_fonts.get('header', 'TkDefaultFont 10 bold')),
            text_color=self.theme_colors.get('primary_fg', '#FFFFFF'),
            bg_color=self.theme_colors.get('primary', '#0078D4'),
            row_height=30,
            col_width=100,
            horiz_justify='center',
            vert_justify='center',
        )

        # Selected cell style
        self.base_styles['selected'] = CellStyle(
            font=self._parse_font_spec(self.theme_fonts.get('body', 'TkDefaultFont 10')),
            text_color=self.theme_colors.get('primary_fg', '#FFFFFF'),
            bg_color=self.theme_colors.get('primary', '#0078D4'),
            row_height=25,
            col_width=100,
            horiz_justify='w',
            vert_justify='center',
        )

        # Zebra striping (alternate row colors)
        self.base_styles['zebra'] = CellStyle(
            font=self._parse_font_spec(self.theme_fonts.get('body', 'TkDefaultFont 10')),
            text_color=self.theme_colors.get('fg', '#000000'),
            bg_color=self.theme_colors.get('secondary', '#F3F2F1'),
            row_height=25,
            col_width=100,
            horiz_justify='w',
            vert_justify='center',
        )

    def _parse_font_spec(self, font_spec) -> Tuple[str, int]:
        """Parse a font specification into (family, size) tuple.

        Args:
            font_spec: Font spec like 'Arial 12' or ('Arial', 12)

        Returns:
            Tuple of (font_family, font_size)
        """
        if isinstance(font_spec, tuple) and len(font_spec) >= 2:
            return (str(font_spec[0]), int(font_spec[1]))

        if isinstance(font_spec, str):
            parts = font_spec.split()
            if len(parts) >= 2:
                try:
                    size = int(parts[1])
                    family = parts[0]
                    return (family, size)
                except (ValueError, IndexError):
                    pass

        # Fallback to default
        return ('TkDefaultFont', 10)

    def update_theme(self, theme_colors: Dict[str, str], theme_fonts: Dict[str, str]) -> None:
        """Update the theme and refresh all styles.

        Called when TTK Bootstrap theme changes.

        Args:
            theme_colors: New color mapping
            theme_fonts: New font mapping
        """
        # Preserve cell editor classes before reloading
        editor_classes = {
            name: style.cell_editor_class
            for name, style in self.base_styles.items()
            if style.cell_editor_class is not None
        }

        self.theme_colors = theme_colors.copy()
        self.theme_fonts = theme_fonts.copy()
        self.load_defaults_from_theme()

        # Restore cell editor classes after theme reload
        for name, editor_class in editor_classes.items():
            if name in self.base_styles:
                self.base_styles[name] = self.base_styles[name].copy(cell_editor_class=editor_class)

        self.clear_cache()
        self._notify_observers(event_type='theme_changed')

    def register_base_style(self, name: str, style: CellStyle) -> None:
        """Register a new base style.

        Args:
            name: Style name (e.g., 'error', 'warning')
            style: The CellStyle to register
        """
        self.base_styles[name] = style
        self.clear_cache()
        self._notify_observers(event_type='style_registered', payload={'name': name})

    def set_row_style_rule(self, row_index: int, style_name: str) -> None:
        """Set a style rule for a specific row.

        Args:
            row_index: Row index (0-based)
            style_name: Name of base style to apply
        """
        self.style_rules[f'row_{row_index}'] = style_name
        self.clear_cache()
        self._notify_observers(event_type='rule_changed', payload={'type': 'row', 'index': row_index})

    def set_column_style_rule(self, col_index: int, style_name: str) -> None:
        """Set a style rule for a specific column.

        Args:
            col_index: Column index (0-based)
            style_name: Name of base style to apply
        """
        self.style_rules[f'col_{col_index}'] = style_name
        self.clear_cache()
        self._notify_observers(event_type='rule_changed', payload={'type': 'column', 'index': col_index})

    def set_zebra_rule(self, enabled: bool = True, start_row: int = 0) -> None:
        """Enable or disable zebra striping.

        Args:
            enabled: Whether to enable zebra striping
            start_row: Row index to start zebra pattern (0-based)
        """
        if enabled:
            self.style_rules['zebra'] = {'enabled': True, 'start_row': start_row}
        else:
            self.style_rules.pop('zebra', None)
        self.clear_cache()
        self._notify_observers(event_type='rule_changed', payload={'type': 'zebra', 'enabled': enabled})

    def set_cell_override(self, row: int, col: int, style: CellStyle) -> None:
        """Set a style override for a specific cell.

        Args:
            row: Row index (0-based)
            col: Column index (0-based)
            style: The override style
        """
        self.style_overrides[(row, col)] = style
        self.clear_cache()
        self._notify_observers(event_type='cell_override_set', payload={'row': row, 'col': col})

    def clear_cell_override(self, row: int, col: int) -> None:
        """Remove a style override for a specific cell.

        Args:
            row: Row index (0-based)
            col: Column index (0-based)
        """
        self.style_overrides.pop((row, col), None)
        self.clear_cache()
        self._notify_observers(event_type='cell_override_cleared', payload={'row': row, 'col': col})

    def clear_cache(self) -> None:
        """Clear the style cache.

        Should be called whenever styles or rules change.
        """
        self.style_cache.clear()
        self._notify_observers(event_type='style_changed')

    def get_effective_style(self, row: int, col: int, is_selected: bool = False) -> CellStyle:
        """Get the effective style for a cell, combining all applicable rules.

        Args:
            row: Row index (0-based)
            col: Column index (0-based)
            is_selected: Whether the cell is currently selected

        Returns:
            The effective CellStyle for the cell
        """
        import logging
        logger = logging.getLogger('TabulaMutabilis.Styles')
        
        cache_key = (row, col, is_selected)
        if cache_key in self.style_cache:
            return self.style_cache[cache_key]

        # Start with default style
        style = self.base_styles['default'].copy()
        logger.debug(f"get_effective_style({row}, {col}, selected={is_selected})")
        logger.debug(f"  Default style editor: {style.cell_editor_class}")

        # Apply row rules
        if f'row_{row}' in self.style_rules:
            rule_style = self.base_styles.get(self.style_rules[f'row_{row}'])
            if rule_style:
                style = rule_style.copy()

        # Apply column rules (override row rules)
        if f'col_{col}' in self.style_rules:
            rule_style = self.base_styles.get(self.style_rules[f'col_{col}'])
            if rule_style:
                style = rule_style.copy()

        # Apply zebra striping
        if 'zebra' in self.style_rules:
            zebra_config = self.style_rules['zebra']
            if zebra_config.get('enabled', False):
                start_row = zebra_config.get('start_row', 0)
                if (row - start_row) % 2 == 1:  # Odd rows get zebra style
                    zebra_style = self.base_styles.get('zebra')
                    if zebra_style:
                        # Only override background color for zebra, preserve editor
                        style = style.copy(bg_color=zebra_style.bg_color)

        # Apply cell-specific overrides (high priority, but not highest)
        if (row, col) in self.style_overrides:
            override_style = self.style_overrides[(row, col)]
            style = override_style.copy()

        # Apply selection (HIGHEST priority - always on top)
        if is_selected:
            logger.debug(f"  Cell is selected, applying selection style")
            selected_style = self.base_styles.get('selected')
            if selected_style:
                # Preserve the cell editor from the current style
                editor_class = style.cell_editor_class
                logger.debug(f"  Editor before selection: {editor_class}")
                # Only override visual properties for selection, keep everything else
                style = style.copy(
                    bg_color=selected_style.bg_color,
                    text_color=selected_style.text_color
                )
                logger.debug(f"  Applied selection colors, editor preserved: {style.cell_editor_class}")

        self.style_cache[cache_key] = style
        return style