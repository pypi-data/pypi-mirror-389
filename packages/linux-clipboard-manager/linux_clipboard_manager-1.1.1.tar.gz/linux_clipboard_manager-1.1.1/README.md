# 📋 Smart Clipboard Manager

<div align="center">

![Python](https://img.shields.io/badge/Python-3.7%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Linux-orange)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

A powerful clipboard manager with history, search, and smart categorization features.

[🚀 Quick Install](#-quick-install) • [📖 Features](#-features) • [🎯 Usage](#-usage) • [⚙️ Configuration](#️-configuration)

</div>

---

## ✨ Features

### 🎯 Core Features
- 📋 **Clipboard History**: Automatically saves your last 1000 clipboard entries
- 🔍 **Smart Search**: Full-text search across all clipboard history
- 🏷️ **Auto-Categorization**: Automatically detects URLs, emails, code, file paths, and more
- ⭐ **Favorites**: Pin frequently used clips for quick access
- 🔒 **Privacy Protection**: Automatically excludes sensitive content from password managers
- 🎯 **Deduplication**: Doesn't store identical content twice
- ⌨️ **Global Hotkey**: Quick access with Ctrl+Alt+V
- 🔄 **Auto-Refresh**: Shows newly copied items immediately

### 🎨 User Interface
- **Modern UI**: Clean, intuitive interface with dark/light theme support
- **Click-to-Copy**: Single click on any item to copy it to clipboard
- **Real-time Updates**: See new clipboard items appear instantly
- **Smart Filtering**: Filter by content type (URLs, Code, Favorites, etc.)
- **Preview Panel**: Full content preview with syntax highlighting for code

### 🛡️ Security & Privacy
- **Local Storage**: All data stored locally in SQLite database
- **No Cloud Sync**: By default, no data leaves your machine
- **App Exclusion**: Automatically excludes clipboard content from password managers
- **Sensitive Content Detection**: Detects and optionally excludes passwords, credit cards, etc.

---

## 🚀 Quick Install

### Option 1: Install via pipx (Recommended)

```bash
# Install pipx if you don't have it
sudo apt install pipx
pipx ensurepath

# Install from PyPI
pipx install linux-clipboard-manager
```

### Option 2: Install from source

```bash
# Install from GitHub
pipx install git+https://github.com/krakujs/linux-clipboard-manager.git
```

### Option 3: One-Click System Installation

```bash
# Download and run the installation script (installs system dependencies + app)
curl -fsSL https://raw.githubusercontent.com/krakujs/linux-clipboard-manager/master/install-system.sh | bash
```

---

## 🎯 Usage

### After Installation

1. **Start the Application**: Run `smart-clipboard` in a terminal to start the background service
2. **Open the UI**: Press `Ctrl+Alt+V` to toggle the clipboard manager window (while service is running)
3. **Or Open GUI Directly**: Run `smart-clipboard-gui` to open just the UI
4. **Copy Items**: Click on any item to copy it to your clipboard
5. **Search**: Type in the search box to filter clipboard history
6. **Filter by Type**: Click buttons to filter by content type (All, URLs, Code, Favorites)

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Alt+V` | Toggle clipboard manager window |
| `Enter` | Paste selected clip |
| `Escape` | Close window |
| `Double-click` | Paste selected clip |

### Command Line Usage

```bash
# Start background service (monitors clipboard + hotkey)
smart-clipboard

# Open GUI only (no background monitoring)
smart-clipboard-gui

# Start with UI visible
smart-clipboard --show-ui
```

---

## ⚙️ Configuration

The configuration file is located at: `~/.smart-clipboard/config.json`

### Default Configuration

```json
{
  "max_history": 1000,
  "monitor_interval": 0.5,
  "hotkey": "<ctrl>+<alt>+v",
  "database_path": "clipboard.db",
  "max_content_size": 1048576,
  "enable_encryption": false,
  "excluded_apps": ["KeePass", "1Password", "LastPass"],
  "categories": {
    "url": true,
    "email": true,
    "code": true,
    "image": true
  },
  "ui": {
    "max_preview_length": 100,
    "window_width": 600,
    "window_height": 400,
    "theme": "light"
  }
}
```

### Customizing the Hotkey

Edit the `hotkey` field in config.json. Examples:
- `<ctrl>+<alt>+v` (default)
- `<ctrl>+<shift>+c`
- `<cmd>+<shift>+v` (macOS)

---

## 📦 System Requirements

### Linux
- Python 3.7 or higher
- pip (Python package manager)
- System dependencies:
  ```bash
  sudo apt install python3 python3-pip python3-venv python3-full sqlite3 xdotool
  ```

### Other Platforms
- Windows: Additional `pywin32` and `psutil` packages required
- macOS: No additional dependencies needed (uses built-in AppleScript)

---

## 🔧 Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/your-username/smart-clipboard-manager.git
cd smart-clipboard-manager

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

### Project Structure

```
smart-clipboard-manager/
├── src/
│   ├── __init__.py
│   ├── clipboard_monitor.py    # Background clipboard monitoring
│   ├── storage.py               # SQLite storage engine
│   ├── ui.py                    # Tkinter GUI interface
│   ├── hotkey_handler.py        # Global hotkey management
│   ├── content_analyzer.py      # Content categorization
│   └── config.py                # Configuration management
├── tests/                       # Test suite
├── requirements.txt             # Python dependencies
├── setup.py                     # Package configuration
├── install-system.sh           # System installation script
├── main.py                      # Application entry point
└── README.md                    # This file
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](https://github.com/krakujs/linux-clipboard-manager/blob/master/CONTRIBUTING.md) for details.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [pyperclip](https://github.com/asweigart/pyperclip) for cross-platform clipboard access
- [pynput](https://github.com/moses-palmer/pynput) for global hotkey handling
- [Tkinter](https://docs.python.org/3/library/tkinter.html) for the GUI framework

---

## 📞 Support

- 🐛 **Bug Reports**: [Open an issue](https://github.com/krakujs/linux-clipboard-manager/issues)
- 💡 **Feature Requests**: [Open an issue](https://github.com/krakujs/linux-clipboard-manager/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/krakujs/linux-clipboard-manager/discussions)

---

## 🔄 Changelog

### v1.0.1 (2024-11-05)
- 🔧 **Changed hotkey** from Ctrl+Shift+V to Ctrl+Alt+V to avoid conflicts
- 📚 **Updated documentation** with new hotkey information
- 🐛 **Fixed hotkey collision** issues with other applications

### v1.0.0 (2024-11-05)
- ✨ Initial release
- 📋 Clipboard history with 1000 item limit
- 🔍 Full-text search functionality
- 🏷️ Smart content categorization
- ⭐ Favorites system
- ⌨️ Global hotkey support
- 🔄 Auto-refresh functionality
- 🖥️ Modern UI with click-to-copy
- 🔧 System service integration
- 📦 Easy installation scripts

---

<div align="center">

**Made with ❤️ for productivity enthusiasts**

[⭐ Star this repo](https://github.com/krakujs/linux-clipboard-manager) • [🐛 Report issues](https://github.com/krakujs/linux-clipboard-manager/issues) • [💬 Start a discussion](https://github.com/krakujs/linux-clipboard-manager/discussions)

</div>
