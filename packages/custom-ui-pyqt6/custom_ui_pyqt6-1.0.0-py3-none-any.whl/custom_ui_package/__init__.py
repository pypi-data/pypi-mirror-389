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

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__description__ = "Modern PyQt6 UI components with glassmorphism effects and smooth animations"

__all__ = [
    "CustomDropdown",
    "CustomDropdownCompact",
    "CustomDropdownLarge",
    "CustomDropdownDelegate",
    "CustomMessageDialog",
    "CustomTitleBar",
    "CustomMainWindow",
    "THEMES",
]
