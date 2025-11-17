import sys
import os
import hashlib
import io
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                            QScrollArea, QFrame, QFileDialog, QMessageBox, 
                            QProgressBar, QLineEdit, QSpinBox, QToolBar,
                            QStatusBar, QDockWidget, QSlider,
                            QComboBox, QTabWidget, QTreeWidget, QTreeWidgetItem,
                            QSplitter, QMenuBar, QAction)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QDir, QBuffer, QIODevice
from PyQt5.QtGui import QPixmap, QIcon, QFont, QPalette, QColor

try:
    import fitz  # PyMuPDF
    from PIL import Image
except ImportError:
    print("Required packages not installed. Please install PyMuPDF and Pillow.")
    sys.exit(1)

class ThumbnailWorker(QThread):
    """Worker thread for generating thumbnails"""
    thumbnail_ready = pyqtSignal(str, object)  # path, image
    progress_updated = pyqtSignal(int)  # progress percentage
    
    def __init__(self, pdf_files, folder_path, cache_dir, thumbnail_size, page_num=0):
        super().__init__()
        self.pdf_files = pdf_files
        self.folder_path = folder_path
        self.cache_dir = cache_dir
        self.thumbnail_size = thumbnail_size
        self.page_num = page_num
        self.is_running = True
    
    def run(self):
        """Generate thumbnails for all PDF files"""
        total = len(self.pdf_files)
        for i, pdf_file in enumerate(self.pdf_files):
            if not self.is_running:
                break
                
            pdf_path = os.path.join(self.folder_path, pdf_file)
            thumbnail = self.generate_thumbnail(pdf_path, self.page_num)
            self.thumbnail_ready.emit(pdf_path, thumbnail)
            self.progress_updated.emit(int((i + 1) / total * 100))
    
    def generate_thumbnail(self, pdf_path, page_num=0):
        """Generate thumbnail from PDF page"""
        cache_file = self.get_cache_filename(pdf_path, page_num)
        
        if cache_file.exists():
            try:
                return Image.open(cache_file)
            except Exception:
                # Corrupted cache file, regenerate
                pass
        
        doc = None
        try:
            doc = fitz.open(pdf_path)
            if page_num >= len(doc):
                page_num = min(len(doc) - 1, 0)  # Use last page if requested page doesn't exist
            
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
            
            # Save with optimization
            img.save(cache_file, "PNG", optimize=True)
            return img
            
        except Exception as e:
            print(f"Error generating thumbnail for {pdf_path}: {e}")
            return self.create_placeholder_thumbnail()
        finally:
            if doc:
                doc.close()
    
    def get_cache_filename(self, pdf_path, page_num=0):
        """Generate a unique cache filename for a PDF thumbnail"""
        try:
            file_stat = os.stat(pdf_path)
            cache_key = f"{pdf_path}_{file_stat.st_mtime}_{page_num}"
            hash_name = hashlib.md5(cache_key.encode()).hexdigest()[:12]
            
            pdf_filename = Path(pdf_path).stem
            safe_filename = "".join(c for c in pdf_filename if c.isalnum() or c in ('-', '_')).rstrip()
            cache_filename = f"{safe_filename}_{hash_name}_p{page_num}.png"
            
            return self.cache_dir / cache_filename
        except Exception:
            # Fallback if file stats can't be read
            pdf_filename = Path(pdf_path).name
            safe_filename = "".join(c for c in pdf_filename if c.isalnum() or c in ('-', '_')).rstrip()
            cache_filename = f"{safe_filename}_p{page_num}.png"
            return self.cache_dir / cache_filename
    
    def create_placeholder_thumbnail(self):
        """Create a placeholder thumbnail when PDF can't be processed"""
        return Image.new('RGB', self.thumbnail_size, color='lightgray')
    
    def stop(self):
        """Stop the thumbnail generation process"""
        self.is_running = False

class PDFViewer(QWidget):
    """Widget for viewing PDF pages"""
    def __init__(self):
        super().__init__()
        self.current_pdf_doc = None
        self.current_page = 0
        self.total_pages = 0
        self.viewer_zoom = 1.0
        self.selected_pdf = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the PDF viewer UI"""
        layout = QVBoxLayout()
        
        # Toolbar for navigation and zoom controls
        toolbar = QToolBar()
        
        self.prev_btn = toolbar.addAction("◀ Previous")
        self.prev_btn.triggered.connect(self.previous_page)
        
        self.page_label = QLabel("Page: - / -")
        toolbar.addWidget(self.page_label)
        
        self.next_btn = toolbar.addAction("Next ▶")
        self.next_btn.triggered.connect(self.next_page)
        
        toolbar.addWidget(QLabel("Go to:"))
        self.page_entry = QLineEdit()
        self.page_entry.setMaximumWidth(50)
        self.page_entry.returnPressed.connect(self.go_to_page)
        toolbar.addWidget(self.page_entry)
        
        toolbar.addWidget(QLabel("Zoom:"))
        self.zoom_out_btn = toolbar.addAction("-")
        self.zoom_out_btn.triggered.connect(self.zoom_out)
        
        self.zoom_in_btn = toolbar.addAction("+")
        self.zoom_in_btn.triggered.connect(self.zoom_in)
        
        self.zoom_reset_btn = toolbar.addAction("Reset")
        self.zoom_reset_btn.triggered.connect(self.zoom_reset)
        
        self.open_external_btn = toolbar.addAction("Open Externally")
        self.open_external_btn.triggered.connect(self.open_pdf)
        
        layout.addWidget(toolbar)
        
        # Scroll area for PDF display
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        
        self.image_label = QLabel("Select a PDF from the list to view it here")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        self.image_label.setMinimumSize(400, 300)
        
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)
    
    def display_pdf(self, pdf_path):
        """Display PDF in the viewer"""
        try:
            self.selected_pdf = pdf_path
            doc = fitz.open(pdf_path)
            
            # Close previous document
            if self.current_pdf_doc:
                self.current_pdf_doc.close()
            
            self.current_pdf_doc = doc
            self.total_pages = len(doc)
            self.current_page = min(0, self.total_pages - 1)
            
            self.display_current_page()
            
        except Exception as e:
            print(f"Error displaying PDF: {e}")
            QMessageBox.critical(self, "Error", f"Could not display PDF: {e}")
    
    def display_current_page(self):
        """Display the current page in the viewer"""
        if not self.current_pdf_doc:
            return
            
        try:
            page = self.current_pdf_doc[self.current_page]
            zoom_factor = self.viewer_zoom * 2.5  # Higher base resolution
            mat = fitz.Matrix(zoom_factor, zoom_factor)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert directly to QPixmap without PIL intermediate step
            q_image = QPixmap()
            q_image.loadFromData(pix.tobytes("png"))
            
            self.image_label.setPixmap(q_image)
            self.image_label.resize(q_image.size())
            self.update_page_info()
            
        except Exception as e:
            print(f"Error rendering PDF page: {e}")
    
    def update_page_info(self):
        """Update the page navigation info"""
        if self.total_pages > 0:
            self.page_label.setText(f"Page: {self.current_page + 1} / {self.total_pages}")
            self.page_entry.setText(str(self.current_page + 1))
        else:
            self.page_label.setText("Page: - / -")
            self.page_entry.setText("")
    
    def previous_page(self):
        """Go to previous page"""
        if self.current_pdf_doc and self.current_page > 0:
            self.current_page -= 1
            self.display_current_page()
    
    def next_page(self):
        """Go to next page"""
        if self.current_pdf_doc and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.display_current_page()
    
    def go_to_page(self):
        """Go to specific page number"""
        try:
            page_num = int(self.page_entry.text()) - 1
            if 0 <= page_num < self.total_pages:
                self.current_page = page_num
                self.display_current_page()
        except ValueError:
            pass
    
    def zoom_in(self):
        """Zoom in the PDF view"""
        self.viewer_zoom = min(self.viewer_zoom * 1.2, 5.0)  # Max zoom 5x
        if self.selected_pdf:
            self.display_current_page()
    
    def zoom_out(self):
        """Zoom out the PDF view"""
        self.viewer_zoom = max(self.viewer_zoom / 1.2, 0.1)  # Min zoom 0.1x
        if self.selected_pdf:
            self.display_current_page()
    
    def zoom_reset(self):
        """Reset zoom to 100%"""
        self.viewer_zoom = 1.0
        if self.selected_pdf:
            self.display_current_page()
    
    def open_pdf(self):
        """Open selected PDF file in external viewer"""
        if self.selected_pdf and os.path.exists(self.selected_pdf):
            try:
                if sys.platform == 'win32':
                    os.startfile(self.selected_pdf)
                elif sys.platform == 'darwin':  # macOS
                    os.system(f'open "{self.selected_pdf}"')
                else:  # Linux
                    os.system(f'xdg-open "{self.selected_pdf}"')
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open PDF: {e}")
        else:
            QMessageBox.warning(self, "No PDF selected", "Please select a PDF first")

class ThumbnailWidget(QLabel):
    """Widget for displaying a PDF thumbnail"""
    clicked = pyqtSignal(str)  # path
    
    def __init__(self, pdf_path, thumbnail=None):
        super().__init__()
        self.pdf_path = pdf_path
        self.thumbnail = thumbnail
        self.init_ui()
    
    def init_ui(self):
        """Initialize the thumbnail widget"""
        self.setFixedSize(120, 160)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QLabel:hover {
                border: 2px solid #4a90e2;
            }
        """)
        
        if self.thumbnail:
            self.set_thumbnail(self.thumbnail)
        else:
            self.setText("Loading...")
        
        # Mouse events
        self.mousePressEvent = self.on_click
    
    def set_thumbnail(self, thumbnail):
        """Set the thumbnail image"""
        self.thumbnail = thumbnail
        if thumbnail:
            # Convert PIL image to QPixmap using a different approach
            # Save PIL image to a buffer in memory
            buffer = QBuffer()
            buffer.open(QIODevice.ReadWrite)
            
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            thumbnail.save(img_byte_arr, format='PNG')
            
            # Load from bytes to QPixmap
            pixmap = QPixmap()
            pixmap.loadFromData(img_byte_arr.getvalue())
            
            self.setPixmap(pixmap.scaled(100, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
            # Set tooltip with filename
            filename = os.path.basename(self.pdf_path)
            self.setToolTip(filename)
    
    def on_click(self, event):
        """Handle click events"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.pdf_path)

class PDFLibraryWidget(QWidget):
    """Widget for displaying PDF library with thumbnails"""
    pdf_selected = pyqtSignal(str)  # path
    
    def __init__(self):
        super().__init__()
        self.current_folder = ""
        self.current_pdfs = []
        self.thumbnail_widgets = {}
        self.cache_dir = Path("./thumbnail_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.thumbnail_size = (100, 140)
        self.thumbnail_worker = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the PDF library UI"""
        layout = QVBoxLayout()
        
        # Folder controls
        folder_frame = QFrame()
        folder_layout = QHBoxLayout(folder_frame)
        
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setWordWrap(True)
        folder_layout.addWidget(self.folder_label)
        
        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.clicked.connect(self.open_folder)
        folder_layout.addWidget(self.open_folder_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_library)
        folder_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(folder_frame)
        
        # Search
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        
        search_layout.addWidget(QLabel("Search:"))
        self.search_entry = QLineEdit()
        self.search_entry.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_entry)
        
        layout.addWidget(search_frame)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Thumbnail grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.thumbnail_grid = QWidget()
        self.grid_layout = QGridLayout(self.thumbnail_grid)
        self.grid_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.thumbnail_grid)
        layout.addWidget(self.scroll_area)
        
        # Thumbnail settings
        settings_frame = QFrame()
        settings_layout = QVBoxLayout(settings_frame)
        
        thumbnail_settings = QFrame()
        thumbnail_settings_layout = QHBoxLayout(thumbnail_settings)
        
        thumbnail_settings_layout.addWidget(QLabel("Thumbnail page:"))
        self.thumbnail_page_spin = QSpinBox()
        self.thumbnail_page_spin.setRange(0, 999)
        self.thumbnail_page_spin.setValue(0)
        thumbnail_settings_layout.addWidget(self.thumbnail_page_spin)
        
        self.apply_selected_btn = QPushButton("Apply to Selected")
        self.apply_selected_btn.clicked.connect(self.apply_thumbnail_to_selected)
        thumbnail_settings_layout.addWidget(self.apply_selected_btn)
        
        self.apply_all_btn = QPushButton("Apply to All")
        self.apply_all_btn.clicked.connect(self.apply_thumbnail_settings)
        thumbnail_settings_layout.addWidget(self.apply_all_btn)
        
        settings_layout.addWidget(thumbnail_settings)
        
        self.clear_cache_btn = QPushButton("Clear Cache")
        self.clear_cache_btn.clicked.connect(self.clear_thumbnail_cache)
        settings_layout.addWidget(self.clear_cache_btn)
        
        layout.addWidget(settings_frame)
        
        self.setLayout(layout)
    
    def open_folder(self):
        """Open a folder containing PDFs"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.current_folder = folder_path
            self.folder_label.setText(f"Folder: {os.path.basename(folder_path)}")
            self.load_pdfs_from_folder(folder_path)
    
    def load_pdfs_from_folder(self, folder_path):
        """Load all PDF files from the selected folder"""
        try:
            pdf_files = [f for f in os.listdir(folder_path) 
                        if f.lower().endswith('.pdf') and os.path.isfile(os.path.join(folder_path, f))]
            pdf_files.sort()  # Sort alphabetically
            self.current_pdfs = pdf_files
            
            self.load_thumbnails_async(pdf_files, folder_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load PDFs: {e}")
    
    def load_thumbnails_async(self, pdf_files, folder_path):
        """Load thumbnails asynchronously"""
        # Stop any existing worker
        if self.thumbnail_worker and self.thumbnail_worker.isRunning():
            self.thumbnail_worker.stop()
            self.thumbnail_worker.wait()
        
        # Clear existing thumbnails
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        self.thumbnail_widgets = {}
        
        if not pdf_files:
            no_files_label = QLabel("No PDF files found in selected folder")
            no_files_label.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(no_files_label, 0, 0)
            return
        
        # Create placeholder widgets
        for i, pdf_file in enumerate(pdf_files):
            pdf_path = os.path.join(folder_path, pdf_file)
            row = i // 4
            col = i % 4
            
            thumbnail_widget = ThumbnailWidget(pdf_path)
            thumbnail_widget.clicked.connect(self.on_thumbnail_clicked)
            
            self.grid_layout.addWidget(thumbnail_widget, row, col)
            self.thumbnail_widgets[pdf_path] = thumbnail_widget
        
        # Start worker thread
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.thumbnail_worker = ThumbnailWorker(
            pdf_files, folder_path, self.cache_dir, 
            self.thumbnail_size, self.thumbnail_page_spin.value()
        )
        self.thumbnail_worker.thumbnail_ready.connect(self.on_thumbnail_ready)
        self.thumbnail_worker.progress_updated.connect(self.on_progress_updated)
        self.thumbnail_worker.start()
    
    def on_thumbnail_ready(self, pdf_path, thumbnail):
        """Handle thumbnail generation completion"""
        if pdf_path in self.thumbnail_widgets:
            self.thumbnail_widgets[pdf_path].set_thumbnail(thumbnail)
    
    def on_progress_updated(self, value):
        """Handle progress updates"""
        self.progress_bar.setValue(value)
        if value >= 100:
            self.progress_bar.setVisible(False)
    
    def on_thumbnail_clicked(self, pdf_path):
        """Handle thumbnail click"""
        self.pdf_selected.emit(pdf_path)
    
    def on_search(self, text):
        """Handle search functionality"""
        search_term = text.lower()
        if not search_term and self.current_folder:
            # If search is cleared, show all PDFs
            self.load_pdfs_from_folder(self.current_folder)
        elif search_term and self.current_folder:
            # Filter PDFs based on search term
            filtered_pdfs = [f for f in self.current_pdfs if search_term in f.lower()]
            self.load_thumbnails_async(filtered_pdfs, self.current_folder)
    
    def refresh_library(self):
        """Refresh the current library view"""
        if self.current_folder:
            self.load_pdfs_from_folder(self.current_folder)
    
    def apply_thumbnail_to_selected(self):
        """Apply thumbnail page setting only to the selected PDF"""
        # This would need to track which PDF is selected
        # For simplicity, we'll just apply to all
        self.apply_thumbnail_settings()
    
    def apply_thumbnail_settings(self):
        """Apply thumbnail page settings to all PDFs"""
        try:
            # Clear cache
            cache_files = list(self.cache_dir.glob("*.png"))
            for cache_file in cache_files:
                cache_file.unlink()
            
            if self.current_folder:
                self.refresh_library()
                QMessageBox.information(self, "Success", 
                                      f"Thumbnail settings applied to all PDFs\nCleared {len(cache_files)} cached thumbnails")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not apply settings: {e}")
    
    def clear_thumbnail_cache(self):
        """Clear all cached thumbnails"""
        try:
            cache_files = list(self.cache_dir.glob("*.png"))
            for cache_file in cache_files:
                cache_file.unlink()
            
            QMessageBox.information(self, "Cache Cleared", 
                                  f"Cleared {len(cache_files)} cached thumbnails")
            
            if self.current_folder:
                self.refresh_library()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not clear cache: {e}")

class PDFLibraryMainWindow(QMainWindow):
    """Main window for the PDF Library application"""
    def __init__(self):
        super().__init__()
        self.selected_pdf = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the main window UI"""
        self.setWindowTitle("PDF Library Viewer")
        self.setGeometry(100, 100, 1400, 800)
        
        # Create central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - PDF library
        self.pdf_library = PDFLibraryWidget()
        self.pdf_library.pdf_selected.connect(self.on_pdf_selected)
        splitter.addWidget(self.pdf_library)
        
        # Right panel - PDF viewer
        self.pdf_viewer = PDFViewer()
        splitter.addWidget(self.pdf_viewer)
        
        # Set splitter proportions
        splitter.setSizes([350, 1050])
        
        layout.addWidget(splitter)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
    
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_folder_action = file_menu.addAction("Open Folder")
        open_folder_action.triggered.connect(self.pdf_library.open_folder)
        
        refresh_action = file_menu.addAction("Refresh")
        refresh_action.triggered.connect(self.pdf_library.refresh_library)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        clear_cache_action = tools_menu.addAction("Clear Cache")
        clear_cache_action.triggered.connect(self.pdf_library.clear_thumbnail_cache)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)
    
    def create_toolbar(self):
        """Create the toolbar"""
        toolbar = self.addToolBar("Main")
        
        open_folder_action = toolbar.addAction("Open Folder")
        open_folder_action.triggered.connect(self.pdf_library.open_folder)
        
        refresh_action = toolbar.addAction("Refresh")
        refresh_action.triggered.connect(self.pdf_library.refresh_library)
    
    def on_pdf_selected(self, pdf_path):
        """Handle PDF selection"""
        self.selected_pdf = pdf_path
        self.pdf_viewer.display_pdf(pdf_path)
        
        # Update status bar
        filename = os.path.basename(pdf_path)
        self.status_bar.showMessage(f"Selected: {filename}")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About PDF Library Viewer", 
                         "PDF Library Viewer\n\nA modern PDF viewer with thumbnail previews\n\n"
                         "Features:\n"
                         "- Thumbnail previews\n"
                         "- PDF viewing with navigation\n"
                         "- Zoom controls\n"
                         "- Search functionality\n"
                         "- Thumbnail caching")

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = PDFLibraryMainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
