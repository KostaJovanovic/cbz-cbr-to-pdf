import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.font
import os
import platform
import threading
import sys
import shlex
import math
import random
import shutil
import subprocess

# Optional dependencies - will show nice error if missing
try:
    import img2pdf
    HAS_IMG2PDF = True
except ImportError:
    HAS_IMG2PDF = False

try:
    import rarfile
    HAS_RARFILE = True
except ImportError:
    HAS_RARFILE = False

# Drag and drop support
try:
    import tkinterdnd2 as tkdnd
    USE_TKINTERDND2 = True
except ImportError:
    try:
        import windnd
        USE_TKINTERDND2 = False
        windnd = None
    except ImportError:
        USE_TKINTERDND2 = False
        windnd = None


# ============================================================================
# CONFIGURATION & THEME
# ============================================================================

MIN_WIDTH = 700
MIN_HEIGHT = 500
DEFAULT_WIDTH = 900
DEFAULT_HEIGHT = 650

# Zed-inspired dark theme
THEME = {
    "bg": "#0d1117",           # GitHub dark dim
    "bg_secondary": "#161b22", # Slightly lighter
    "bg_tertiary": "#21262d",  # Borders
    "bg_hover": "#30363d",     # Hover state
    "text_primary": "#f0f6fc", # Primary text
    "text_secondary": "#8b949e",  # Dimmed text
    "text_muted": "#6e7681",   # Very dim
    "accent": "#58a6ff",       # Blue accent
    "accent_dim": "#1f6feb",   # Darker blue
    "success": "#3fb950",      # Green
    "error": "#f85149",        # Red
    "warning": "#d29922",      # Yellow
    "border": "#30363d",       # Border color
    "scrollbar": "#21262d",    # Scrollbar track
    "scrollbar_thumb": "#58a6ff",  # Scrollbar thumb
}

# Layout
PAD_SMALL = 4
PAD_MEDIUM = 8
PAD_LARGE = 16
PAD_XL = 24
SIDEBAR_WIDTH = 280


# ============================================================================
# UTILITIES
# ============================================================================

def get_unrar_path():
    """Get path to bundled unrar binary"""
    system = platform.system().lower()
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    if system == "windows":
        return os.path.join(base_path, "binaries", "windows", "UnRAR.exe")
    elif system == "darwin":
        return os.path.join(base_path, "binaries", "macos", "unrar")
    else:
        return os.path.join(base_path, "binaries", "linux", "unrar")


def setup_rarfile():
    """Configure rarfile to use bundled unrar"""
    if not HAS_RARFILE:
        return False
    unrar_path = get_unrar_path()
    if os.path.exists(unrar_path):
        rarfile.UNRAR_TOOL = unrar_path
        return True
    return False


def apply_dark_title_bar(root):
    """Apply dark title bar on Windows"""
    try:
        if platform.system() == "Windows":
            from ctypes import windll, c_int, byref
            hwnd = windll.user32.GetParent(root.winfo_id())
            windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(c_int(1)), 4)
    except Exception:
        pass


def open_file_or_folder(path):
    """Open file or folder with system default"""
    if not path or not os.path.exists(path):
        return
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.run(['open', path])
        else:
            subprocess.run(['xdg-open', path])
    except Exception:
        pass


# ============================================================================
# CONVERSION LOGIC
# ============================================================================

def extract_zip(zip_path, extract_to):
    """Extract ZIP archive"""
    import zipfile
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_to)
        return True
    except Exception as e:
        return False


def extract_rar(rar_path, extract_to):
    """Extract RAR archive"""
    if not HAS_RARFILE:
        return False
    try:
        setup_rarfile()
        with rarfile.RarFile(rar_path) as rf:
            rf.extractall(extract_to)
        return True
    except Exception as e:
        return False


def find_comic_files(paths):
    """Find all comic files in paths"""
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, names in os.walk(p):
                for name in names:
                    if name.lower().endswith((".cbr", ".cbz")):
                        files.append(os.path.join(root, name))
        elif p.lower().endswith((".cbr", ".cbz")):
            files.append(p)
    return sorted(files)


def convert_comic(comic_path, pdf_folder, callback=None):
    """Convert a single comic to PDF"""
    basename = os.path.splitext(os.path.basename(comic_path))[0]
    out_dir = os.path.join(os.path.dirname(comic_path), basename + "_temp")
    pdf_out = os.path.join(pdf_folder, basename + ".pdf")
    
    if os.path.exists(pdf_out):
        return True, pdf_out, "Already exists"
    
    if callback:
        callback(f"Extracting: {basename}")
    
    # Extract
    if comic_path.lower().endswith('.cbz'):
        success = extract_zip(comic_path, out_dir)
    elif comic_path.lower().endswith('.cbr'):
        success = extract_rar(comic_path, out_dir)
    else:
        return False, None, "Unsupported format"
    
    if not success:
        return False, None, "Extraction failed"
    
    # Find images
    exts = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".gif", ".webp")
    images = sorted([
        os.path.join(r, f)
        for r, _, fs in os.walk(out_dir)
        for f in fs if f.lower().endswith(exts)
    ])
    
    if not images:
        shutil.rmtree(out_dir, ignore_errors=True)
        return False, None, "No images found"
    
    if callback:
        callback(f"Converting {len(images)} pages")
    
    # Create PDF
    if not HAS_IMG2PDF:
        return False, None, "img2pdf not installed"
    
    try:
        with open(pdf_out, "wb") as f:
            f.write(img2pdf.convert(images))
    except Exception as e:
        shutil.rmtree(out_dir, ignore_errors=True)
        return False, None, str(e)
    
    # Cleanup
    shutil.rmtree(out_dir, ignore_errors=True)
    return True, pdf_out, "Success"


# ============================================================================
# UI COMPONENTS
# ============================================================================

class ModernButton:
    """Zed-style button"""
    def __init__(self, parent, text, command, primary=False, small=False):
        self.parent = parent
        self.text = text
        self.command = command
        self.primary = primary
        self.small = small
        self.enabled = True
        self.hover = False
        
        self.height = 28 if small else 34
        
        # Calculate width
        font = ("Segoe UI", 9 if small else 10)
        self.parent.update_idletasks()
        text_width = tkinter.font.Font(font=font).measure(text)
        self.width = max(80, text_width + 24)
        
        self.frame = tk.Frame(parent, bg=THEME["bg"])
        self.canvas = tk.Canvas(
            self.frame, width=self.width, height=self.height,
            bg=THEME["bg"], highlightthickness=0, cursor="hand2"
        )
        self.canvas.pack()
        
        self.canvas.bind("<Configure>", self._draw)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        
        self._draw()
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.frame.grid(**kwargs)
    
    def set_enabled(self, enabled):
        self.enabled = enabled
        self._draw()
    
    def _on_click(self, event):
        if self.enabled and self.command:
            self.command()
    
    def _on_enter(self, event):
        if self.enabled:
            self.hover = True
            self._draw()
    
    def _on_leave(self, event):
        self.hover = False
        self._draw()
    
    def _draw(self, event=None):
        c = self.canvas
        c.delete("all")
        w, h = self.width, self.height
        
        if not self.enabled:
            bg = THEME["bg_tertiary"]
            fg = THEME["text_muted"]
        elif self.primary:
            bg = THEME["accent"] if self.hover else THEME["accent_dim"]
            fg = "#ffffff"
        else:
            bg = THEME["bg_hover"] if self.hover else THEME["bg_secondary"]
            fg = THEME["text_primary"]
        
        # Draw rounded rect
        r = 4
        c.create_rectangle(0, 0, w, h, fill=bg, outline="", width=0)
        
        # Text
        font = ("Segoe UI", 9, "bold") if self.primary else ("Segoe UI", 9)
        c.create_text(w/2, h/2, text=self.text, fill=fg, font=font)


class FileSidebar:
    """Right sidebar for file list"""
    def __init__(self, parent, on_click):
        self.parent = parent
        self.on_click = on_click
        self.files = []
        self.row_height = 36
        self.hover_idx = -1
        
        self.frame = tk.Frame(parent, bg=THEME["bg_secondary"], width=SIDEBAR_WIDTH)
        self.frame.pack_propagate(False)
        self.frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Header
        header = tk.Frame(self.frame, bg=THEME["bg_secondary"], height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header, text="Files",
            font=("Segoe UI", 9, "bold"), fg=THEME["text_secondary"],
            bg=THEME["bg_secondary"], anchor="w", padx=PAD_MEDIUM
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Scrollable content
        self.canvas = tk.Canvas(
            self.frame, bg=THEME["bg_secondary"], 
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=(0, 1))
        
        self.canvas.bind("<Configure>", self._draw)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Button-1>", self._on_click)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(
            self.frame, orient=tk.VERTICAL,
            command=self.canvas.yview,
            bg=THEME["bg_tertiary"],
            troughcolor=THEME["bg_secondary"],
            borderwidth=0, highlightthickness=0,
            activebackground=THEME["accent"]
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(yscrollcommand=scrollbar.set)
        
        self._draw()
    
    def set_files(self, files):
        self.files = files
        self._update_scroll()
        self._draw()
    
    def update_file(self, path, status, pdf_path=None):
        for f in self.files:
            if f["path"] == path:
                f["status"] = status
                if pdf_path:
                    f["pdf_path"] = pdf_path
                break
        self._draw()
    
    def _update_scroll(self):
        h = len(self.files) * self.row_height
        self.canvas.config(scrollregion=(0, 0, SIDEBAR_WIDTH, h))
    
    def _draw(self, event=None):
        c = self.canvas
        c.delete("all")
        w = self.canvas.winfo_width()
        
        if w < 10:
            return
        
        for i, file_info in enumerate(self.files):
            y = i * self.row_height
            
            # Background
            bg = THEME["bg_hover"] if i == self.hover_idx else THEME["bg_secondary"]
            c.create_rectangle(0, y, w, y + self.row_height - 1,
                             fill=bg, outline="", tags=f"row_{i}")
            
            name = file_info["display_name"]
            status = file_info["status"]
            
            # Icon
            if status == "pending":
                icon = "○"
                color = THEME["text_muted"]
            elif status == "converting":
                icon = "⟳"
                color = THEME["accent"]
            elif status == "done":
                icon = "●"
                color = THEME["success"]
            else:  # failed
                icon = "●"
                color = THEME["error"]
            
            c.create_text(
                PAD_MEDIUM, y + self.row_height/2,
                text=icon, fill=color, font=("Segoe UI", 12),
                anchor="w"
            )
            
            # Filename (truncated)
            max_width = w - 50
            text_width = tkinter.font.Font(font=("Segoe UI", 9)).measure(name)
            if text_width > max_width:
                name = name[:int(max_width / 7)] + "..."
            
            c.create_text(
                PAD_MEDIUM + 20, y + self.row_height/2,
                text=name, fill=THEME["text_primary"],
                font=("Segoe UI", 9), anchor="w"
            )
    
    def _on_motion(self, event):
        idx = int(event.y / self.row_height)
        if 0 <= idx < len(self.files):
            if self.hover_idx != idx:
                self.hover_idx = idx
                self._draw()
        else:
            if self.hover_idx != -1:
                self.hover_idx = -1
                self._draw()
    
    def _on_click(self, event):
        idx = int(event.y / self.row_height)
        if 0 <= idx < len(self.files):
            f = self.files[idx]
            if f["status"] == "done" and f.get("pdf_path"):
                if self.on_click:
                    self.on_click(f["pdf_path"])


class StatusBar:
    """Status bar at bottom"""
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg=THEME["bg_tertiary"], height=28)
        self.frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.frame.pack_propagate(False)
        
        self.label = tk.Label(
            self.frame, text="Ready",
            font=("Segoe UI", 8), fg=THEME["text_secondary"],
            bg=THEME["bg_tertiary"], anchor="w", padx=PAD_MEDIUM
        )
        self.label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def set_text(self, text):
        self.label.config(text=text)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Comic to PDF Converter")
        self.root.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.configure(bg=THEME["bg"])
        
        # Center window
        self.root.update_idletasks()
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = (ws - DEFAULT_WIDTH) // 2
        y = (hs - DEFAULT_HEIGHT) // 2
        self.root.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}+{x}+{y}")
        
        self.converting = False
        self.output_folder = None
        self.conversion_files = []
        
        apply_dark_title_bar(self.root)
        
        # Build UI
        self._build_ui()
        self._setup_drag_drop()
    
    def _build_ui(self):
        # Main container
        main = tk.Frame(self.root, bg=THEME["bg"])
        main.pack(fill=tk.BOTH, expand=True)
        
        # Left content area
        self.content = tk.Frame(main, bg=THEME["bg"])
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Header
        self._build_header()
        
        # Drop zone
        self._build_drop_zone()
        
        # Actions
        self._build_actions()
        
        # Progress
        self._build_progress()
        
        # Status bar
        self.status = StatusBar(self.content)
        
        # Right sidebar
        self.sidebar = FileSidebar(self.content, self.on_file_click)
    
    def _build_header(self):
        header = tk.Frame(self.content, bg=THEME["bg"], height=50)
        header.pack(fill=tk.X, pady=(PAD_XL, PAD_LARGE))
        header.pack_propagate(False)
        
        tk.Label(
            header, text="Comic to PDF",
            font=("Segoe UI", 18, "bold"), fg=THEME["text_primary"],
            bg=THEME["bg"], anchor="w"
        ).pack(side=tk.LEFT, fill=tk.X)
    
    def _build_drop_zone(self):
        self.drop_frame = tk.Frame(self.content, bg=THEME["bg"])
        self.drop_frame.pack(fill=tk.BOTH, expand=True, padx=PAD_XL)
        
        self.drop_zone = tk.Canvas(
            self.drop_frame, bg=THEME["bg_secondary"],
            highlightthickness=1, highlightbackground=THEME["border"],
            cursor="hand2"
        )
        self.drop_zone.pack(fill=tk.BOTH, expand=True)
        
        self.drop_zone.bind("<Configure>", self._draw_drop_zone)
        self.drop_zone.bind("<Button-1>", lambda e: self.browse())
        self.drop_zone.bind("<Enter>", lambda e: self._draw_drop_zone(hover=True))
        self.drop_zone.bind("<Leave>", lambda e: self._draw_drop_zone(hover=False))
        
        self._drop_hover = False
    
    def _build_actions(self):
        actions = tk.Frame(self.content, bg=THEME["bg"])
        actions.pack(fill=tk.X, padx=PAD_XL, pady=PAD_LARGE)
        
        self.browse_btn = ModernButton(actions, "Browse Files", self.browse, primary=True)
        self.browse_btn.pack(side=tk.LEFT)
        
        self.clear_btn = ModernButton(actions, "Clear", self.clear, primary=False, small=True)
        self.clear_btn.pack(side=tk.LEFT, padx=(PAD_MEDIUM, 0))
        self.clear_btn.set_enabled(False)
        
        self.open_btn = ModernButton(actions, "Open Folder", self.open_folder, primary=False, small=True)
        self.open_btn.pack(side=tk.RIGHT)
        self.open_btn.set_enabled(False)
    
    def _build_progress(self):
        prog = tk.Frame(self.content, bg=THEME["bg"])
        prog.pack(fill=tk.X, padx=PAD_XL, pady=(0, PAD_LARGE))
        
        self.progress_canvas = tk.Canvas(
            prog, height=4, bg=THEME["bg_tertiary"],
            highlightthickness=0
        )
        self.progress_canvas.pack(fill=tk.X)
        
        self.progress = 0
        self.total = 1
        self._draw_progress()
    
    def _draw_drop_zone(self, event=None, hover=False):
        c = self.drop_zone
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        
        # Draw centered content
        cx, cy = w/2, h/2
        
        icon = "↓" if hover else "↓"
        color = THEME["accent"] if hover else THEME["text_secondary"]
        
        c.create_text(
            cx, cy - 20,
            text=icon, fill=color, font=("Segoe UI", 32)
        )
        c.create_text(
            cx, cy + 10,
            text="Drop CBR/CBZ files here",
            fill=THEME["text_primary"], font=("Segoe UI", 11, "bold")
        )
        c.create_text(
            cx, cy + 30,
            text="or click to browse",
            fill=THEME["text_secondary"], font=("Segoe UI", 9)
        )
    
    def _draw_progress(self):
        c = self.progress_canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        
        # Background
        c.create_rectangle(0, 0, w, h, fill=THEME["bg_tertiary"], outline="")
        
        # Fill
        if self.total > 0:
            fill_w = int(w * self.progress / self.total)
            c.create_rectangle(0, 0, fill_w, h, fill=THEME["accent"], outline="")
    
    def _setup_drag_drop(self):
        if USE_TKINTERDND2:
            try:
                tkdnd.TkinterDnD().bindroot(self.root)
                self.root.drop_target_register(tkdnd.DND_FILES)
                self.root.dnd_bind('<<Drop>>', self._on_tkdnd_drop)
                self.status.set_text("Drag & drop enabled")
            except Exception as e:
                self.status.set_text("Drag & drop unavailable")
        elif windnd:
            windnd.hook_dropfiles(self.root, func=self._on_windnd_drop)
            self.status.set_text("Drag & drop enabled")
        else:
            self.status.set_text("Install tkinterdnd2 for drag & drop")
    
    def _on_tkdnd_drop(self, event):
        if self.converting:
            return
        files_str = event.data
        if files_str.startswith('{') and files_str.endswith('}'):
            files_str = files_str[1:-1]
        try:
            paths = shlex.split(files_str)
        except:
            paths = files_str.split()
        self.start_conversion(list(paths))
    
    def _on_windnd_drop(self, files):
        if self.converting:
            return
        paths = [f.decode("utf-8") if isinstance(f, bytes) else f for f in files]
        self.start_conversion(paths)
    
    def browse(self):
        if self.converting:
            return
        paths = filedialog.askopenfilenames(
            title="Select CBR/CBZ files",
            filetypes=[("Comic archives", "*.cbr *.cbz"), ("All files", "*.*")]
        )
        if paths:
            self.start_conversion(list(paths))
    
    def clear(self):
        if self.converting:
            return
        self.conversion_files = []
        self.sidebar.set_files([])
        self.clear_btn.set_enabled(False)
        self.open_btn.set_enabled(False)
        self.progress = 0
        self.total = 1
        self._draw_progress()
        self.status.set_text("Cleared")
    
    def open_folder(self):
        if self.output_folder:
            open_file_or_folder(self.output_folder)
    
    def on_file_click(self, pdf_path):
        open_file_or_folder(pdf_path)
    
    def start_conversion(self, paths):
        comics = find_comic_files(paths)
        if not comics:
            self.status.set_text("No comic files found")
            return
        
        self.conversion_files = [{
            "path": c,
            "status": "pending",
            "pdf_path": None,
            "display_name": os.path.basename(c)
        } for c in comics]
        
        self.sidebar.set_files(self.conversion_files)
        self.clear_btn.set_enabled(True)
        self.converting = True
        
        # Set output folder
        first_dir = os.path.dirname(comics[0])
        self.output_folder = os.path.join(first_dir, "Converted PDFs")
        os.makedirs(self.output_folder, exist_ok=True)
        
        self.status.set_text(f"Converting {len(comics)} file(s)...")
        
        threading.Thread(target=self._run_conversion, args=(comics,), daemon=True).start()
    
    def _run_conversion(self, comics):
        total = len(comics)
        success = 0
        failed = 0
        
        for i, comic in enumerate(comics):
            self.root.after(0, lambda p=comic: self.sidebar.update_file(p, "converting"))
            
            result, pdf_path, msg = convert_comic(comic, self.output_folder)
            
            if result:
                success += 1
                self.root.after(0, lambda p=comic, pdf=pdf_path: 
                               self.sidebar.update_file(p, "done", pdf))
            else:
                failed += 1
                self.root.after(0, lambda p=comic: 
                               self.sidebar.update_file(p, "failed"))
            
            self.root.after(0, lambda: setattr(self, 'progress', i + 1))
            self.root.after(0, self._draw_progress)
        
        self.converting = False
        self.root.after(0, self._on_complete, success, failed)
    
    def _on_complete(self, success, failed):
        if failed == 0:
            self.status.set_text(f"✓ Complete: {success} converted")
        else:
            self.status.set_text(f"✗ Done: {success} succeeded, {failed} failed")
        self.open_btn.set_enabled(True)
    
    def run(self):
        self.root.mainloop()


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Check dependencies
    missing = []
    if not HAS_IMG2PDF:
        missing.append("img2pdf")
    if not HAS_RARFILE:
        missing.append("rarfile")
    
    if missing:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Missing Dependencies",
            f"Please install:\n" + "\n".join(f"  - {m}" for m in missing) +
            "\n\nRun: pip install -r requirements.txt"
        )
        sys.exit(1)
    
    app = App()
    app.run()
