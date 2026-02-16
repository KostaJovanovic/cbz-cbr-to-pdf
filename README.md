# Comics to PDF Converter

A cross-platform GUI tool that batch converts CBR and CBZ comic book archives to PDF files.

![Python](https://img.shields.io/badge/Python-3.10+-blue) 
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- ✅ Drag and drop CBR/CBZ files or entire folders
- ✅ Batch converts all comics found in dropped folders
- ✅ Skips files that already have a matching PDF
- ✅ Outputs all PDFs to a `Converted PDFs` folder
- ✅ **Cross-platform** (Windows, macOS, Linux)
- ✅ **Self-contained** - no external tools required!
- ✅ Beautiful dark UI with random color themes

## Download

Get the latest release for your platform:

- **[Windows](https://github.com/omznc/cbz-cbr-to-pdf/releases/latest)** - `comic-to-pdf-windows.exe`
- **[macOS](https://github.com/omznc/cbz-cbr-to-pdf/releases/latest)** - `comic-to-pdf-macos`
- **[Linux](https://github.com/omznc/cbz-cbr-to-pdf/releases/latest)** - `comic-to-pdf-linux`

Just download and run - no installation required!

## How to Run (From Source)

### Requirements

- Python 3.10 or higher
- Tkinter (usually included with Python)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run

```bash
python comic_to_pdf.py
```

## Development

### Building Executables

You can build executables for your platform using PyInstaller:

```bash
# Install PyInstaller
pip install pyinstaller

# Download unrar binary for your platform

# Linux:
mkdir -p binaries/linux
wget https://www.rarlab.com/rar/unrar-linux-x64-6.2.12.tar.gz
tar -xzf unrar-linux-x64-6.2.12.tar.gz
cp unrar binaries/linux/
chmod +x binaries/linux/unrar

# macOS:
mkdir -p binaries/macos
wget https://www.rarlab.com/rar/unrar-macos-6.2.12.tar.gz
tar -xzf unrar-macos-6.2.12.tar.gz
cp unrar binaries/macos
chmod +x binaries/macos/unrar

# Windows:
mkdir binaries\windows
# Download UnRAR.exe from https://www.rarlab.com/rar_add.htm
# Place it in binaries\windows\UnRAR.exe

# Build executable
pyinstaller comic_to_pdf.spec
```

The executable will be in the `dist/` directory.

## How It Works

1. **CBZ files**: Extracted using Python's built-in `zipfile` module
2. **CBR files**: Extracted using `rarfile` library with bundled `unrar` binary
3. Collects all image files (JPG, PNG, BMP, TIFF, GIF, WebP) sorted by name
4. Combines them into a multi-page PDF using `img2pdf`
5. Cleans up temporary extracted files

## What Changed

This is a cross-platform fork of [KostaJovanovic/cbz-cbr-to-pdf](https://github.com/KostaJovanovic/cbz-cbr-to-pdf) with the following improvements:

- **Removed 7-Zip dependency** - No longer requires 7-Zip to be installed
- **Cross-platform support** - Works on Windows, macOS, and Linux
- **Bundled unrar binary** - Includes unrar for RAR extraction
- **Cross-platform drag-and-drop** - Uses tkinterdnd2 for drag-and-drop on all platforms
- **Self-contained executables** - No external dependencies needed

## License

MIT License - see LICENSE file for details

## Credits

- Original project by [KostaJovanovic](https://github.com/KostaJovanovic/cbz-cbr-to-pdf)
- Cross-platform improvements by [omznc](https://github.com/omznc)
