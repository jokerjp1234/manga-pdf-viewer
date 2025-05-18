import os
import hashlib
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
import fitz  # PyMuPDF

class ThumbnailLoader(QThread):
    """
    A worker thread for loading PDF thumbnails asynchronously.
    Caches thumbnails to disk for faster subsequent loading.
    """
    thumbnail_loaded = pyqtSignal(str, QPixmap)
    
    def __init__(self, pdf_path, cache_dir, parent=None):
        """
        Initialize the thumbnail loader thread.
        
        Args:
            pdf_path: Path to the PDF file
            cache_dir: Directory to store cached thumbnails
            parent: Parent QObject
        """
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.cache_dir = cache_dir
        
    def run(self):
        """Thread execution method to generate thumbnails from PDFs."""
        try:
            # Check/create cache folder
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
            
            # Generate cache filename using hash of the path
            cache_file = os.path.join(
                self.cache_dir, 
                hashlib.md5(self.pdf_path.encode()).hexdigest() + ".png"
            )
            
            # Use cache if it exists
            if os.path.exists(cache_file):
                pixmap = QPixmap(cache_file)
                self.thumbnail_loaded.emit(self.pdf_path, pixmap)
                return
            
            # Generate new thumbnail from the first page
            doc = fitz.open(self.pdf_path)
            if doc.page_count > 0:
                page = doc.load_page(0)
                # Set appropriate thumbnail size
                pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
                
                # Convert to QImage
                img_data = pix.samples
                img_format = QImage.Format_RGB888 if pix.n == 3 else QImage.Format_RGBA8888
                qimage = QImage(img_data, pix.width, pix.height, pix.stride, img_format)
                
                # Convert to QPixmap
                pixmap = QPixmap.fromImage(qimage)
                
                # Save to cache
                pixmap.save(cache_file)
                
                # Emit signal with the thumbnail
                self.thumbnail_loaded.emit(self.pdf_path, pixmap)
                
            doc.close()
        except Exception as e:
            print(f"Thumbnail generation error: {str(e)}")
            # Emit empty pixmap on error
            self.thumbnail_loaded.emit(self.pdf_path, QPixmap())
