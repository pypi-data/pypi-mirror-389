# Custom UI Components for PyQt6

[![PyPI version](https://badge.fury.io/py/custom-ui-pyqt6.svg)](https://badge.fury.io/py/custom-ui-pyqt6)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Modern, reusable PyQt6 UI components with glassmorphism effects and smooth animations. Perfect for building beautiful, modern desktop applications.

## Features

✨ **Modern Design**
- Gradient backgrounds
- Semi-transparent glassmorphism effects
- Smooth hover transitions
- Professional typography

🎯 **User-Friendly**
- Draggable windows
- Clear visual hierarchy
- Intuitive interactions
- Responsive feedback

🔄 **Reusable**
- Easy to integrate into any PyQt6 project
- Customizable colors and styles
- Modular components
- Well-documented

🎨 **Themeable**
- 5 predefined color themes
- Runtime theme switching
- Custom color support
- Flexible styling system

## Installation

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

## Quick Start

### Basic Window Setup

```python
import sys
from PyQt6.QtWidgets import QApplication, QPushButton, QLabel
from PyQt6.QtGui import QFont
from custom_ui_package import CustomMainWindow

class MyApp(CustomMainWindow):
    def __init__(self):
        super().__init__(
            title='My Application',
            width=600,
            height=750,
            theme='dark_blue'
        )
        
        # Add content
        title = QLabel('Welcome!')
        title.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        self.add_content(title)
        
        btn = QPushButton('Click Me')
        self.add_content(btn)
        
        self.add_stretch()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())
```

## Components

### CustomMainWindow

A frameless main window with custom title bar and customizable styling.

```python
from custom_ui_package import CustomMainWindow

window = CustomMainWindow(
    title='My App',
    width=600,
    height=750,
    theme='dark_purple'
)

# Change theme at runtime
window.set_theme('dark_green')
```

### CustomDropdown

A modern dropdown widget with glassmorphism effects.

```python
from custom_ui_package import CustomDropdown

dropdown = CustomDropdown()
dropdown.add_items_with_icons({
    'Option 1': 'value1',
    'Option 2': 'value2',
    'Option 3': 'value3'
})

selected_text = dropdown.get_selected_text()
```

### CustomMessageDialog

A modern message dialog with draggable interface.

```python
from custom_ui_package import CustomMessageDialog

dialog = CustomMessageDialog(
    'Information',
    'This is an info message',
    'info',
    parent_widget
)
dialog.exec()
```

### CustomTitleBar

A custom title bar for frameless windows.

```python
from custom_ui_package import CustomTitleBar

title_bar = CustomTitleBar(
    parent=window,
    title="My Application",
    icon_path=None,
    show_minimize=True,
    show_close=True
)
```

## Themes

Available predefined themes:

- **dark_blue** (default) - Modern blue gradient with indigo buttons
- **dark_purple** - Purple gradient with vibrant purple buttons
- **dark_green** - Green gradient with emerald buttons
- **dark_orange** - Orange gradient with warm orange buttons
- **dark_red** - Red gradient with crimson buttons

```python
# Use a theme
window = CustomMainWindow(theme='dark_purple')

# Change theme at runtime
window.set_theme('dark_green')

# Custom colors
window.set_custom_colors({
    'button_start': '#ff6b6b',
    'button_end': '#ee5a6f'
})
```

## Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Primary | #6366f1 | Indigo - Main buttons |
| Secondary | #4f46e5 | Purple - Button end gradient |
| Accent | #a5f3fc | Cyan - Secondary text |
| Background | #0a0e27 | Dark Blue - Window background |
| Text Primary | #e8f0ff | Light Blue - Main text |
| Text Secondary | #a5f3fc | Cyan - Secondary text |
| Warning | #eab308 | Yellow - Warning elements |
| Error | #ef4444 | Red - Error elements |
| Success | #10b981 | Green - Success elements |

## Customization

All components support extensive customization:

- **CustomMainWindow**: Use `set_theme()` and `set_custom_colors()` to customize
- **CustomDropdown**: Use `set_custom_colors()` for color customization
- **CustomMessageDialog**: Pass different `icon_type` values: "info", "warning", "error"
- **CustomTitleBar**: Customize title, icon, and button visibility

## Components Overview

| Component | Purpose | Features |
|-----------|---------|----------|
| `CustomMainWindow` | Main application window | Frameless, custom title bar, themeable, draggable |
| `CustomDropdown` | Standard dropdown | Glassmorphism, smooth animations, custom colors |
| `CustomDropdownCompact` | Compact dropdown | Smaller height variant |
| `CustomDropdownLarge` | Large dropdown | Larger height variant |
| `CustomMessageDialog` | Message dialog | Frameless, draggable, icon support |
| `CustomTitleBar` | Window title bar | Minimize/close buttons, draggable, icon support |

## Requirements

- Python 3.8+
- PyQt6 >= 6.0.0

## Documentation

For detailed documentation, see:

- **DOCUMENTATION.md** - Complete user guide with examples
- **SETUP_AND_PUBLISHING.md** - Setup and PyPI publishing guide
- **CHANGELOG.md** - Version history

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please open an issue on the [GitHub repository](https://github.com/yourusername/custom-ui-pyqt6/issues).

---

**Happy building! 🚀**
