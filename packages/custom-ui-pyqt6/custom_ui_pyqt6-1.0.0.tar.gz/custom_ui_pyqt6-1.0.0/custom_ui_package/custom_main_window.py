"""
Custom Main Window - A reusable frameless main window with custom title bar
Provides a base class for creating modern, draggable windows with customizable styling
"""

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from .custom_titlebar import CustomTitleBar


# Predefined color themes
THEMES = {
    'dark_blue': {
        'bg_gradient_start': '#0a0e27',
        'bg_gradient_end': '#0f1535',
        'button_start': '#6366f1',
        'button_end': '#4f46e5',
        'button_hover_start': '#7c3aed',
        'button_hover_end': '#6366f1',
        'button_pressed_start': '#4338ca',
        'button_pressed_end': '#3730a3',
        'text_primary': '#e8f0ff',
        'text_secondary': '#a5f3fc',
        'border_color': 'rgba(99, 102, 241, 0.3)',
        'border_bg': 'rgba(99, 102, 241, 0.1)',
    },
    'dark_purple': {
        'bg_gradient_start': '#1a0f2e',
        'bg_gradient_end': '#2d1b4e',
        'button_start': '#a855f7',
        'button_end': '#9333ea',
        'button_hover_start': '#c084fc',
        'button_hover_end': '#a855f7',
        'button_pressed_start': '#7e22ce',
        'button_pressed_end': '#6b21a8',
        'text_primary': '#f3e8ff',
        'text_secondary': '#e9d5ff',
        'border_color': 'rgba(168, 85, 247, 0.3)',
        'border_bg': 'rgba(168, 85, 247, 0.1)',
    },
    'dark_green': {
        'bg_gradient_start': '#0f2818',
        'bg_gradient_end': '#1a3a2a',
        'button_start': '#10b981',
        'button_end': '#059669',
        'button_hover_start': '#34d399',
        'button_hover_end': '#10b981',
        'button_pressed_start': '#047857',
        'button_pressed_end': '#065f46',
        'text_primary': '#d1fae5',
        'text_secondary': '#a7f3d0',
        'border_color': 'rgba(16, 185, 129, 0.3)',
        'border_bg': 'rgba(16, 185, 129, 0.1)',
    },
    'dark_orange': {
        'bg_gradient_start': '#2a1810',
        'bg_gradient_end': '#3d2817',
        'button_start': '#f97316',
        'button_end': '#ea580c',
        'button_hover_start': '#fb923c',
        'button_hover_end': '#f97316',
        'button_pressed_start': '#c2410c',
        'button_pressed_end': '#92400e',
        'text_primary': '#fed7aa',
        'text_secondary': '#fdba74',
        'border_color': 'rgba(249, 115, 22, 0.3)',
        'border_bg': 'rgba(249, 115, 22, 0.1)',
    },
    'dark_red': {
        'bg_gradient_start': '#2a0f0f',
        'bg_gradient_end': '#3d1a1a',
        'button_start': '#ef4444',
        'button_end': '#dc2626',
        'button_hover_start': '#f87171',
        'button_hover_end': '#ef4444',
        'button_pressed_start': '#b91c1c',
        'button_pressed_end': '#7f1d1d',
        'text_primary': '#fee2e2',
        'text_secondary': '#fecaca',
        'border_color': 'rgba(239, 68, 68, 0.3)',
        'border_bg': 'rgba(239, 68, 68, 0.1)',
    },
}


class CustomMainWindow(QMainWindow):
    """
    A frameless main window with a custom title bar and customizable styling.
    
    Features:
    - Frameless window design
    - Custom draggable title bar
    - Modern gradient background
    - Smooth button transitions
    - Customizable color themes
    - Easy to extend for custom applications
    
    Args:
        title (str): Window title
        width (int): Window width in pixels (default: 600)
        height (int): Window height in pixels (default: 750)
        icon_path (str, optional): Path to window icon
        show_minimize (bool): Show minimize button in title bar (default: True)
        show_close (bool): Show close button in title bar (default: True)
        theme (str): Theme name from THEMES dict (default: 'dark_blue')
        custom_colors (dict, optional): Custom color dictionary to override theme
    """
    
    def __init__(self, title='Custom Window', width=600, height=750, 
                 icon_path=None, show_minimize=True, show_close=True,
                 theme='dark_blue', custom_colors=None):
        super().__init__()
        self.setGeometry(100, 100, width, height)
        self.setWindowTitle(title)
        
        # Apply frameless window style - removes default title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        
        # Load theme colors
        if theme in THEMES:
            self.colors = THEMES[theme].copy()
        else:
            self.colors = THEMES['dark_blue'].copy()
        
        # Override with custom colors if provided
        if custom_colors:
            self.colors.update(custom_colors)
        
        # Apply stylesheet with theme colors
        self._apply_stylesheet()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add custom title bar
        self.title_bar = CustomTitleBar(
            parent=self,
            title=title,
            icon_path=icon_path,
            show_minimize=show_minimize,
            show_close=show_close
        )
        layout.addWidget(self.title_bar)
        
        # Create content area widget (to be populated by subclasses)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(40, 30, 40, 30)
        self.content_layout.setSpacing(15)
        
        layout.addWidget(self.content_widget)
    
    def _apply_stylesheet(self):
        """Apply stylesheet with current theme colors"""
        stylesheet = f"""
            QMainWindow {{ 
                background: linear-gradient(135deg, {self.colors['bg_gradient_start']} 0%, {self.colors['bg_gradient_end']} 100%); 
            }}
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {self.colors['button_start']}, stop:1 {self.colors['button_end']});
                border: none;
                border-radius: 12px;
                padding: 15px 20px;
                color: #ffffff;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {self.colors['button_hover_start']}, stop:1 {self.colors['button_hover_end']});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {self.colors['button_pressed_start']}, stop:1 {self.colors['button_pressed_end']});
            }}
        """
        self.setStyleSheet(stylesheet)
    
    def set_theme(self, theme_name):
        """
        Change the window theme.
        
        Args:
            theme_name (str): Name of theme from THEMES dict
        """
        if theme_name in THEMES:
            self.colors = THEMES[theme_name].copy()
            self._apply_stylesheet()
    
    def set_custom_colors(self, colors_dict):
        """
        Set custom colors for the window.
        
        Args:
            colors_dict (dict): Dictionary with color keys to override
                Expected keys: bg_gradient_start, bg_gradient_end, button_start, button_end,
                              button_hover_start, button_hover_end, button_pressed_start, 
                              button_pressed_end, text_primary, text_secondary, 
                              border_color, border_bg
        """
        self.colors.update(colors_dict)
        self._apply_stylesheet()
    
    def get_theme_colors(self):
        """
        Get current theme colors.
        
        Returns:
            dict: Current color configuration
        """
        return self.colors.copy()
    
    def add_content(self, widget):
        """
        Add a widget to the content area.
        
        Args:
            widget (QWidget): Widget to add to content area
        """
        self.content_layout.addWidget(widget)
    
    def add_stretch(self):
        """Add stretch to push remaining content to top"""
        self.content_layout.addStretch()
    
    def set_title(self, title):
        """
        Update the window title.
        
        Args:
            title (str): New title text
        """
        self.setWindowTitle(title)
        self.title_bar.set_title(title)
    
    def set_content_margins(self, left, top, right, bottom):
        """
        Set content area margins.
        
        Args:
            left (int): Left margin in pixels
            top (int): Top margin in pixels
            right (int): Right margin in pixels
            bottom (int): Bottom margin in pixels
        """
        self.content_layout.setContentsMargins(left, top, right, bottom)
    
    def set_content_spacing(self, spacing):
        """
        Set spacing between content widgets.
        
        Args:
            spacing (int): Spacing in pixels
        """
        self.content_layout.setSpacing(spacing)
