# PDF Library Manager

![Windows](https://img.shields.io/badge/Windows-11-0078D6?logo=windows&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-Ubuntu|Fedora|Debian-E95420?logo=linux&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.6%2B-3776AB?logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15%2B-41CD52?logo=qt&logoColor=white)

A powerful Python desktop application that creates a visual library of your PDF files with customizable thumbnails. Built with PyQt5 for a modern, professional interface that solves the common problem of PDF thumbnail generation on Windows 11 and Linux systems.

Image 1: App with PDF Thumbnail preview — `PDFs not included with this app`.
<img width="1438" height="870" alt="image" src="https://github.com/user-attachments/assets/1a486611-c30a-461d-b570-e67cb2d43405" />  
__PDFs not included with this app__


## 🎯 The Problem This Solves

**Windows 11 Thumbnail Issue**: Many Windows 11 users experience problems with PDF thumbnails not displaying correctly in File Explorer. The built-in thumbnail cache system can be unreliable, leaving you with generic PDF icons instead of meaningful previews.

**Visual PDF Management**: PDF filenames don't always reflect the actual content. This app provides visual previews so you can quickly identify documents without opening each one.

## ✨ Key Features

- **Modern PyQt5 Interface**: Professional-looking GUI with smooth interactions
- **Visual PDF Library**: Grid view with thumbnail previews of your PDFs
- **Built-in PDF Viewer**: Full PDF viewing with navigation and zoom controls
- **Custom Thumbnail Pages**: Choose any page from a PDF to use as its thumbnail
- **Individual or Bulk Thumbnail Control**: Update thumbnails for single files or entire libraries
- **Fast Search**: Real-time filtering by filename
- **Smart Caching**: Automatic thumbnail caching for quick loading
- **Cross-Platform**: Works on both Windows 11 and Linux distributions

![test](appdemo.gif)

## 🆚 What's New in This Version

- **Upgraded GUI**: Replaced Tkinter with PyQt5 for a more professional appearance
- **Built-in PDF Viewer**: No need to open external applications to view PDFs
- **Better Performance**: Improved threading and memory management
- **Enhanced UI**: Modern toolbars, menus, and status bar
- **Improved Search**: More responsive search functionality
- **Better Error Handling**: More informative error messages and graceful failure handling

## 🚀 Quick Start Guide

### Step 1: Download and Extract
1. Click the **"Code"** button above
2. Select **"Download ZIP"**
3. Extract the ZIP file to your preferred location

### Step 2: Set Up Virtual Environment
Open terminal/command prompt in the extracted folder and run:

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Requirements
```bash
pip install -r requirements.txt
```
or  
```bash
pip install PyQt5 PyMuPDF Pillow
```

### Step 4: Run the Application
```bash
python main.py
```

## 🛠️ Technical Challenges Overcome

### 1. **Thumbnail Generation**
- **Challenge**: Extracting high-quality previews from PDF files
- **Solution**: Uses PyMuPDF for reliable PDF rendering and Pillow for image processing

### 2. **Performance Optimization**
- **Challenge**: Generating thumbnails for large PDF collections
- **Solution**: Smart caching system that stores thumbnails for instant loading

### 3. **Cross-Platform Compatibility**
- **Challenge**: Different file handling between Windows and Linux
- **Solution**: Python's pathlib for consistent file path management

### 4. **UI Responsiveness**
- **Challenge**: Preventing GUI freezing during thumbnail generation
- **Solution**: Efficient threading with QThread and progressive loading

### 5. **Image Conversion**
- **Challenge**: Converting between PIL images and Qt pixmaps
- **Solution**: Implemented a robust image conversion system using in-memory buffers

## 📁 Project Structure

```
pdf-library-manager/
├── main.py     # Main application file (PyQt5 version)
├── appdemo.gif   # GIF made on the site https://ezgif.com/
├── requirements.txt        # Python dependencies
├── thumbnail_cache/        # Auto-generated thumbnail cache
└── README.md              # This file
```

## 🎮 How to Use

1. **Open a Folder**: Click "Open Folder" in the toolbar or File menu and select a directory containing PDFs
2. **Browse Visually**: See all your PDFs as thumbnails with their first pages
3. **View PDFs**: Click any thumbnail to open the PDF in the built-in viewer
4. **Navigate PDFs**: Use the navigation controls to browse through pages, zoom in/out
5. **Customize Thumbnails**:
   - Enter a page number in the "Thumbnail page" field (0 = first page)
   - Click "Apply to Selected" for individual files
   - Click "Apply to All" for the entire library
6. **Search**: Use the search box to filter PDFs by filename
7. **Manage Files**: Open PDFs externally or delete them using the buttons or menu

## 🔧 Technical Details

- **GUI Framework**: PyQt5 for modern, professional interface
- **PDF Processing**: PyMuPDF (fitz) for high-quality rendering
- **Image Handling**: Pillow (PIL) for thumbnail manipulation
- **Cache System**: MD5-hashed filenames with original PDF names for easy management
- **Threading**: QThread for non-blocking thumbnail generation
- **Layout Management**: QSplitter, QGridLayout, and QScrollArea for responsive UI

## 🤝 Contributing

This is a learning project! Feel free to:
- Report bugs or suggest features
- Fork and modify for your own needs
- Study the code to learn about Python GUI development
- Improve the documentation

## 💡 Learning Opportunities

This project demonstrates:
- Python GUI development with PyQt5
- Signal-slot mechanism for event handling
- PDF processing and image manipulation
- File system operations and caching strategies
- Cross-platform application development
- Threading for responsive applications
- Modern UI design principles
- Error handling and user feedback

## 🐛 Troubleshooting

**Common Issues:**
- **Missing dependencies**: Ensure you ran `pip install -r requirements.txt`
- **Blank thumbnails**: Some PDFs may be encrypted or corrupted
- **Slow loading**: First-time thumbnail generation takes longer; subsequent loads use cache
- **Import errors**: Make sure you have PyQt5, PyMuPDF, and Pillow installed correctly

**Need Help?** Check that all requirements are installed and your PDF files are accessible.

## 📚 Resources for Learners

If you're interested in learning more about the technologies used in this project:

- [PyQt5 Official Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/en/latest/)
- [Pillow Handbook](https://pillow.readthedocs.io/en/stable/handbook/index.html)
- [Python Threading Documentation](https://docs.python.org/3/library/threading.html)

## AI Transparency
This app was created with the help of AI as assistance.  

## Thank you!  
A special thank you to https://ezgif.com/ for the GIF made converting my MP4. Thank you!  

---

**Happy PDF organizing!** 📚✨
