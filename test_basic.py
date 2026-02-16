#!/usr/bin/env python3
"""Test script for comic_to_pdf functionality"""

import os
import sys
import tempfile

# Test imports
print("Testing imports...")
try:
    import zipfile
    print("✓ zipfile (built-in)")
except ImportError as e:
    print(f"✗ zipfile: {e}")

try:
    import rarfile
    print("✓ rarfile")
except ImportError as e:
    print(f"✗ rarfile: {e}")

try:
    import img2pdf
    print("✓ img2pdf")
except ImportError as e:
    print(f"✗ img2pdf: {e}")

try:
    import tkinter as tk
    print("✓ tkinter")
except ImportError as e:
    print(f"✗ tkinter: {e}")

# Test functions
print("\nTesting functions...")

# Test get_unrar_path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comic_to_pdf import get_unrar_path, setup_rarfile

unrar_path = get_unrar_path()
print(f"UnRAR path: {unrar_path}")
print(f"UnRAR exists: {os.path.exists(unrar_path)}")

# Test if we can find the test CBR file
test_cbr = "Watchmen - Issue 01.cbr"
if os.path.exists(test_cbr):
    print(f"\n✓ Test file found: {test_cbr}")
    print(f"  Size: {os.path.getsize(test_cbr) / 1024 / 1024:.1f} MB")
else:
    print(f"\n✗ Test file not found: {test_cbr}")

print("\n✓ All basic tests passed!")
