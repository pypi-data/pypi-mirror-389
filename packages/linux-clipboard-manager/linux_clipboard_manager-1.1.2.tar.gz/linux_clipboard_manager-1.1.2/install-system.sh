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

# Set up systemd service for autostart
echo "⚙️  Setting up autostart service..."
mkdir -p ~/.config/systemd/user/

# Create service file
cat > ~/.config/systemd/user/linux-clipboard-manager.service << 'EOF'
[Unit]
Description=Linux Clipboard Manager
After=graphical-session.target

[Service]
Type=simple
ExecStart=%h/.local/bin/smart-clipboard
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

# Reload systemd and enable service
systemctl --user daemon-reload
systemctl --user enable linux-clipboard-manager.service
systemctl --user start linux-clipboard-manager.service

# Wait for service to start
sleep 2

# Check if service is running
if systemctl --user is-active --quiet linux-clipboard-manager.service; then
    print_success "Service is running!"
else
    print_warning "Service may not have started. Check with: systemctl --user status linux-clipboard-manager.service"
fi

print_success "Installation completed!"
echo ""
echo "🎯 Usage:"
echo "   • The clipboard manager is now running in the background"
echo "   • Press Ctrl+Alt+V to toggle the clipboard manager window"
echo "   • Run 'smart-clipboard-gui' to open just the UI"
echo ""
echo "🔧 Service Management:"
echo "   • Status: systemctl --user status linux-clipboard-manager.service"
echo "   • Stop: systemctl --user stop linux-clipboard-manager.service"
echo "   • Restart: systemctl --user restart linux-clipboard-manager.service"
echo "   • Disable autostart: systemctl --user disable linux-clipboard-manager.service"
echo ""
echo "📝 Configuration file: ~/.smart-clipboard/config.json"
echo "🗄️  Database: ~/.smart-clipboard/clipboard.db"
