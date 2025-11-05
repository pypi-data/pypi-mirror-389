#!/bin/bash
# Installation script for Smart Clipboard Manager on Linux

set -e

echo "🚀 Installing Smart Clipboard Manager..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if running as root for system-wide installation
if [[ $EUID -eq 0 ]]; then
    print_error "This script should not be run as root for user installation"
    echo "Please run as regular user. The script will ask for password when needed."
    exit 1
fi

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-full sqlite3 xdotool

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install --user --break-system-packages -r requirements.txt

# Create installation directory
INSTALL_DIR="/usr/local/lib/smart-clipboard"
sudo mkdir -p "$INSTALL_DIR"

# Copy application files
echo "📁 Copying application files..."
sudo cp -r src/ "$INSTALL_DIR/"
sudo cp main.py "$INSTALL_DIR/"
sudo cp requirements.txt "$INSTALL_DIR/"

# Set permissions
sudo chown -R root:root "$INSTALL_DIR"
sudo chmod 755 "$INSTALL_DIR"
sudo chmod 644 "$INSTALL_DIR"/*.py
sudo chmod 644 "$INSTALL_DIR"/src/*.py

# Install executables
echo "🔧 Installing executables..."
sudo cp smart-clipboard /usr/local/bin/
sudo cp smart-clipboard-gui /usr/local/bin/
sudo chmod +x /usr/local/bin/smart-clipboard
sudo chmod +x /usr/local/bin/smart-clipboard-gui

# Install systemd service
echo "⚙️  Installing systemd service..."
mkdir -p ~/.config/systemd/user/
cp smart-clipboard.service ~/.config/systemd/user/smart-clipboard.service

# Install desktop entry
echo "🖥️  Installing desktop entry..."
mkdir -p ~/.local/share/applications/
cp smart-clipboard.desktop ~/.local/share/applications/

# Reload systemd and enable service
systemctl --user daemon-reload
systemctl --user enable smart-clipboard.service

# Start the service
echo "🚀 Starting Smart Clipboard Manager service..."
systemctl --user start smart-clipboard.service

# Wait a moment for service to start
sleep 2

# Check if service is running
if systemctl --user is-active --quiet smart-clipboard.service; then
    print_success "Smart Clipboard Manager is now running in the background!"
else
    print_error "Failed to start the service. Please check the logs with: journalctl --user -u smart-clipboard.service"
    exit 1
fi

print_success "Installation completed!"
echo ""
echo "🎯 Usage:"
echo "   • Press Ctrl+Shift+V to open the clipboard manager"
echo "   • Run 'smart-clipboard-gui' to open the UI manually"
echo "   • Run 'systemctl --user status smart-clipboard.service' to check status"
echo "   • Run 'systemctl --user stop smart-clipboard.service' to stop the service"
echo ""
echo "📝 Configuration file: ~/.smart-clipboard/config.json"
echo "🗄️  Database: ~/.smart-clipboard/clipboard.db"
echo ""
print_warning "The service will start automatically when you log in."
