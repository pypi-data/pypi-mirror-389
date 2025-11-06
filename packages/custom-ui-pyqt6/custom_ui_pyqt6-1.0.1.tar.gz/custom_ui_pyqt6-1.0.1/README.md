# Custom UI Components for PyQt6

[![PyPI version](https://badge.fury.io/py/custom-ui-pyqt6.svg)](https://badge.fury.io/py/custom-ui-pyqt6)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Modern, reusable PyQt6 UI components with glassmorphism effects and smooth animations. Perfect for building beautiful, modern desktop applications with solid color theming.

## ✨ Features

🎨 **Modern Design**
- Solid color backgrounds with transparency effects
- Semi-transparent glassmorphism effects
- Smooth hover transitions and animations
- Professional typography and spacing

🎯 **User-Friendly**
- Draggable frameless windows
- Clear visual hierarchy
- Intuitive interactions
- Responsive visual feedback

🔄 **Reusable & Flexible**
- Easy to integrate into any PyQt6 project
- Highly customizable colors and styles
- Modular component architecture
- Well-documented with examples

🎨 **Solid Color Theming**
- Direct color assignment (no complex gradient setup)
- Runtime color updates
- Hex (#RRGGBB) and RGBA color support
- Consistent color palette across components

## 📦 Installation

Install from PyPI:
```bash
pip install custom-ui-pyqt6
```

Or install from source:
```bash
git clone https://github.com/yourusername/custom-ui-pyqt6.git
cd custom-ui-pyqt6
pip install -e .
```

## 🚀 Quick Start

### Basic Application

```python
import sys
from PyQt6.QtWidgets import QApplication
from custom_ui_package import CustomMainWindow, CustomTitleBar, CustomLabel, CustomButton

class MyApp(CustomMainWindow):
    def __init__(self):
        super().__init__(
            title='My Application',
            width=600,
            height=500,
            bg_color='#1a0f2e'  # Solid color background
        )

        # Add custom title bar
        title_bar = CustomTitleBar(
            parent=self,
            title='My Application',
            bg_color='#7a00ff',
            text_color='#e8f0ff',
            font_size=16,
            bold=True
        )
        self.centralWidget().layout().insertWidget(0, title_bar)

        # Add content
        welcome_label = CustomLabel(
            parent=self.overlay_widget,
            text='Welcome to My App!',
            size=(300, 40),
            position=(40, 30),
            font_size=20,
            bold=True,
            color='#a855f7'
        )

        button = CustomButton(
            parent=self.content_widget,
            title='Get Started',
            size=(150, 45),
            font_size=12
        )
        button.clicked.connect(self.get_started)
        self.add_content(button)

        self.add_stretch()

    def get_started(self):
        print("Getting started!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())
```

## 🎛️ Components

### CustomMainWindow

Frameless main window with solid color backgrounds and customizable styling.

```python
from custom_ui_package import CustomMainWindow

window = CustomMainWindow(
    title='My App',
    width=800,
    height=600,
    bg_color='#1a0f2e'  # Solid background color
)

# Runtime color updates
window.set_custom_colors({
    'button_color': '#ec4899',
    'text_primary': '#f3e8ff'
})
```

### CustomTitleBar

Custom title bar for frameless windows with configurable fonts and colors.

```python
from custom_ui_package import CustomTitleBar

title_bar = CustomTitleBar(
    parent=window,
    title="My Application",
    bg_color='#7a00ff',
    text_color='#e8f0ff',
    font_size=16,        # Custom font size
    bold=True,           # Bold text
    show_minimize=True,
    show_close=True
)
```

### CustomLabel

Configurable label with support for both layout-managed and absolute positioning.

```python
from custom_ui_package import CustomLabel

# Content area label (layout-managed)
content_label = CustomLabel(
    parent=self.content_widget,
    text="Hello World",
    size=(150, 30),
    font_size=12,
    bold=True
)
self.add_content(content_label)

# Overlay label (absolute positioning)
overlay_label = CustomLabel(
    parent=self.overlay_widget,
    text="Section Title",
    size=(200, 40),
    position=(40, 20),
    font_size=16,
    color='#a855f7'
)
```

### CustomButton

Modern button component with hover effects and custom styling.

```python
from custom_ui_package import CustomButton

button = CustomButton(
    parent=self.content_widget,
    title="Click Me",
    size=(150, 45),
    font_size=12,
    color='#ec4899'  # Custom button color
)
button.clicked.connect(self.handle_click)
self.add_content(button)
```

### CustomDropdown

Modern dropdown with glassmorphism effects and smooth animations.

```python
from custom_ui_package import CustomDropdown

dropdown = CustomDropdown()
dropdown.add_items_with_icons({
    'Python': 'python',
    'JavaScript': 'javascript',
    'Go': 'go'
})

# Customize colors
dropdown.set_custom_colors(
    bg_color='rgba(20, 25, 50, 0.8)',
    text_color='#e0e7ff',
    hover_color='#a78bfa'
)

selected_text = dropdown.get_selected_text()
```

### CustomMessageDialog

Modern message dialog with draggable interface and multiple dialog types.

```python
from custom_ui_package import CustomMessageDialog

# Different dialog types
info_dialog = CustomMessageDialog(
    'Information',
    'This is an info message',
    'info',
    parent_window
)

warning_dialog = CustomMessageDialog(
    'Warning',
    'This is a warning',
    'warning',
    parent_window
)

error_dialog = CustomMessageDialog(
    'Error',
    'This is an error',
    'error',
    parent_window
)

info_dialog.exec()
```

### CustomMenu

Context/application menu with glassmorphism effects, icons, and submenus.

```python
from custom_ui_package import CustomMenu

menu = CustomMenu(title='File')
menu.add_item('New', callback=lambda: print('New'))
menu.add_item('Open', callback=lambda: print('Open'))
menu.add_separator()
menu.add_item('Exit', callback=lambda: print('Exit'))

# With icons and shortcuts
menu.add_item('Copy', icon_path='copy.png', shortcut='Ctrl+C')
menu.add_item('Paste', icon_path='paste.png', shortcut='Ctrl+V')

# Submenu
submenu = menu.add_submenu('Recent Files')
submenu.add_item('File 1.txt')
submenu.add_item('File 2.txt')

# Checkable items
menu.add_item('Show Grid', checkable=True, checked=True)
```

### CustomScrollBar

Modern scrollbar with glassmorphism effects and smooth animations.

```python
from custom_ui_package import CustomMainWindow, CustomVerticalScrollBar

class MyScrollableApp(CustomMainWindow):
    def __init__(self):
        super().__init__(
            title='Scrollable App',
            width=600,
            height=750,
            bg_color='#1a0f2e',
            use_custom_scrollbar=True,
            scrollbar_color='#a855f7',
            scrollbar_width=10
        )

# Or create manually
from custom_ui_package import CustomVerticalScrollBar

scrollbar = CustomVerticalScrollBar(
    handle_color='#a855f7',
    handle_width=10,
    border_radius=8,
    opacity=0.8
)
```

## 🎨 Color Theming

### Solid Color System

The library now uses a simple solid color system instead of complex gradients:

```python
# Define colors directly
PRIMARY_COLOR = '#a855f7'
BACKGROUND_COLOR = '#1a0f2e'
TEXT_COLOR = '#f3e8ff'

# Use in components
window = CustomMainWindow(bg_color=BACKGROUND_COLOR)

title_bar = CustomTitleBar(
    bg_color=PRIMARY_COLOR,
    text_color=TEXT_COLOR
)

button = CustomButton(color=PRIMARY_COLOR)
```

### Color Formats Supported

- **Hex**: `#RRGGBB` (e.g., `#a855f7`)
- **RGBA**: `rgba(r, g, b, a)` (e.g., `rgba(168, 85, 247, 0.8)`)

### Runtime Color Updates

```python
# Update window colors
window.set_custom_colors({
    'button_color': '#ec4899',
    'text_primary': '#f3e8ff'
})

# Update component colors
dropdown.set_custom_colors(
    bg_color='rgba(20, 25, 50, 0.8)',
    text_color='#e0e7ff'
)

# Update scrollbar colors
scrollbar.update_colors(
    handle_color='#a855f7',
    background_color='#2d1b4e'
)
```

## 📋 Components Overview

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| `CustomMainWindow` | Main application window | Frameless, solid backgrounds, layout management |
| `CustomTitleBar` | Window title bar | Configurable fonts, colors, minimize/close buttons |
| `CustomButton` | Interactive buttons | Hover effects, custom colors, click handling |
| `CustomLabel` | Text display | Layout-managed or absolute positioning |
| `CustomDropdown` | Selection dropdown | Glassmorphism, icons, smooth animations |
| `CustomDropdownCompact` | Compact dropdown | Smaller variant for space-constrained UI |
| `CustomDropdownLarge` | Large dropdown | Larger variant for better accessibility |
| `CustomMessageDialog` | Message dialogs | Draggable, multiple types (info/warning/error) |
| `CustomMenu` | Context menus | Icons, submenus, checkable items, shortcuts |
| `CustomScrollBar` | Custom scrollbars | Glassmorphism, vertical/horizontal variants |
| `CustomVerticalScrollBar` | Vertical scrollbar | Convenience class for vertical scrolling |
| `CustomHorizontalScrollBar` | Horizontal scrollbar | Convenience class for horizontal scrolling |

## 📚 Documentation & Examples

- **[DOCUMENTATION.md](DOCUMENTATION.md)** - Complete user guide with detailed examples
- **[SETUP_AND_PUBLISHING.md](SETUP_AND_PUBLISHING.md)** - Setup and PyPI publishing guide
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and updates

## 🔧 Requirements

- Python 3.8+
- PyQt6 >= 6.0.0

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions, please open an issue on the [GitHub repository](https://github.com/yourusername/custom-ui-pyqt6/issues).

---

**Happy building! 🚀**
