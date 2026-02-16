#!/bin/bash
# Script to download UnRAR binaries for local development

set -e

echo "Downloading RAR packages and extracting unrar..."

# Linux
mkdir -p binaries/linux
echo "Downloading for Linux..."
if [ ! -f "binaries/linux/unrar" ]; then
    curl -sL https://www.rarlab.com/rar/rarlinux-x64-720.tar.gz | tar -xz
    cp rar/unrar binaries/linux/
    chmod +x binaries/linux/unrar
    rm -rf rar
    echo "✓ Linux unrar downloaded"
else
    echo "✓ Linux unrar already exists"
fi

# macOS
mkdir -p binaries/macos
echo "Downloading for macOS..."
if [ ! -f "binaries/macos/unrar" ]; then
    curl -sL https://www.rarlab.com/rar/rarmacos-x64-720.tar.gz | tar -xz
    cp rar/unrar binaries/macos/
    chmod +x binaries/macos/unrar
    rm -rf rar
    echo "✓ macOS unrar downloaded"
else
    echo "✓ macOS unrar already exists"
fi

# Windows (placeholder - users need to download manually)
mkdir -p binaries/windows
echo "For Windows: Download UnRAR.exe from https://www.rarlab.com/rar_add.htm"
echo "Or extract from winrar-x64-720.exe installation"
echo "Place it in binaries/windows/UnRAR.exe"

echo ""
echo "Binary downloads complete!"
echo ""
echo "Directory structure:"
ls -lh binaries/*/ 2>/dev/null || echo "No binaries found"
