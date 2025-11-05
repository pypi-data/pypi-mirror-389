#!/bin/bash
# Installation script for Linux Clipboard Manager

set -e

echo "🚀 Installing Linux Clipboard Manager..."

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_error "This script should not be run as root"
    echo "Please run as regular user. The script will ask for password when needed."
    exit 1
fi

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-full sqlite3 xdotool pipx

# Ensure pipx path is set
pipx ensurepath

# Install the application using pipx
echo "🐍 Installing Linux Clipboard Manager..."
pipx install linux-clipboard-manager

print_success "Installation completed!"
echo ""
echo "🎯 Usage:"
echo "   • Run 'smart-clipboard' to start the background service"
echo "   • Run 'smart-clipboard-gui' to open the UI"
echo "   • Press Ctrl+Alt+V to toggle the clipboard manager (when running)"
echo ""
echo "📝 Configuration file: ~/.smart-clipboard/config.json"
echo "🗄️  Database: ~/.smart-clipboard/clipboard.db"
echo ""
print_warning "To start automatically on login, set up a systemd service or autostart entry."
