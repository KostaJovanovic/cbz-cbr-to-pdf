#!/bin/bash
# Script to download UnRAR binaries for local development

set -e

UNRAR_VERSION="6.2.12"

echo "Downloading UnRAR binaries..."

# Linux
mkdir -p binaries/linux
echo "Downloading for Linux..."
curl -L -o binaries/linux/unrar.tar.gz "https://www.rarlab.com/rar/unrar-linux-x64-${UNRAR_VERSION}.tar.gz" || echo "Warning: Failed to download Linux unrar"
if [ -f "binaries/linux/unrar.tar.gz" ]; then
    tar -xzf binaries/linux/unrar.tar.gz -C binaries/linux/ --strip-components=1 unrar
    rm binaries/linux/unrar.tar.gz
    chmod +x binaries/linux/unrar
    echo "✓ Linux unrar downloaded"
fi

# macOS
mkdir -p binaries/macos
echo "Downloading for macOS..."
curl -L -o binaries/macos/unrar.tar.gz "https://www.rarlab.com/rar/unrar-macos-${UNRAR_VERSION}.tar.gz" || echo "Warning: Failed to download macOS unrar"
if [ -f "binaries/macos/unrar.tar.gz" ]; then
    tar -xzf binaries/macos/unrar.tar.gz -C binaries/macos/ --strip-components=1 unrar
    rm binaries/macos/unrar.tar.gz
    chmod +x binaries/macos/unrar
    echo "✓ macOS unrar downloaded"
fi

# Windows (placeholder)
mkdir -p binaries/windows
echo "For Windows: Please download UnRAR.exe manually from https://www.rarlab.com/rar_add.htm"
echo "Place it in binaries/windows/UnRAR.exe"

echo ""
echo "Binary downloads complete!"
echo ""
echo "Directory structure:"
ls -lh binaries/*/
