"""
Custom UI Components - Modern PyQt6 UI components with glassmorphism effects
"""

from .custom_dropdown import (
    CustomDropdown,
    CustomDropdownCompact,
    CustomDropdownLarge,
    CustomDropdownDelegate
)
from .custom_dialog import CustomMessageDialog
from .custom_titlebar import CustomTitleBar
from .custom_main_window import CustomMainWindow, THEMES
from .custom_button import CustomButton
from .custom_label import CustomLabel
from .custom_menu import CustomMenu
from .custom_scrollbar import CustomScrollBar, CustomVerticalScrollBar, CustomHorizontalScrollBar
from .colors.color_palette import (
    GLOBAL_COLOR_PALETTE,
    create_background_style,
    get_global_color,
    set_global_color_palette
)

__version__ = "1.0.1"
__author__ = "CrypterENC"
__email__ = "a95899003@gmail.com"
__description__ = "Modern PyQt6 UI components with glassmorphism effects and smooth animations"

__all__ = [
    "CustomDropdown",
    "CustomDropdownCompact",
    "CustomDropdownLarge",
    "CustomDropdownDelegate",
    "CustomMessageDialog",
    "CustomTitleBar",
    "CustomMainWindow",
    "CustomButton",
    "CustomLabel",
    "CustomMenu",
    "CustomScrollBar",
    "CustomVerticalScrollBar",
    "CustomHorizontalScrollBar",
    "THEMES",
    "GLOBAL_COLOR_PALETTE",
    "create_background_style",
    "get_global_color",
    "set_global_color_palette",
]
