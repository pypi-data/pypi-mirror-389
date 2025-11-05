"""
User interface for Smart Clipboard Manager
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, List, Dict
import pyperclip


class ClipboardUI:
    """Main UI for clipboard manager"""
    
    def __init__(self, storage, analyzer, clipboard_manager, config):
        """Initialize UI
        
        Args:
            storage: ClipboardStorage instance
            analyzer: ContentAnalyzer instance
            clipboard_manager: ClipboardManager instance
            config: Config instance
        """
        self.storage = storage
        self.analyzer = analyzer
        self.clipboard_manager = clipboard_manager
        self.config = config
        
        self.root = None
        self.search_var = None
        self.clips_listbox = None
        self.preview_text = None
        self.current_clips = []
        self.auto_refresh_enabled = True
        
    def create_window(self):
        """Create the main UI window"""
        self.root = tk.Tk()
        self.root.title("Smart Clipboard Manager")
        
        # Get window size from config
        width = self.config.get('ui.window_width', 600)
        height = self.config.get('ui.window_height', 400)
        
        # Center window on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.withdraw()  # Start hidden
        
        # Create UI elements
        self._create_widgets()
        
        # Register for clipboard updates
        if hasattr(self.clipboard_manager, 'add_refresh_callback'):
            self.clipboard_manager.add_refresh_callback(self._auto_refresh)
        
        # Bind keyboard shortcuts
        self.root.bind('<Escape>', lambda e: self.hide())
        self.root.bind('<Return>', lambda e: self._paste_selected())
        self.root.bind('<Double-Button-1>', lambda e: self._paste_selected())
        self.root.bind('<Button-1>', lambda e: self._on_click_copy(e))
        
        return self.root
    
    def _create_widgets(self):
        """Create UI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Search bar
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._on_search())
        
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        search_entry.focus()
        
        # Filter buttons
        filter_frame = ttk.Frame(search_frame)
        filter_frame.grid(row=0, column=2, padx=(10, 0))
        
        ttk.Button(filter_frame, text="All", command=lambda: self._filter_by_type(None), width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="URLs", command=lambda: self._filter_by_type('url'), width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Code", command=lambda: self._filter_by_type('code'), width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="⭐", command=self._show_favorites, width=4).pack(side=tk.LEFT, padx=2)
        
        # Clips list with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.clips_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=('Courier', 10),
            height=15
        )
        self.clips_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.clips_listbox.yview)
        
        self.clips_listbox.bind('<<ListboxSelect>>', self._on_select)
        
        # Preview pane
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding="5")
        preview_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        preview_scroll = ttk.Scrollbar(preview_frame)
        preview_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.preview_text = tk.Text(
            preview_frame,
            height=6,
            wrap=tk.WORD,
            yscrollcommand=preview_scroll.set,
            font=('Courier', 9)
        )
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_scroll.config(command=self.preview_text.yview)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(button_frame, text="Copy", command=self._copy_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Paste", command=self._paste_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Favorite", command=self._toggle_favorite).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete", command=self._delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self._clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Stats", command=self._show_stats).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.hide).pack(side=tk.RIGHT)
    
    def show(self):
        """Show the UI window"""
        if self.root is None:
            self.create_window()
        
        print("UI show() called")
        self.root.deiconify()
        self.root.lift()
        self.root.attributes('-topmost', True)  # Force window to top
        self.root.after(100, lambda: self.root.attributes('-topmost', False))  # Remove topmost after showing
        self.root.focus_force()
        
        # Refresh clips list
        self._refresh_clips()
        
        # Focus search box and clear filter
        if self.search_var:
            self.search_var.set('')
        # Enable auto-refresh and show all clips when window opens
        self.auto_refresh_enabled = True
        self._refresh_clips()
        print(f"UI shown, viewable: {self.root.winfo_viewable()}")
    
    def hide(self):
        """Hide the UI window"""
        if self.root:
            self.root.withdraw()
    
    def _refresh_clips(self, clips: List[Dict] = None):
        """Refresh the clips list
        
        Args:
            clips: List of clips to display. If None, loads from storage.
        """
        if clips is None:
            clips = self.storage.get_history(limit=100)
        
        self.current_clips = clips
        
        # Clear listbox
        self.clips_listbox.delete(0, tk.END)
        
        # Add clips
        max_preview = self.config.get('ui.max_preview_length', 100)
        
        for clip in clips:
            preview = self.analyzer.get_preview(clip['content'], max_preview)
            preview = preview.replace('\n', ' ').replace('\r', '')
            
            # Add type indicator
            type_icon = self._get_type_icon(clip['content_type'])
            favorite_icon = '⭐' if clip.get('is_favorite') else '  '
            
            display = f"{favorite_icon} {type_icon} {preview}"
            self.clips_listbox.insert(tk.END, display)
    
    def _get_type_icon(self, content_type: str) -> str:
        """Get icon for content type"""
        icons = {
            'url': '🔗',
            'email': '📧',
            'code': '💻',
            'file_path': '📁',
            'number': '🔢',
            'json': '{}',
            'markdown': '📝',
            'text': '📄'
        }
        return icons.get(content_type, '📄')
    
    def _auto_refresh(self):
        """Auto-refresh when new clipboard item is added"""
        if not self.auto_refresh_enabled:
            return
            
        # Only refresh if window is visible and search is empty
        if (self.root and self.root.winfo_viewable() and 
            self.search_var and not self.search_var.get().strip()):
            self._refresh_clips()
    
    def _on_search(self):
        """Handle search input"""
        query = self.search_var.get()
        
        if not query:
            # Enable auto-refresh when search is cleared
            self.auto_refresh_enabled = True
            self._refresh_clips()
            return
        
        # Disable auto-refresh during search
        self.auto_refresh_enabled = False
        
        # Search in storage
        results = self.storage.search(query)
        self._refresh_clips(results)
    
    def _filter_by_type(self, content_type: Optional[str]):
        """Filter clips by type
        
        Args:
            content_type: Type to filter by, or None for all
        """
        # Disable auto-refresh when filtering
        self.auto_refresh_enabled = (content_type is None)
        clips = self.storage.get_history(limit=100, content_type=content_type)
        self._refresh_clips(clips)
    
    def _show_favorites(self):
        """Show favorite clips"""
        # Disable auto-refresh when showing favorites
        self.auto_refresh_enabled = False
        clips = self.storage.get_favorites()
        self._refresh_clips(clips)
    
    def _on_select(self, event):
        """Handle clip selection"""
        selection = self.clips_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index >= len(self.current_clips):
            return
        
        clip = self.current_clips[index]
        
        # Show preview
        self.preview_text.delete('1.0', tk.END)
        self.preview_text.insert('1.0', clip['content'])
    
    def _on_click_copy(self, event):
        """Handle click on listbox item - copy to clipboard"""
        # Check if click is on the listbox
        if event.widget != self.clips_listbox:
            return
        
        selection = self.clips_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index >= len(self.current_clips):
            return
        
        clip = self.current_clips[index]
        
        # Copy to clipboard
        pyperclip.copy(clip['content'])
        print(f"Copied clip {clip['id']} to clipboard")
    
    def _copy_selected(self):
        """Copy selected clip to clipboard"""
        selection = self.clips_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index >= len(self.current_clips):
            return
        
        clip = self.current_clips[index]
        
        # Copy to clipboard
        pyperclip.copy(clip['content'])
        print(f"Copied clip {clip['id']} to clipboard")
    
    def _paste_selected(self):
        """Paste selected clip"""
        selection = self.clips_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index >= len(self.current_clips):
            return
        
        clip = self.current_clips[index]
        
        # Copy to clipboard
        pyperclip.copy(clip['content'])
        
        # Hide window
        self.hide()
        
        print(f"Pasted clip {clip['id']}")
    
    def _toggle_favorite(self):
        """Toggle favorite status of selected clip"""
        selection = self.clips_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index >= len(self.current_clips):
            return
        
        clip = self.current_clips[index]
        self.storage.toggle_favorite(clip['id'])
        
        # Refresh
        self._refresh_clips()
    
    def _delete_selected(self):
        """Delete selected clip"""
        selection = self.clips_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index >= len(self.current_clips):
            return
        
        clip = self.current_clips[index]
        
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", "Delete this clip?"):
            self.storage.delete_clip(clip['id'])
            self._refresh_clips()
    
    def _clear_all(self):
        """Clear all clipboard items"""
        # Confirm deletion
        if messagebox.askyesno("Confirm Clear All", "Delete all clipboard items? This action cannot be undone."):
            try:
                # Get count before clearing for feedback
                stats = self.storage.get_stats()
                count = stats['total']
                
                # Clear all items
                self.storage.clear_all()
                
                # Refresh the display
                self._refresh_clips()
                print(f"Cleared {count} clipboard items")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear clipboard items: {e}")
    
    def _show_stats(self):
        """Show storage statistics"""
        stats = self.storage.get_stats()
        
        message = f"Total clips: {stats['total']}\n"
        message += f"Favorites: {stats['favorites']}\n\n"
        message += "By type:\n"
        
        for content_type, count in stats['by_type'].items():
            message += f"  {content_type}: {count}\n"
        
        messagebox.showinfo("Statistics", message)

