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

- **[Windows](../../releases/latest)** - `comic-to-pdf-windows.exe`
- **[macOS](../../releases/latest)** - `comic-to-pdf-macos`
- **[Linux](../../releases/latest)** - `comic-to-pdf-linux`

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

# Download unrar binaries
./download_binaries.sh

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

## License

MIT License - see LICENSE file for details
