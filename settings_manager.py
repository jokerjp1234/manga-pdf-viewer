import os
import json
from PyQt5.QtCore import QSettings

class SettingsManager:
    """
    Manages application settings and persistent data.
    Handles bookmarks, favorites, and application preferences.
    """
    
    def __init__(self, app_name="MangaPDFViewer", org_name="MangaApp"):
        """
        Initialize settings manager with default values.
        
        Args:
            app_name: Application name for settings
            org_name: Organization name for settings
        """
        self.settings = QSettings(org_name, app_name)
        self.user_home = os.path.expanduser("~")
        self.cache_dir = os.path.join(self.user_home, ".manga_viewer_cache")
        
        # Ensure cache directory exists
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
        # File paths for persistent data
        self.bookmarks_file = os.path.join(self.user_home, ".manga_viewer_bookmarks.json")
        self.favorites_file = os.path.join(self.user_home, ".manga_viewer_favorites.json")
        
        # Load persistent data
        self.bookmarks = self.load_bookmarks()
        self.favorites = self.load_favorites()
        
        # Set default application settings if not already set
        if not self.settings.contains("use_arrow_keys"):
            self.settings.setValue("use_arrow_keys", True)
            
        if not self.settings.contains("left_click_next"):
            self.settings.setValue("left_click_next", True)
            
        if not self.settings.contains("manga_folders"):
            self.settings.setValue("manga_folders", [])
    
    def get_cache_dir(self):
        """Get the thumbnail cache directory path."""
        return self.cache_dir
    
    def get_manga_folders(self):
        """Get the list of registered manga folders."""
        folders = self.settings.value("manga_folders", [])
        if folders is None:
            folders = []
        return folders
    
    def add_manga_folder(self, folder_path):
        """
        Add a manga folder to the settings.
        
        Args:
            folder_path: Path to add
            
        Returns:
            Boolean indicating success
        """
        folders = self.get_manga_folders()
        if folder_path in folders:
            return False
            
        folders.append(folder_path)
        self.settings.setValue("manga_folders", folders)
        return True
    
    def remove_manga_folder(self, folder_path):
        """
        Remove a manga folder from the settings.
        
        Args:
            folder_path: Path to remove
            
        Returns:
            Boolean indicating success
        """
        folders = self.get_manga_folders()
        if folder_path not in folders:
            return False
            
        folders.remove(folder_path)
        self.settings.setValue("manga_folders", folders)
        return True
    
    def load_bookmarks(self):
        """
        Load bookmarks from the bookmarks file.
        
        Returns:
            Dictionary of bookmarks
        """
        try:
            if os.path.exists(self.bookmarks_file):
                with open(self.bookmarks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading bookmarks: {str(e)}")
        return {}
    
    def save_bookmarks(self):
        """Save bookmarks to the bookmarks file."""
        try:
            with open(self.bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving bookmarks: {str(e)}")
    
    def add_bookmark(self, manga, volume, page):
        """
        Add a bookmark for a manga volume.
        
        Args:
            manga: Manga name
            volume: Volume name
            page: Page number
        """
        bookmark_key = f"{manga}/{volume}"
        self.bookmarks[bookmark_key] = page
        self.save_bookmarks()
    
    def remove_bookmark(self, bookmark_key):
        """
        Remove a bookmark.
        
        Args:
            bookmark_key: Bookmark key to remove
            
        Returns:
            Boolean indicating success
        """
        if bookmark_key in self.bookmarks:
            del self.bookmarks[bookmark_key]
            self.save_bookmarks()
            return True
        return False
    
    def load_favorites(self):
        """
        Load favorites from the favorites file.
        
        Returns:
            List of favorite manga names
        """
        try:
            if os.path.exists(self.favorites_file):
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading favorites: {str(e)}")
        return []
    
    def save_favorites(self):
        """Save favorites to the favorites file."""
        try:
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving favorites: {str(e)}")
    
    def add_favorite(self, manga_name):
        """
        Add a manga to favorites.
        
        Args:
            manga_name: Name of manga to add
            
        Returns:
            Boolean indicating success
        """
        if manga_name in self.favorites:
            return False
            
        self.favorites.append(manga_name)
        self.save_favorites()
        return True
    
    def remove_favorite(self, manga_name):
        """
        Remove a manga from favorites.
        
        Args:
            manga_name: Name of manga to remove
            
        Returns:
            Boolean indicating success
        """
        if manga_name not in self.favorites:
            return False
            
        self.favorites.remove(manga_name)
        self.save_favorites()
        return True
    
    def get_setting(self, key, default=None):
        """
        Get a setting value.
        
        Args:
            key: Setting key
            default: Default value if setting does not exist
            
        Returns:
            Setting value
        """
        return self.settings.value(key, default)
    
    def set_setting(self, key, value):
        """
        Set a setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        self.settings.setValue(key, value)
