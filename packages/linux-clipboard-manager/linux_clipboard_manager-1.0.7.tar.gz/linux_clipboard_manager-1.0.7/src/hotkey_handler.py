"""
Global hotkey handler for clipboard manager
"""
from pynput import keyboard
from typing import Callable, Optional
import threading


class HotkeyHandler:
    """Handles global keyboard shortcuts using pynput's GlobalHotKeys"""

    def __init__(self, callback: Callable[[], None], hotkey: str = "<ctrl>+<shift>+v"):
        """Initialize hotkey handler

        Args:
            callback: Function to call when hotkey is pressed
            hotkey: Hotkey combination (e.g., "<ctrl>+<shift>+v")
        """
        self.callback = callback
        self.hotkey_str = hotkey
        self.listener: Optional[keyboard.GlobalHotKeys] = None
        self._lock = threading.Lock()
        self._activated = False

    def start(self):
        """Start listening for hotkey"""
        if self.listener is not None:
            print("Hotkey handler already running")
            return

        try:
            # Use pynput's GlobalHotKeys - the proper way to handle global hotkeys
            self.listener = keyboard.GlobalHotKeys({
                self.hotkey_str: self._on_activate
            })
            self.listener.start()
            print(f"✅ Hotkey handler started: {self.hotkey_str}")
        except Exception as e:
            print(f"❌ Error starting hotkey handler: {e}")
            print(f"   This may be due to permissions or conflicting applications")
            print(f"   Try running with sudo/admin privileges or change the hotkey")

    def stop(self):
        """Stop listening for hotkey"""
        if self.listener is not None:
            try:
                self.listener.stop()
                self.listener = None
                print("Hotkey handler stopped")
            except Exception as e:
                print(f"Error stopping hotkey handler: {e}")

    def _on_activate(self):
        """Handle hotkey activation"""
        with self._lock:
            # Prevent multiple rapid activations
            if self._activated:
                return
            self._activated = True

        try:
            self.callback()
        except Exception as e:
            print(f"Error in hotkey callback: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Reset activation flag after a short delay
            threading.Timer(0.2, self._reset_activation).start()

    def _reset_activation(self):
        """Reset activation flag"""
        with self._lock:
            self._activated = False


class HotkeyManager:
    """Manages multiple hotkeys"""
    
    def __init__(self):
        """Initialize hotkey manager"""
        self.handlers = []
    
    def register(self, hotkey: str, callback: Callable[[], None]) -> HotkeyHandler:
        """Register a new hotkey
        
        Args:
            hotkey: Hotkey combination
            callback: Function to call when hotkey is pressed
            
        Returns:
            HotkeyHandler instance
        """
        handler = HotkeyHandler(callback, hotkey)
        self.handlers.append(handler)
        return handler
    
    def start_all(self):
        """Start all registered hotkey handlers"""
        for handler in self.handlers:
            handler.start()
    
    def stop_all(self):
        """Stop all registered hotkey handlers"""
        for handler in self.handlers:
            handler.stop()

