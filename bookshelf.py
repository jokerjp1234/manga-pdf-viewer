import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                           QTreeWidget, QTreeWidgetItem, QGridLayout, QScrollArea,
                           QMessageBox, QListWidget, QListWidgetItem, QMenu, QFileDialog)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPixmap

from thumbnail_loader import ThumbnailLoader
from utils import natural_sort_key, get_pdf_files, get_manga_directories

class Bookshelf(QWidget):
    """
    Manages manga books and volumes with bookshelf, favorites, and bookmarks functionality.
    """
    # Signals
    manga_selected = pyqtSignal(str, str)  # manga name, manga path
    volume_selected = pyqtSignal(str, str, str)  # manga name, manga path, volume name
    
    def __init__(self, settings_manager, parent=None):
        """
        Initialize the bookshelf component.
        
        Args:
            settings_manager: The application settings manager
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.settings_manager = settings_manager
        self.manga_folders = settings_manager.get_manga_folders()
        self.favorites = settings_manager.favorites
        self.bookmarks = settings_manager.bookmarks
        self.cache_dir = settings_manager.get_cache_dir()
        
        # Current state
        self.current_manga = None
        self.current_manga_path = None
        
        # Thread management
        self.thumbnail_threads = []
        
        # Set up the UI
        self.setup_ui()
        
        # Load initial data
        self.load_manga_tree()
        self.update_favorites_list()
        self.update_bookmarks_list()
    
    def setup_ui(self):
        """Set up the user interface for the bookshelf component."""
        layout = QVBoxLayout(self)
        
        # Create tabs
        from PyQt5.QtWidgets import QTabWidget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Bookshelf tab
        self.manga_tab = QWidget()
        self.manga_tab_layout = QVBoxLayout(self.manga_tab)
        
        # Add manga folder button
        self.add_folder_button = QPushButton("漫画フォルダを本棚に追加")
        self.add_folder_button.clicked.connect(self.add_manga_folder)
        self.manga_tab_layout.addWidget(self.add_folder_button)
        
        # Manga tree
        self.manga_tree = QTreeWidget()
        self.manga_tree.setHeaderLabels(["本棚"])
        self.manga_tree.setIconSize(QSize(80, 120))
        self.manga_tree.itemClicked.connect(self.tree_item_clicked)
        self.manga_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.manga_tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        self.manga_tab_layout.addWidget(self.manga_tree)
        
        # Volume grid (for showing manga volumes)
        self.volume_container = QWidget()
        self.volume_layout = QGridLayout(self.volume_container)
        self.volume_scroll = QScrollArea()
        self.volume_scroll.setWidgetResizable(True)
        self.volume_scroll.setWidget(self.volume_container)
        self.manga_tab_layout.addWidget(self.volume_scroll)
        
        # Favorite button
        self.favorite_button = QPushButton("お気に入りに追加")
        self.favorite_button.clicked.connect(self.toggle_favorite)
        self.manga_tab_layout.addWidget(self.favorite_button)
        
        # Favorites tab
        self.favorites_tab = QWidget()
        self.favorites_tab_layout = QVBoxLayout(self.favorites_tab)
        
        # Favorites list label
        favorites_label = QLabel("お気に入りの漫画")
        favorites_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.favorites_tab_layout.addWidget(favorites_label)
        
        # Favorites list
        self.favorites_list = QListWidget()
        self.favorites_list.setIconSize(QSize(80, 120))
        self.favorites_list.itemClicked.connect(self.load_volumes_from_favorites)
        self.favorites_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.favorites_list.customContextMenuRequested.connect(self.show_favorites_context_menu)
        self.favorites_tab_layout.addWidget(self.favorites_list)
        
        # Favorites help text
        favorites_help = QLabel("※右クリックでお気に入りから削除できます")
        self.favorites_tab_layout.addWidget(favorites_help)
        
        # Bookmarks tab
        self.bookmarks_tab = QWidget()
        self.bookmarks_tab_layout = QVBoxLayout(self.bookmarks_tab)
        
        # Bookmarks list label
        bookmarks_label = QLabel("しおりの一覧")
        bookmarks_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.bookmarks_tab_layout.addWidget(bookmarks_label)
        
        # Bookmarks list
        self.bookmarks_list = QListWidget()
        self.bookmarks_list.setIconSize(QSize(80, 120))
        self.bookmarks_list.itemClicked.connect(self.open_bookmark_from_list)
        self.bookmarks_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bookmarks_list.customContextMenuRequested.connect(self.show_bookmarks_context_menu)
        self.bookmarks_tab_layout.addWidget(self.bookmarks_list)
        
        # Bookmarks help text
        bookmarks_help = QLabel("※右クリックでしおりを削除できます")
        self.bookmarks_tab_layout.addWidget(bookmarks_help)
        
        # Add tabs
        self.tabs.addTab(self.manga_tab, "本棚")
        self.tabs.addTab(self.favorites_tab, "お気に入り")
        self.tabs.addTab(self.bookmarks_tab, "しおり")
    
    def add_manga_folder(self):
        """Add a manga folder to the bookshelf."""
        directory = QFileDialog.getExistingDirectory(self, "漫画フォルダを選択")
        if directory:
            # Check if already added
            if directory in self.manga_folders:
                QMessageBox.information(self, "情報", "このフォルダは既に追加されています。")
                return
                
            # Add to settings
            self.settings_manager.add_manga_folder(directory)
            self.manga_folders = self.settings_manager.get_manga_folders()
            
            # Refresh UI
            self.load_manga_tree()
            QMessageBox.information(self, "追加完了", f"フォルダ「{directory}」を本棚に追加しました。")
    
    def load_manga_tree(self):
        """Load the manga tree with registered folders."""
        self.manga_tree.clear()
        
        if not self.manga_folders:
            # No folders registered
            root_item = QTreeWidgetItem(self.manga_tree)
            root_item.setText(0, "漫画フォルダが登録されていません。「漫画フォルダを本棚に追加」ボタンを押して追加してください。")
            root_item.setFlags(Qt.NoItemFlags)  # Make unselectable
            return
        
        # Sort folders by name
        sorted_folders = sorted(self.manga_folders, key=lambda x: os.path.basename(x).lower())
        
        for folder_path in sorted_folders:
            try:
                if not os.path.exists(folder_path):
                    continue  # Skip if folder doesn't exist
                    
                root_item = QTreeWidgetItem(self.manga_tree)
                root_item.setText(0, os.path.basename(folder_path))
                root_item.setData(0, Qt.UserRole, folder_path)  # Store folder path
                
                # Get manga directories within this folder (subfolders with PDFs)
                manga_dirs = get_manga_directories(folder_path)
                
                for manga_dir in manga_dirs:
                    manga_path = os.path.join(folder_path, manga_dir)
                    manga_item = QTreeWidgetItem(root_item)
                    manga_item.setText(0, manga_dir)
                    manga_item.setData(0, Qt.UserRole, manga_path)  # Store manga path
                    
                    # Add favorite icon if in favorites
                    if manga_dir in self.favorites:
                        manga_item.setIcon(0, QIcon.fromTheme("emblem-favorite"))
                
                # Expand root item
                root_item.setExpanded(True)
                
            except Exception as e:
                print(f"Error loading folder: {str(e)}")
    
    def tree_item_clicked(self, item, column):
        """
        Handle tree item click events.
        
        Args:
            item: The clicked tree item
            column: The clicked column
        """
        path = item.data(0, Qt.UserRole)
        if not path:
            return
            
        if os.path.isdir(path):
            # Directory item clicked
            try:
                pdf_files = get_pdf_files(path)
                if pdf_files:
                    # If item has parent, it's a manga folder
                    if item.parent():
                        self.current_manga = item.text(0)
                        self.current_manga_path = path
                        self.display_volumes(path, pdf_files)
                        
                        # Update favorite button state
                        if self.current_manga in self.favorites:
                            self.favorite_button.setText("お気に入りから削除")
                        else:
                            self.favorite_button.setText("お気に入りに追加")
                        
                        # Emit signal that manga was selected
                        self.manga_selected.emit(self.current_manga, self.current_manga_path)
            except Exception as e:
                print(f"Error loading folder contents: {str(e)}")
    
    def display_volumes(self, manga_path, files):
        """
        Display the volumes (PDF files) for a manga.
        
        Args:
            manga_path: Path to the manga directory
            files: List of PDF files
        """
        # Clean up any running thumbnail threads
        self.clean_thumbnail_threads()
        
        # Clear existing layout
        for i in reversed(range(self.volume_layout.count())):
            widget = self.volume_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Sort files in natural order (case-insensitive)
        files.sort(key=lambda x: natural_sort_key(x.lower()))
        
        # Add volumes to grid
        row, col = 0, 0
        max_cols = 3  # Number of columns in grid
        
        for pdf_file in files:
            # Container for each volume
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setAlignment(Qt.AlignCenter)
            
            # Thumbnail label
            thumb_label = QLabel()
            thumb_label.setFixedSize(120, 160)
            thumb_label.setAlignment(Qt.AlignCenter)
            thumb_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
            container_layout.addWidget(thumb_label)
            
            # Filename label
            name_label = QLabel(pdf_file)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setWordWrap(True)
            container_layout.addWidget(name_label)
            
            # Open button
            button = QPushButton("開く")
            button.clicked.connect(lambda checked, f=pdf_file: self.open_volume(f))
            container_layout.addWidget(button)
            
            # Add to grid
            self.volume_layout.addWidget(container, row, col)
            
            # Load thumbnail in separate thread
            pdf_path = os.path.join(manga_path, pdf_file)
            
            # Create and start thumbnail loader thread
            loader = ThumbnailLoader(pdf_path, self.cache_dir, self)
            local_thumb_label = thumb_label  # Bind to local variable for lambda
            loader.thumbnail_loaded.connect(
                lambda path, pixmap, label=local_thumb_label: self.set_thumbnail(label, pixmap)
            )
            loader.start()
            self.thumbnail_threads.append(loader)
            
            # Move to next position
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def open_volume(self, pdf_file):
        """
        Open a volume (PDF file).
        
        Args:
            pdf_file: Name of the PDF file to open
        """
        if not self.current_manga_path:
            QMessageBox.warning(self, "エラー", "漫画が選択されていません")
            return
            
        # Emit signal to open volume
        self.volume_selected.emit(self.current_manga, self.current_manga_path, pdf_file)
    
    def clean_thumbnail_threads(self):
        """Clean up completed thumbnail loader threads."""
        active_threads = []
        for thread in self.thumbnail_threads:
            if thread.isRunning():
                active_threads.append(thread)
            else:
                thread.wait()
        
        self.thumbnail_threads = active_threads
    
    def set_thumbnail(self, label, pixmap):
        """
        Set a thumbnail image on a label.
        
        Args:
            label: Label to set thumbnail on
            pixmap: Pixmap to set
        """
        # Check if label still exists
        if not label or not label.isVisible():
            return
            
        if not pixmap.isNull():
            # Resize to fit label
            scaled_pixmap = pixmap.scaled(
                label.width(), 
                label.height(),
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            label.setPixmap(scaled_pixmap)
        else:
            # Display default text
            label.setText("No Preview")
    
    def show_tree_context_menu(self, position):
        """
        Show context menu for tree items.
        
        Args:
            position: Position to show menu at
        """
        item = self.manga_tree.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        
        # Root folder
        if not item.parent():
            remove_action = menu.addAction("本棚から削除")
            action = menu.exec_(self.manga_tree.mapToGlobal(position))
            
            if action == remove_action:
                folder_path = item.data(0, Qt.UserRole)
                if folder_path in self.manga_folders:
                    reply = QMessageBox.question(
                        self, 
                        "本棚から削除", 
                        f"フォルダ「{folder_path}」を本棚から削除しますか？\nしおりやお気に入りの情報は保持されます。",
                        QMessageBox.Yes | QMessageBox.No, 
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        self.settings_manager.remove_manga_folder(folder_path)
                        self.manga_folders = self.settings_manager.get_manga_folders()
                        self.load_manga_tree()
                        QMessageBox.information(self, "削除完了", f"フォルダ「{folder_path}」を本棚から削除しました。")
        # Manga folder
        else:
            manga_name = item.text(0)
            
            if manga_name in self.favorites:
                favorite_action = menu.addAction("お気に入りから削除")
            else:
                favorite_action = menu.addAction("お気に入りに追加")
                
            action = menu.exec_(self.manga_tree.mapToGlobal(position))
            
            if action == favorite_action:
                if manga_name in self.favorites:
                    self.settings_manager.remove_favorite(manga_name)
                    QMessageBox.information(self, "お気に入り", f"{manga_name}をお気に入りから削除しました。")
                else:
                    self.settings_manager.add_favorite(manga_name)
                    QMessageBox.information(self, "お気に入り", f"{manga_name}をお気に入りに追加しました。")
                
                self.favorites = self.settings_manager.favorites
                self.update_favorites_list()
                self.load_manga_tree()  # Reload tree to update star icons
    
    def toggle_favorite(self):
        """Toggle favorite status for current manga."""
        if not self.current_manga:
            QMessageBox.information(self, "情報", "マンガを選択してください。")
            return
        
        if self.current_manga in self.favorites:
            self.settings_manager.remove_favorite(self.current_manga)
            self.favorite_button.setText("お気に入りに追加")
            QMessageBox.information(self, "お気に入り", f"{self.current_manga}をお気に入りから削除しました。")
        else:
            self.settings_manager.add_favorite(self.current_manga)
            self.favorite_button.setText("お気に入りから削除")
            QMessageBox.information(self, "お気に入り", f"{self.current_manga}をお気に入りに追加しました。")
        
        self.favorites = self.settings_manager.favorites
        self.update_favorites_list()
        self.load_manga_tree()  # Reload tree to update star icons
    
    def update_favorites_list(self):
        """Update the favorites list."""
        self.favorites_list.clear()
        
        if not self.favorites:
            # No favorites
            empty_item = QListWidgetItem("お気に入りに追加された漫画はありません")
            empty_item.setFlags(Qt.NoItemFlags)  # Make unselectable
            self.favorites_list.addItem(empty_item)
            return
            
        for manga in self.favorites:
            item = QListWidgetItem(manga)
            item.setIcon(QIcon.fromTheme("emblem-favorite"))
            
            # Find thumbnail
            for folder_path in self.manga_folders:
                manga_path = os.path.join(folder_path, manga)
                if os.path.exists(manga_path) and os.path.isdir(manga_path):
                    # Find first PDF
                    pdf_files = get_pdf_files(manga_path)
                    if pdf_files:
                        pdf_path = os.path.join(manga_path, pdf_files[0])
                        
                        # Load thumbnail in thread
                        loader = ThumbnailLoader(pdf_path, self.cache_dir, self)
                        local_item = item  # Bind to local variable for lambda
                        loader.thumbnail_loaded.connect(
                            lambda path, pixmap, item=local_item: self.set_favorite_thumbnail(item, pixmap)
                        )
                        loader.start()
                        self.thumbnail_threads.append(loader)
                        break
            
            self.favorites_list.addItem(item)
    
    def set_favorite_thumbnail(self, item, pixmap):
        """
        Set thumbnail for favorites list item.
        
        Args:
            item: List item to set thumbnail for
            pixmap: Pixmap to set
        """
        # Check if item still exists
        if not item or not self.favorites_list.findItems(item.text(), Qt.MatchExactly):
            return
            
        if not pixmap.isNull():
            item.setIcon(QIcon(pixmap))
    
    def load_volumes_from_favorites(self, item):
        """
        Load volumes for a manga from favorites.
        
        Args:
            item: The selected favorites list item
        """
        manga_name = item.text()
        
        # Find manga folder
        for folder_path in self.manga_folders:
            manga_path = os.path.join(folder_path, manga_name)
            if os.path.exists(manga_path) and os.path.isdir(manga_path):
                # Set current manga
                self.current_manga = manga_name
                self.current_manga_path = manga_path
                
                # Display volumes
                files = get_pdf_files(manga_path)
                self.display_volumes(manga_path, files)
                
                # Switch to main tab
                self.tabs.setCurrentIndex(0)
                
                # Update favorite button
                self.favorite_button.setText("お気に入りから削除")
                
                # Emit signal that manga was selected
                self.manga_selected.emit(self.current_manga, self.current_manga_path)
                return
        
        QMessageBox.warning(self, "エラー", f"お気に入りの漫画「{manga_name}」のフォルダが見つかりませんでした。")
    
    def update_bookmarks_list(self):
        """Update the bookmarks list."""
        self.bookmarks_list.clear()
        
        if not self.bookmarks:
            # No bookmarks
            empty_item = QListWidgetItem("しおりはありません")
            empty_item.setFlags(Qt.NoItemFlags)  # Make unselectable
            self.bookmarks_list.addItem(empty_item)
            return
            
        for key, page in self.bookmarks.items():
            try:
                manga, volume = key.split('/', 1)
                item = QListWidgetItem(f"{manga} - {volume} (ページ {page + 1})")
                item.setData(Qt.UserRole, key)
                
                # Find thumbnail
                for folder_path in self.manga_folders:
                    manga_path = os.path.join(folder_path, manga)
                    if os.path.exists(manga_path) and os.path.isdir(manga_path):
                        pdf_path = os.path.join(manga_path, volume)
                        if os.path.exists(pdf_path):
                            # Load thumbnail in thread
                            loader = ThumbnailLoader(pdf_path, self.cache_dir, self)
                            local_item = item  # Bind to local variable for lambda
                            loader.thumbnail_loaded.connect(
                                lambda path, pixmap, item=local_item: self.set_bookmark_thumbnail(item, pixmap)
                            )
                            loader.start()
                            self.thumbnail_threads.append(loader)
                            break
                
                self.bookmarks_list.addItem(item)
            except Exception as e:
                print(f"Error displaying bookmark: {str(e)}")
    
    def set_bookmark_thumbnail(self, item, pixmap):
        """
        Set thumbnail for bookmarks list item.
        
        Args:
            item: List item to set thumbnail for
            pixmap: Pixmap to set
        """
        # Check if item still exists
        if not item or not self.bookmarks_list.findItems(item.text(), Qt.MatchContains):
            return
            
        if not pixmap.isNull():
            item.setIcon(QIcon(pixmap))
    
    def open_bookmark_from_list(self, item):
        """
        Open a bookmark from the list.
        
        Args:
            item: The selected bookmarks list item
        """
        key = item.data(Qt.UserRole)
        manga_name, volume = key.split('/', 1)
        
        # Find manga folder
        for folder_path in self.manga_folders:
            manga_path = os.path.join(folder_path, manga_name)
            if os.path.exists(manga_path) and os.path.isdir(manga_path):
                # Set current manga
                self.current_manga = manga_name
                self.current_manga_path = manga_path
                
                # Display volumes
                files = get_pdf_files(manga_path)
                self.display_volumes(manga_path, files)
                
                # Switch to main tab
                self.tabs.setCurrentIndex(0)
                
                # Update favorite button
                if manga_name in self.favorites:
                    self.favorite_button.setText("お気に入りから削除")
                else:
                    self.favorite_button.setText("お気に入りに追加")
                
                # Emit signals
                self.manga_selected.emit(self.current_manga, self.current_manga_path)
                self.volume_selected.emit(self.current_manga, self.current_manga_path, volume)
                return
        
        QMessageBox.warning(self, "エラー", f"しおりの漫画「{manga_name}」のフォルダが見つかりませんでした。")
    
    def show_favorites_context_menu(self, position):
        """
        Show context menu for favorites list.
        
        Args:
            position: Position to show menu at
        """
        item = self.favorites_list.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        remove_action = menu.addAction("お気に入りから削除")
        open_action = menu.addAction("開く")
        
        action = menu.exec_(self.favorites_list.mapToGlobal(position))
        
        if action == remove_action:
            manga = item.text()
            if manga in self.favorites:
                self.settings_manager.remove_favorite(manga)
                self.favorites = self.settings_manager.favorites
                self.update_favorites_list()
                self.load_manga_tree()
                QMessageBox.information(self, "お気に入り", f"{manga}をお気に入りから削除しました。")
        elif action == open_action:
            self.load_volumes_from_favorites(item)
    
    def show_bookmarks_context_menu(self, position):
        """
        Show context menu for bookmarks list.
        
        Args:
            position: Position to show menu at
        """
        item = self.bookmarks_list.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        remove_action = menu.addAction("しおりを削除")
        open_action = menu.addAction("開く")
        
        action = menu.exec_(self.bookmarks_list.mapToGlobal(position))
        
        if action == remove_action:
            key = item.data(Qt.UserRole)
            if key in self.bookmarks:
                manga, volume = key.split('/', 1)
                self.settings_manager.remove_bookmark(key)
                self.bookmarks = self.settings_manager.bookmarks
                self.update_bookmarks_list()
                QMessageBox.information(self, "しおり", f"{manga} - {volume}のしおりを削除しました。")
        elif action == open_action:
            self.open_bookmark_from_list(item)
    
    def closeEvent(self, event):
        """
        Handle close event.
        
        Args:
            event: Close event
        """
        # Clean up running threads
        for thread in self.thumbnail_threads:
            if thread.isRunning():
                thread.wait(500)  # Wait up to 0.5 seconds
