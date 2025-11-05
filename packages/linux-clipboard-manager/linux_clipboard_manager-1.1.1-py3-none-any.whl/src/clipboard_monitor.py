"""
Background clipboard monitoring service
"""
import threading
import time
import pyperclip
from typing import Callable, Optional
from datetime import datetime


class ClipboardMonitor:
    """Monitors clipboard for changes and triggers callbacks"""
    
    def __init__(self, callback: Callable[[str], None], 
                 interval: float = 0.5,
                 ignore_empty: bool = True):
        """Initialize clipboard monitor
        
        Args:
            callback: Function to call when clipboard changes
            interval: Polling interval in seconds
            ignore_empty: Whether to ignore empty clipboard content
        """
        self.callback = callback
        self.interval = interval
        self.ignore_empty = ignore_empty
        self.last_content = ""
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def start(self):
        """Start monitoring clipboard"""
        if self.running:
            print("Clipboard monitor already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print("Clipboard monitor started")
    
    def stop(self):
        """Stop monitoring clipboard"""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        print("Clipboard monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        # Initialize with current clipboard content
        try:
            self.last_content = pyperclip.paste()
        except Exception as e:
            print(f"Error reading initial clipboard: {e}")
            self.last_content = ""
        
        while self.running:
            try:
                current_content = pyperclip.paste()
                
                # Check if content has changed
                if current_content != self.last_content:
                    # Ignore empty content if configured
                    if self.ignore_empty and not current_content.strip():
                        self.last_content = current_content
                        continue
                    
                    # Update last content
                    with self._lock:
                        self.last_content = current_content
                    
                    # Trigger callback
                    try:
                        self.callback(current_content)
                    except Exception as e:
                        print(f"Error in clipboard callback: {e}")
                
            except Exception as e:
                print(f"Error monitoring clipboard: {e}")
            
            # Sleep for interval
            time.sleep(self.interval)
    
    def get_current_content(self) -> str:
        """Get current clipboard content
        
        Returns:
            Current clipboard content
        """
        with self._lock:
            return self.last_content
    
    def set_clipboard(self, content: str):
        """Set clipboard content
        
        Args:
            content: Content to set
        """
        try:
            pyperclip.copy(content)
            with self._lock:
                self.last_content = content
        except Exception as e:
            print(f"Error setting clipboard: {e}")


class ClipboardManager:
    """High-level clipboard manager that integrates monitoring and storage"""
    
    def __init__(self, storage, analyzer, config):
        """Initialize clipboard manager
        
        Args:
            storage: ClipboardStorage instance
            analyzer: ContentAnalyzer instance
            config: Config instance
        """
        self.storage = storage
        self.analyzer = analyzer
        self.config = config
        
        # Get active window/app name (platform-specific)
        self.app_detector = AppDetector()
        
        # Refresh callbacks for UI updates
        self.refresh_callbacks = []
        
        # Create monitor with callback
        interval = config.get('monitor_interval', 0.5)
        self.monitor = ClipboardMonitor(
            callback=self._on_clipboard_change,
            interval=interval
        )
        
        self.excluded_apps = set(config.get('excluded_apps', []))
    
    def start(self):
        """Start clipboard monitoring"""
        self.monitor.start()
    
    def stop(self):
        """Stop clipboard monitoring"""
        self.monitor.stop()
    
    def add_refresh_callback(self, callback):
        """Add a callback to be called when clipboard is updated
        
        Args:
            callback: Function to call when new clipboard item is saved
        """
        self.refresh_callbacks.append(callback)
    
    def _trigger_refresh_callbacks(self):
        """Trigger all refresh callbacks"""
        for callback in self.refresh_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in refresh callback: {e}")
    
    def _on_clipboard_change(self, content: str):
        """Handle clipboard change event
        
        Args:
            content: New clipboard content
        """
        # Get current app name
        app_name = self.app_detector.get_active_app()
        
        # Check if app is excluded
        if app_name in self.excluded_apps:
            print(f"Ignoring clipboard from excluded app: {app_name}")
            return
        
        # Analyze content
        analysis = self.analyzer.analyze(content)
        
        # Skip sensitive content if configured
        if analysis['is_sensitive']:
            print("Skipping sensitive content")
            return
        
        # Check content size limit
        max_size = self.config.get('max_content_size', 1048576)
        if len(content) > max_size:
            print(f"Content too large ({len(content)} bytes), skipping")
            return
        
        # Save to storage
        clip_id = self.storage.save_clip(
            content=content,
            content_type=analysis['content_type'],
            app_name=app_name,
            metadata=analysis['metadata']
        )
        
        if clip_id:
            print(f"Saved clipboard entry {clip_id} ({analysis['content_type']})")
            # Trigger UI refresh callbacks
            self._trigger_refresh_callbacks()
        
        # Cleanup old entries
        max_history = self.config.get('max_history', 1000)
        self.storage.cleanup_old_entries(max_history)
    
    def paste_clip(self, clip_id: int):
        """Paste a clip from history
        
        Args:
            clip_id: Clipboard entry ID
        """
        clips = self.storage.get_history(limit=1000)
        clip = next((c for c in clips if c['id'] == clip_id), None)
        
        if clip:
            self.monitor.set_clipboard(clip['content'])
            print(f"Pasted clip {clip_id}")
        else:
            print(f"Clip {clip_id} not found")


class AppDetector:
    """Detects the currently active application (platform-specific)"""
    
    def __init__(self):
        """Initialize app detector"""
        import platform
        self.platform = platform.system()
        
        if self.platform == "Windows":
            self._init_windows()
        elif self.platform == "Darwin":
            self._init_macos()
        elif self.platform == "Linux":
            self._init_linux()
    
    def _init_windows(self):
        """Initialize Windows-specific detection"""
        try:
            import win32gui
            import win32process
            import psutil
            self.win32gui = win32gui
            self.win32process = win32process
            self.psutil = psutil
        except ImportError:
            print("Warning: win32gui/psutil not available. App detection disabled.")
            self.win32gui = None
    
    def _init_macos(self):
        """Initialize macOS-specific detection"""
        # Will use AppleScript
        pass
    
    def _init_linux(self):
        """Initialize Linux-specific detection"""
        # Will use xdotool or similar
        pass
    
    def get_active_app(self) -> Optional[str]:
        """Get name of currently active application
        
        Returns:
            App name or None if detection fails
        """
        try:
            if self.platform == "Windows":
                return self._get_active_app_windows()
            elif self.platform == "Darwin":
                return self._get_active_app_macos()
            elif self.platform == "Linux":
                return self._get_active_app_linux()
        except Exception as e:
            print(f"Error detecting active app: {e}")
        
        return None
    
    def _get_active_app_windows(self) -> Optional[str]:
        """Get active app on Windows"""
        if not self.win32gui:
            return None
        
        try:
            window = self.win32gui.GetForegroundWindow()
            _, pid = self.win32process.GetWindowThreadProcessId(window)
            process = self.psutil.Process(pid)
            return process.name()
        except:
            return None
    
    def _get_active_app_macos(self) -> Optional[str]:
        """Get active app on macOS"""
        try:
            import subprocess
            script = 'tell application "System Events" to get name of first application process whose frontmost is true'
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=1
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None
    
    def _get_active_app_linux(self) -> Optional[str]:
        """Get active app on Linux"""
        try:
            import subprocess
            result = subprocess.run(
                ['xdotool', 'getactivewindow', 'getwindowname'],
                capture_output=True,
                text=True,
                timeout=1
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None

