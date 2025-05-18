import fitz  # PyMuPDF
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QScrollArea, QPushButton, QMessageBox,
                            QLineEdit, QSpinBox, QDialog, QFormLayout)
from PyQt5.QtCore import Qt, QEvent, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QFont

class PDFViewer(QWidget):
    """
    Handles PDF viewing functionality.
    """
    # Signals
    page_changed = pyqtSignal(int, int)  # current page, total pages
    
    def __init__(self, settings_manager, parent=None):
        """
        Initialize PDF viewer.
        
        Args:
            settings_manager: The application settings manager
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.settings_manager = settings_manager
        self.current_manga = None
        self.current_volume = None
        self.pdf_document = None
        self.current_page = 0
        self.total_pages = 0
        self.fit_to_window = True
        self.is_fullscreen = False
        
        # Get keyboard and mouse settings
        self.use_arrow_keys = self.settings_manager.get_setting("use_arrow_keys", True)
        self.left_click_next = self.settings_manager.get_setting("left_click_next", True)
        
        # Set up the UI
        self.setup_ui()
        
        # Apply event filters for keyboard navigation
        self.scroll_area.installEventFilter(self)
        self.image_label.installEventFilter(self)
    
    def setup_ui(self):
        """Set up the user interface elements."""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Title bar to show current manga and volume
        self.title_layout = QHBoxLayout()
        
        self.manga_title_label = QLabel("漫画が選択されていません")
        self.manga_title_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.manga_title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_layout.addWidget(self.manga_title_label)
        
        # Stretch to push the page jump button to the right
        self.title_layout.addStretch()
        
        # Page jump button
        self.page_jump_button = QPushButton("ページ移動 (Ctrl+G)")
        self.page_jump_button.setToolTip("特定のページに移動します (ショートカット: Ctrl+G)")
        self.page_jump_button.clicked.connect(self.show_page_jump_dialog)
        self.title_layout.addWidget(self.page_jump_button)
        
        layout.addLayout(self.title_layout)
        
        # PDF display
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFocusPolicy(Qt.StrongFocus)  # Enable focus for key events
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self.on_image_click
        self.image_label.setFocusPolicy(Qt.StrongFocus)  # Enable focus for key events
        
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)
        
        # Page controls
        controls_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("前のページ")
        self.prev_button.clicked.connect(self.prev_page)
        controls_layout.addWidget(self.prev_button)
        
        self.page_label = QLabel("0 / 0")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setMinimumWidth(100)
        controls_layout.addWidget(self.page_label)
        
        self.next_button = QPushButton("次のページ")
        self.next_button.clicked.connect(self.next_page)
        controls_layout.addWidget(self.next_button)
        
        layout.addLayout(controls_layout)
    
    def show_page_jump_dialog(self):
        """Show dialog to jump to a specific page."""
        if not self.pdf_document:
            QMessageBox.information(self, "情報", "PDFが開かれていません。")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("ページ移動")
        dialog.setMinimumWidth(250)
        
        form_layout = QFormLayout(dialog)
        
        # Use a spinner with limits
        page_spinner = QSpinBox(dialog)
        page_spinner.setMinimum(1)
        page_spinner.setMaximum(self.total_pages)
        page_spinner.setValue(self.current_page + 1)  # 1-based for display
        form_layout.addRow(f"ページ番号 (1-{self.total_pages})", page_spinner)
        
        button_layout = QHBoxLayout()
        ok_button = QPushButton("移動", dialog)
        cancel_button = QPushButton("キャンセル", dialog)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        form_layout.addRow("", button_layout)
        
        # Connect buttons
        ok_button.clicked.connect(lambda: self.jump_to_page(page_spinner.value() - 1) or dialog.accept())
        cancel_button.clicked.connect(dialog.reject)
        
        # Set focus to spinner and select all text
        page_spinner.selectAll()
        page_spinner.setFocus()
        
        dialog.exec_()
    
    def jump_to_page(self, page):
        """
        Jump to the specified page.
        
        Args:
            page: 0-based page index
            
        Returns:
            Boolean indicating success
        """
        if not self.pdf_document:
            return False
            
        if 0 <= page < self.total_pages:
            self.current_page = page
            self.display_page()
            return True
            
        return False
    
    def update_title_display(self):
        """Update the title display with current manga and volume information."""
        if self.current_manga and self.current_volume:
            self.manga_title_label.setText(f"現在読んでいる漫画: {self.current_manga} - {self.current_volume}")
        else:
            self.manga_title_label.setText("漫画が選択されていません")
    
    def load_pdf(self, manga_name, manga_path, volume_name):
        """
        Load a PDF file.
        
        Args:
            manga_name: Name of the manga
            manga_path: Path to the manga directory
            volume_name: Name of the volume (PDF file)
            
        Returns:
            Boolean indicating success
        """
        import os
        
        self.current_manga = manga_name
        self.current_volume = volume_name
        pdf_path = os.path.join(manga_path, volume_name)
        
        # Update title display
        self.update_title_display()
        
        # Close any open document
        if self.pdf_document:
            self.pdf_document.close()
            self.pdf_document = None
        
        try:
            self.pdf_document = fitz.open(pdf_path)
            self.total_pages = len(self.pdf_document)
            
            # Check for bookmark
            bookmark_key = f"{manga_name}/{volume_name}"
            if bookmark_key in self.settings_manager.bookmarks:
                # Ask user if they want to continue from bookmark
                reply = QMessageBox.question(
                    self, 
                    "しおり", 
                    f"前回の続き({self.settings_manager.bookmarks[bookmark_key] + 1}ページ目)から読みますか？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.current_page = self.settings_manager.bookmarks[bookmark_key]
                else:
                    self.current_page = 0
            else:
                self.current_page = 0
            
            # Display first page
            self.display_page()
            
            # Focus on the scroll area for keyboard navigation
            self.scroll_area.setFocus()
            self.image_label.setFocus()
            
            return True
            
        except Exception as e:
            QMessageBox.warning(
                self, 
                "エラー", 
                f"PDFの読み込み中にエラーが発生しました: {str(e)}"
            )
            return False
    
    def display_page(self):
        """Display the current page of the PDF."""
        if not self.pdf_document or self.current_page >= self.total_pages:
            return
        
        try:
            # Get the page
            page = self.pdf_document.load_page(self.current_page)
            
            # Fit to window if enabled
            if self.fit_to_window:
                # Get scroll area size
                view_width = self.scroll_area.viewport().width()
                view_height = self.scroll_area.viewport().height()
                
                # Get page size
                page_rect = page.rect
                page_width = page_rect.width
                page_height = page_rect.height
                
                # Calculate zoom factor to fit page while maintaining aspect ratio
                width_ratio = view_width / page_width
                height_ratio = view_height / page_height
                zoom_factor = min(width_ratio, height_ratio) * 0.98  # Add small margin
                
                # Get pixmap with appropriate zoom
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom_factor, zoom_factor))
            else:
                # Fixed zoom
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            
            # Convert to QImage
            img_data = pix.samples
            img_format = QImage.Format_RGB888 if pix.n == 3 else QImage.Format_RGBA8888
            qimage = QImage(img_data, pix.width, pix.height, pix.stride, img_format)
            
            # Display the image
            self.image_label.setPixmap(QPixmap.fromImage(qimage))
            
            # Update page number
            self.page_label.setText(f"{self.current_page + 1} / {self.total_pages}")
            
            # Emit signal for page change
            self.page_changed.emit(self.current_page, self.total_pages)
            
            # Save bookmark automatically
            if self.current_manga and self.current_volume:
                self.settings_manager.add_bookmark(
                    self.current_manga, 
                    self.current_volume, 
                    self.current_page
                )
            
            # Set focus for key navigation
            self.scroll_area.setFocus()
            self.image_label.setFocus()
            
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"ページの表示中にエラーが発生しました: {str(e)}")
    
    def next_page(self):
        """Go to the next page."""
        if self.pdf_document and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.display_page()
        elif self.pdf_document and self.current_page == self.total_pages - 1:
            QMessageBox.information(self, "情報", "最後のページです。")
    
    def prev_page(self):
        """Go to the previous page."""
        if self.pdf_document and self.current_page > 0:
            self.current_page -= 1
            self.display_page()
        elif self.pdf_document and self.current_page == 0:
            QMessageBox.information(self, "情報", "最初のページです。")
    
    def go_to_page(self, page_number):
        """
        Go to a specific page.
        
        Args:
            page_number: Page number to go to (0-based index)
        """
        if self.pdf_document and 0 <= page_number < self.total_pages:
            self.current_page = page_number
            self.display_page()
    
    def on_image_click(self, event):
        """
        Handle mouse clicks on the image.
        
        Args:
            event: Mouse event
        """
        if not self.pdf_document:
            return
            
        if event.button() == Qt.LeftButton:
            if self.left_click_next:
                self.next_page()
            else:
                self.prev_page()
        elif event.button() == Qt.RightButton:
            if self.left_click_next:
                self.prev_page()
            else:
                self.next_page()
    
    def toggle_fit_to_window(self, checked):
        """
        Toggle fit-to-window mode.
        
        Args:
            checked: New state
        """
        self.fit_to_window = checked
        if self.pdf_document:
            self.display_page()
    
    def eventFilter(self, obj, event):
        """
        Filter events for keyboard navigation.
        
        Args:
            obj: Object that generated the event
            event: Event
            
        Returns:
            Boolean indicating if event was handled
        """
        if event.type() == QEvent.KeyPress and self.pdf_document:
            # Handle shortcut for page jump (Ctrl+G)
            if event.key() == Qt.Key_G and event.modifiers() == Qt.ControlModifier:
                self.show_page_jump_dialog()
                return True
                
            # Handle arrow keys if enabled
            if self.use_arrow_keys:
                if event.key() == Qt.Key_Right or event.key() == Qt.Key_Down:
                    self.next_page()
                    return True
                elif event.key() == Qt.Key_Left or event.key() == Qt.Key_Up:
                    self.prev_page()
                    return True
                elif event.key() == Qt.Key_Home:
                    self.go_to_page(0)
                    return True
                elif event.key() == Qt.Key_End:
                    self.go_to_page(self.total_pages - 1)
                    return True
        
        return super().eventFilter(obj, event)
    
    def keyPressEvent(self, event):
        """
        Handle key press events.
        
        Args:
            event: Key event
        """
        # Handle shortcut for page jump
        if self.pdf_document and event.key() == Qt.Key_G and event.modifiers() == Qt.ControlModifier:
            self.show_page_jump_dialog()
            return
            
        # Handle navigation keys if enabled
        if self.pdf_document and self.use_arrow_keys:
            if event.key() == Qt.Key_Right or event.key() == Qt.Key_Down:
                self.next_page()
                return
            elif event.key() == Qt.Key_Left or event.key() == Qt.Key_Up:
                self.prev_page()
                return
            elif event.key() == Qt.Key_Home:
                self.go_to_page(0)
                return
            elif event.key() == Qt.Key_End:
                self.go_to_page(self.total_pages - 1)
                return
        
        super().keyPressEvent(event)
    
    def close_document(self):
        """Close the current document and clean up."""
        if self.pdf_document:
            self.pdf_document.close()
            self.pdf_document = None
            self.current_page = 0
            self.total_pages = 0
            self.page_label.setText("0 / 0")
            self.image_label.clear()
            
            # Reset title
            self.current_manga = None
            self.current_volume = None
            self.update_title_display()
