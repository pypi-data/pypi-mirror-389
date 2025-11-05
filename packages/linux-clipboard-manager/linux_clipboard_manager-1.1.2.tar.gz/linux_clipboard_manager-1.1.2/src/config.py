"""
Configuration management for Smart Clipboard Manager
"""
import os
import json
from pathlib import Path
from typing import Dict, Any


class Config:
    """Manages application configuration and settings"""
    
    DEFAULT_CONFIG = {
        "max_history": 1000,
        "monitor_interval": 0.5,  # seconds
        "hotkey": "<ctrl>+<alt>+v",
        "database_path": "clipboard.db",
        "max_content_size": 1048576,  # 1MB
        "enable_encryption": False,
        "excluded_apps": ["KeePass", "1Password", "LastPass"],
        "categories": {
            "url": True,
            "email": True,
            "code": True,
            "image": True
        },
        "ui": {
            "max_preview_length": 100,
            "window_width": 600,
            "window_height": 400,
            "theme": "light"
        }
    }
    
    def __init__(self, config_path: str = None):
        """Initialize configuration
        
        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            config_dir = Path.home() / ".smart-clipboard"
            config_dir.mkdir(exist_ok=True)
            config_path = config_dir / "config.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                # Merge with defaults
                config = self.DEFAULT_CONFIG.copy()
                config.update(user_config)
                return config
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, config: Dict[str, Any] = None):
        """Save configuration to file
        
        Args:
            config: Configuration dict to save. If None, saves current config.
        """
        if config is None:
            config = self.config
        
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'ui.theme')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()
    
    def get_database_path(self) -> Path:
        """Get full path to database file"""
        db_path = self.get("database_path")
        if not os.path.isabs(db_path):
            config_dir = Path.home() / ".smart-clipboard"
            return config_dir / db_path
        return Path(db_path)

