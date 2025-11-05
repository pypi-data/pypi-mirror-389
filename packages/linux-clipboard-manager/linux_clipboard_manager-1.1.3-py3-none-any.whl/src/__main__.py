#!/usr/bin/env python3
"""
Smart Clipboard Manager - Main Entry Point
"""
import sys
import signal
import argparse
from pathlib import Path

from .config import Config
from .storage import ClipboardStorage
from .content_analyzer import ContentAnalyzer
from .clipboard_monitor import ClipboardManager
from .ui import ClipboardUI
from .hotkey_handler import HotkeyHandler


class SmartClipboardApp:
    """Main application class"""
    
    def __init__(self):
        """Initialize the application"""
        print("Starting Smart Clipboard Manager...")
        
        # Initialize components
        self.config = Config()
        print(f"Config loaded from: {self.config.config_path}")
        
        db_path = self.config.get_database_path()
        self.storage = ClipboardStorage(str(db_path))
        print(f"Database: {db_path}")
        
        self.analyzer = ContentAnalyzer()
        
        self.clipboard_manager = ClipboardManager(
            self.storage,
            self.analyzer,
            self.config
        )
        
        self.ui = ClipboardUI(
            self.storage,
            self.analyzer,
            self.clipboard_manager,
            self.config
        )
        
        # Create UI window
        self.root = self.ui.create_window()
        
        # Setup hotkey
        hotkey = self.config.get('hotkey', '<ctrl>+<shift>+v')
        self.hotkey_handler = HotkeyHandler(
            callback=self.toggle_ui,
            hotkey=hotkey
        )
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print(f"Hotkey: {hotkey}")
        print("Smart Clipboard Manager is ready!")
        print(f"Press {hotkey.replace('<', '').replace('>', '').replace('+', '+')} to open the clipboard manager")
        print("Press Ctrl+C to exit")
    
    def toggle_ui(self):
        """Toggle UI visibility"""
        print(f"Hotkey pressed! Window visible: {self.root.winfo_viewable()}")
        try:
            if self.root.winfo_viewable():
                self.ui.hide()
                print("Hiding UI")
            else:
                self.ui.show()
                print("Showing UI")
        except Exception as e:
            print(f"Error toggling UI: {e}")
            import traceback
            traceback.print_exc()
    
    def start(self):
        """Start the application"""
        # Start clipboard monitoring
        self.clipboard_manager.start()
        
        # Start hotkey handler
        self.hotkey_handler.start()
        
        # Start UI event loop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.stop()
    
    def stop(self):
        """Stop the application"""
        print("Stopping Smart Clipboard Manager...")
        
        # Stop hotkey handler
        self.hotkey_handler.stop()
        
        # Stop clipboard monitoring
        self.clipboard_manager.stop()
        
        # Close storage
        self.storage.close()
        
        print("Goodbye!")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals"""
        print(f"\nReceived signal {signum}")
        self.stop()
        sys.exit(0)


def show_ui_only():
    """Show the UI without starting background monitoring"""
    try:
        config = Config()
        db_path = config.get_database_path()
        storage = ClipboardStorage(str(db_path))
        analyzer = ContentAnalyzer()
        
        # Create a minimal clipboard manager for UI operations
        class MinimalManager:
            def __init__(self):
                pass
            def add_refresh_callback(self, callback):
                pass
        
        clipboard_manager = MinimalManager()
        
        ui = ClipboardUI(storage, analyzer, clipboard_manager, config)
        root = ui.create_window()
        ui.show()
        root.mainloop()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Smart Clipboard Manager')
    parser.add_argument('--show-ui', action='store_true', 
                       help='Show the clipboard manager UI only')
    
    args = parser.parse_args()
    
    if args.show_ui:
        show_ui_only()
        return
    
    try:
        app = SmartClipboardApp()
        app.start()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

