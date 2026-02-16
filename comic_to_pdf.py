import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import tkinter.font
import os
import platform
import threading
import img2pdf
import math
import random
import shutil
import subprocess
import sys
import shlex

# Cross-platform drag-and-drop
try:
    import tkinterdnd2 as tkdnd
    USE_TKINTERDND2 = True
except ImportError:
    try:
        import windnd
        USE_TKINTERDND2 = False
    except ImportError:
        USE_TKINTERDND2 = False
        windnd = None


def get_unrar_path():
    """Get path to bundled unrar binary for current platform"""
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
    import rarfile
    unrar_path = get_unrar_path()
    if os.path.exists(unrar_path):
        rarfile.UNRAR_TOOL = unrar_path
        return True
    return False


def apply_dark_title_bar(root):
    """Apply dark title bar on Windows 10+"""
    try:
        if platform.system() == "Windows":
            from ctypes import windll, c_int, byref
            hwnd = windll.user32.GetParent(root.winfo_id())
            windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(c_int(1)), 4)
    except Exception:
        pass


def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def _blend(hex1, hex2, t=0.5):
    r1, g1, b1 = _hex_to_rgb(hex1)
    r2, g2, b2 = _hex_to_rgb(hex2)
    return _rgb_to_hex(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)


def _darken(hex_color, amount=0.3):
    r, g, b = _hex_to_rgb(hex_color)
    return _rgb_to_hex(r * (1 - amount), g * (1 - amount), b * (1 - amount))


def _lighten(hex_color, amount=0.3):
    r, g, b = _hex_to_rgb(hex_color)
    return _rgb_to_hex(r + (255 - r) * amount, g + (255 - g) * amount, b + (255 - b) * amount)


def _luminance(hex_color):
    r, g, b = _hex_to_rgb(hex_color)
    return 0.299 * r + 0.587 * g + 0.114 * b


def _build_theme(c1, c2, c3, c4):
    """Build a full theme from 4 palette colors"""
    colors = sorted([c1, c2, c3, c4], key=_luminance)
    darkest, dark, mid, bright = colors

    lum = _luminance(darkest)
    if lum > 60:
        bg = _darken(darkest, 0.85)
    else:
        bg = _darken(darkest, 0.35)

    light_text = _luminance(bg) < 100

    accent = mid
    while light_text and _luminance(accent) < 120:
        accent = _lighten(accent, 0.2)
    green = bright
    while light_text and _luminance(green) < 140:
        green = _lighten(green, 0.2)

    return {
        "BG": bg,
        "BG_MID": _lighten(bg, 0.08),
        "BG_LIGHT": _lighten(bg, 0.14),
        "CARD": _lighten(bg, 0.12) if light_text else _darken(bg, 0.15),
        "CARD_HOVER": _lighten(bg, 0.18),
        "CARD_BORDER": _lighten(bg, 0.22),
        "ACCENT": accent,
        "ACCENT_HOVER": _lighten(accent, 0.2),
        "ACCENT_DIM": _darken(accent, 0.25),
        "BLUE": dark if not light_text else _lighten(dark, 0.15),
        "BLUE_LIGHT": _lighten(dark, 0.25),
        "PURPLE": _blend(darkest, dark, 0.5),
        "PURPLE_LIGHT": _lighten(_blend(darkest, dark, 0.5), 0.25),
        "GREEN": green,
        "GREEN_DIM": _darken(green, 0.2),
        "TEXT": "#f0f0f0" if light_text else "#1a1a1a",
        "TEXT_DIM": _lighten(bg, 0.35) if light_text else _darken(bg, 0.4),
        "TEXT_MID": _lighten(bg, 0.50) if light_text else _darken(bg, 0.55),
        "SUCCESS": green,
        "ERROR": "#ff8a80" if light_text else "#c62828",
        "LOG_BG": _darken(bg, 0.15),
    }


PALETTES = [
    ("a2faa3", "92c9b1", "4f759b", "5d5179"),
    ("8ab0ab", "3e505b", "26413c", "1a1d1a"),
    ("d8dbe2", "a9bcd0", "58a4b0", "373f51"),
    ("d7d9b1", "84acce", "827191", "7d1d3f"),
    ("14080e", "49475b", "799496", "acc196"),
    ("ffffff", "ffe8d1", "568ea3", "68c3d4"),
]

_chosen = random.choice(PALETTES)
_theme = _build_theme(*[f"#{c}" for c in _chosen])

BG = _theme["BG"]
BG_MID = _theme["BG_MID"]
BG_LIGHT = _theme["BG_LIGHT"]
CARD = _theme["CARD"]
CARD_HOVER = _theme["CARD_HOVER"]
CARD_BORDER = _theme["CARD_BORDER"]
ACCENT = _theme["ACCENT"]
ACCENT_HOVER = _theme["ACCENT_HOVER"]
ACCENT_DIM = _theme["ACCENT_DIM"]
BLUE = _theme["BLUE"]
BLUE_LIGHT = _theme["BLUE_LIGHT"]
PURPLE = _theme["PURPLE"]
PURPLE_LIGHT = _theme["PURPLE_LIGHT"]
GREEN = _theme["GREEN"]
GREEN_DIM = _theme["GREEN_DIM"]
TEXT = _theme["TEXT"]
TEXT_DIM = _theme["TEXT_DIM"]
TEXT_MID = _theme["TEXT_MID"]
SUCCESS = _theme["SUCCESS"]
ERROR = _theme["ERROR"]
LOG_BG = _theme["LOG_BG"]

# Layout constants
PAD_SMALL = 6
PAD_MEDIUM = 12
PAD_LARGE = 20
PAD_XL = 28

STATUS_PENDING = "pending"
STATUS_CONVERTING = "converting"
STATUS_DONE = "done"
STATUS_FAILED = "failed"


def extract_zip(zip_path, extract_to):
    """Extract ZIP archive"""
    import zipfile
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_to)
        return True
    except Exception:
        return False


def extract_rar(rar_path, extract_to):
    """Extract RAR archive"""
    import rarfile
    try:
        setup_rarfile()
        with rarfile.RarFile(rar_path) as rf:
            rf.extractall(extract_to)
        return True
    except Exception:
        return False


def find_comic_files(paths):
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


def convert_one(comic_path, pdf_folder, log_func):
    basename = os.path.splitext(os.path.basename(comic_path))[0]
    out_dir = os.path.join(os.path.dirname(comic_path), basename + "_temp")
    pdf_out = os.path.join(pdf_folder, basename + ".pdf")

    if os.path.exists(pdf_out):
        log_func(f"  Skipped (exists): {basename}.pdf", "dim")
        return True, pdf_out

    log_func(f"  Extracting: {os.path.basename(comic_path)}", "normal")
    
    if comic_path.lower().endswith('.cbz'):
        success = extract_zip(comic_path, out_dir)
    elif comic_path.lower().endswith('.cbr'):
        success = extract_rar(comic_path, out_dir)
    else:
        log_func(f"  ERROR: Unsupported format", "error")
        return False, None
    
    if not success:
        log_func(f"  ERROR: Failed to extract archive", "error")
        return False, None

    exts = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".gif", ".webp")
    images = sorted([
        os.path.join(r, f)
        for r, _, fs in os.walk(out_dir)
        for f in fs if f.lower().endswith(exts)
    ])

    if not images:
        log_func(f"  ERROR: No images found in archive", "error")
        _cleanup(out_dir)
        return False, None

    log_func(f"  Converting {len(images)} pages...", "normal")
    try:
        with open(pdf_out, "wb") as f:
            f.write(img2pdf.convert(images))
    except Exception as e:
        log_func(f"  ERROR creating PDF: {e}", "error")
        if os.path.exists(pdf_out):
            os.remove(pdf_out)
        _cleanup(out_dir)
        return False, None

    _cleanup(out_dir)
    log_func(f"  Done: {basename}.pdf", "success")
    return True, pdf_out


def _cleanup(out_dir):
    try:
        shutil.rmtree(out_dir, ignore_errors=True)
    except Exception:
        pass


def open_file_or_folder(path):
    """Open file or folder with system default application"""
    if not path or not os.path.exists(path):
        return
    
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.run(['open', path])
        else:
            subprocess.run(['xdg-open', path])
    except Exception:
        pass


class Button:
    """Modern button component with proper padding"""
    def __init__(self, parent, text, command, primary=True, enabled=True):
        self.parent = parent
        self.text = text
        self.command = command
        self.primary = primary
        self.enabled = enabled
        self.hover = False
        
        # Calculate size based on text
        font_spec = ("Segoe UI Semibold", 10)
        self.parent.update_idletasks()
        text_width = tkinter.font.Font(font=font_spec).measure(text)
        self.width = max(120, text_width + 32)
        self.height = 36
        
        self.canvas = tk.Canvas(
            parent, width=self.width, height=self.height,
            bg=BG, highlightthickness=0, cursor="hand2"
        )
        self.canvas.bind("<Configure>", self._draw)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        self._draw()
    
    def pack(self, **kwargs):
        self.canvas.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.canvas.grid(**kwargs)
    
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
            fill = CARD
            text_color = TEXT_DIM
        elif self.primary:
            fill = ACCENT_HOVER if self.hover else ACCENT
            text_color = BG
        else:
            fill = CARD_HOVER if self.hover else CARD
            text_color = TEXT if self.hover else TEXT_MID
        
        # Draw rounded rect
        points = []
        r = 8
        for (cx, cy, sa) in [
            (w - r, r, -90), (w - r, h - r, 0),
            (r, h - r, 90), (r, r, 180)
        ]:
            for i in range(13):
                a = math.radians(sa + i * 90 / 12)
                points.extend([cx + r * math.cos(a), cy + r * math.sin(a)])
        c.create_polygon(points, smooth=True, fill=fill, outline="")
        
        c.create_text(w // 2, h // 2, text=self.text,
                      font=("Segoe UI Semibold", 10), fill=text_color)


class FileList:
    """Scrollable file list with status and click-to-open"""
    def __init__(self, parent, on_file_click):
        self.parent = parent
        self.on_file_click = on_file_click
        self.files = []  # [{path, status, pdf_path, display_name}, ...]
        self.row_height = 40
        self.visible_rows = 6
        self.scroll_offset = 0
        self.hover_row = -1
        
        height = self.row_height * self.visible_rows + 4
        self.canvas = tk.Canvas(
            parent, height=height, bg=BG, highlightthickness=0
        )
        self.canvas.bind("<Configure>", self._draw)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<MouseWheel>", self._on_scroll)  # Windows
        self.canvas.bind("<Button-4>", self._on_scroll)    # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_scroll)    # Linux scroll down
        
        self._draw()
    
    def pack(self, **kwargs):
        self.canvas.pack(**kwargs)
    
    def set_files(self, files):
        """Update file list"""
        self.files = files
        self.scroll_offset = 0
        self._draw()
    
    def update_file_status(self, path, status, pdf_path=None):
        """Update status of a specific file"""
        for f in self.files:
            if f["path"] == path:
                f["status"] = status
                if pdf_path:
                    f["pdf_path"] = pdf_path
                break
        self._draw()
    
    def _get_visible_rows(self):
        total = len(self.files)
        start = self.scroll_offset
        end = min(start + self.visible_rows, total)
        return self.files[start:end], start
    
    def _draw(self, event=None):
        c = self.canvas
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        
        if w < 10:
            return
        
        visible, start = self._get_visible_rows()
        
        for i, file_info in enumerate(visible):
            y = i * self.row_height
            row_idx = start + i
            
            # Background
            if row_idx == self.hover_row:
                bg = BG_LIGHT
            else:
                bg = BG
            
            # Row background
            c.create_rectangle(0, y, w, y + self.row_height - 1,
                             fill=bg, outline="", tags=f"row_{row_idx}")
            
            if not visible:
                continue
            
            name = file_info["display_name"]
            status = file_info["status"]
            pdf_path = file_info.get("pdf_path")
            
            # Status icon and color
            if status == STATUS_PENDING:
                icon = "⏳"
                color = TEXT_DIM
                status_text = "Waiting"
            elif status == STATUS_CONVERTING:
                icon = "⟳"
                color = ACCENT
                status_text = "Converting..."
            elif status == STATUS_DONE:
                icon = "✓"
                color = SUCCESS
                status_text = "Done"
            else:  # failed
                icon = "✗"
                color = ERROR
                status_text = "Failed"
            
            # Icon
            c.create_text(PAD_MEDIUM, y + self.row_height // 2,
                         text=icon, font=("Segoe UI", 14),
                         fill=color, anchor="w")
            
            # Filename
            name_x = PAD_MEDIUM + 24
            c.create_text(name_x, y + self.row_height // 2 - 6,
                         text=name, font=("Segoe UI", 9),
                         fill=TEXT, anchor="w")
            
            # Status text
            c.create_text(name_x, y + self.row_height // 2 + 8,
                         text=status_text, font=("Segoe UI", 8),
                         fill=color, anchor="w")
            
            # Click indicator for completed files
            if status == STATUS_DONE and pdf_path:
                c.create_text(w - PAD_MEDIUM, y + self.row_height // 2,
                             text="Open →", font=("Segoe UI", 8),
                             fill=ACCENT, anchor="e")
    
    def _on_motion(self, event):
        w = self.canvas.winfo_width()
        row = int(event.y / self.row_height) + self.scroll_offset
        
        if 0 <= row < len(self.files):
            if self.hover_row != row:
                self.hover_row = row
                self._draw()
        else:
            if self.hover_row != -1:
                self.hover_row = -1
                self._draw()
    
    def _on_click(self, event):
        row = int(event.y / self.row_height) + self.scroll_offset
        
        if 0 <= row < len(self.files):
            file_info = self.files[row]
            if file_info["status"] == STATUS_DONE and file_info.get("pdf_path"):
                if self.on_file_click:
                    self.on_file_click(file_info["pdf_path"])
    
    def _on_scroll(self, event):
        if event.num == 4 or event.delta > 0:
            self.scroll_offset = max(0, self.scroll_offset - 1)
        elif event.num == 5 or event.delta < 0:
            max_scroll = max(0, len(self.files) - self.visible_rows)
            self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
        self._draw()


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Comic to PDF")
        self.root.geometry("640x700")
        self.root.minsize(500, 550)
        self.root.configure(bg=BG)
        self.converting = False
        self.output_folder = None
        self.conversion_files = []

        apply_dark_title_bar(self.root)

        # Main container
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill=tk.BOTH, expand=True, padx=PAD_XL, pady=(PAD_LARGE, PAD_XL))

        # Header
        self._create_header(main)
        
        # Drop zone
        self._create_drop_zone(main)
        
        # Action buttons
        self._create_action_buttons(main)
        
        # File list
        self._create_file_list(main)
        
        # Progress section
        self._create_progress(main)
        
        # Stats and open folder
        self._create_footer(main)

        # Hook drag and drop
        self._hook_drag_drop()

    def _create_header(self, parent):
        header = tk.Frame(parent, bg=BG)
        header.pack(fill=tk.X, pady=(0, PAD_LARGE))

        tk.Label(
            header, text="Comic to PDF",
            font=("Segoe UI", 20, "bold"), fg=TEXT, bg=BG
        ).pack(side=tk.LEFT)

        # Format badges
        badge1 = tk.Label(
            header, text=" CBR ",
            font=("Segoe UI", 8, "bold"), fg=PURPLE, bg=CARD,
            padx=8, pady=3
        )
        badge1.pack(side=tk.LEFT, padx=(PAD_MEDIUM, 0))
        
        badge2 = tk.Label(
            header, text=" CBZ ",
            font=("Segoe UI", 8, "bold"), fg=BLUE, bg=CARD,
            padx=8, pady=3
        )
        badge2.pack(side=tk.LEFT, padx=(PAD_SMALL, 0))

    def _create_drop_zone(self, parent):
        self.drop_zone = tk.Canvas(
            parent, height=120, bg=BG_MID, highlightthickness=0, cursor="hand2"
        )
        self.drop_zone.pack(fill=tk.X)
        self.drop_zone.bind("<Configure>", self._draw_drop_zone)
        self.drop_zone.bind("<Button-1>", lambda e: self.browse())
        self._drop_hover = False
        self.drop_zone.bind("<Enter>", self._on_drop_enter)
        self.drop_zone.bind("<Leave>", self._on_drop_leave)

    def _create_action_buttons(self, parent):
        btn_frame = tk.Frame(parent, bg=BG)
        btn_frame.pack(fill=tk.X, pady=(PAD_MEDIUM, 0))

        self.browse_btn = Button(btn_frame, "Browse Files", self.browse, primary=True)
        self.browse_btn.pack(side=tk.LEFT)

        self.clear_btn = Button(btn_frame, "Clear", self.clear_queue, primary=False)
        self.clear_btn.pack(side=tk.LEFT, padx=(PAD_MEDIUM, 0))
        self.clear_btn.set_enabled(False)

    def _create_file_list(self, parent):
        self.file_list = FileList(parent, self.on_file_click)
        self.file_list.pack(fill=tk.X, pady=(PAD_LARGE, 0))

    def _create_progress(self, parent):
        prog_frame = tk.Frame(parent, bg=BG)
        prog_frame.pack(fill=tk.X, pady=(PAD_LARGE, 0))

        self.progress_label = tk.Label(
            prog_frame, text="Drop files to start",
            font=("Segoe UI", 9), fg=TEXT_DIM, bg=BG, anchor="w"
        )
        self.progress_label.pack(fill=tk.X)

        self.prog_canvas = tk.Canvas(
            prog_frame, height=6, bg=CARD, highlightthickness=0
        )
        self.prog_canvas.pack(fill=tk.X, pady=(PAD_SMALL, 0))
        self.prog_canvas.bind("<Configure>", self._draw_progress)
        self.progress_value = 0
        self.progress_max = 1

    def _create_footer(self, parent):
        footer = tk.Frame(parent, bg=BG)
        footer.pack(fill=tk.X, pady=(PAD_MEDIUM, 0))

        self.stat_success = tk.Label(
            footer, text="", font=("Segoe UI", 9),
            fg=SUCCESS, bg=BG
        )
        self.stat_success.pack(side=tk.LEFT)

        self.stat_failed = tk.Label(
            footer, text="", font=("Segoe UI", 9),
            fg=ERROR, bg=BG
        )
        self.stat_failed.pack(side=tk.LEFT, padx=(PAD_MEDIUM, 0))

        self.open_folder_btn = Button(
            footer, "Open Output Folder",
            self.open_output_folder, primary=False
        )
        self.open_folder_btn.pack(side=tk.RIGHT)
        self.open_folder_btn.set_enabled(False)

    def _draw_drop_zone(self, event=None):
        c = self.drop_zone
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        pad = 2

        fill = BG_LIGHT if self._drop_hover else BG_MID
        self._draw_rounded_rect(c, pad, pad, w - pad, h - pad, 12,
                                fill=fill, outline=CARD_BORDER, width=1)

        inset = 8
        dash_color = ACCENT if self._drop_hover else PURPLE
        self._draw_rounded_rect(
            c, inset, inset, w - inset, h - inset, 8,
            fill="", outline=dash_color, width=1.5, dash=(4, 3)
        )

        cx = w // 2
        cy = h // 2

        icon_color = GREEN if self._drop_hover else ACCENT
        c.create_text(cx, cy - 8, text="📁",
                      font=("Segoe UI", 32), fill=icon_color)

        label_color = TEXT if self._drop_hover else TEXT_MID
        c.create_text(cx, cy + 18, text="Drop CBR/CBZ files here or click to browse",
                      font=("Segoe UI", 10), fill=label_color)

    def _on_drop_enter(self, e):
        self._drop_hover = True
        self._draw_drop_zone()

    def _on_drop_leave(self, e):
        self._drop_hover = False
        self._draw_drop_zone()

    def _draw_rounded_rect(self, canvas, x1, y1, x2, y2, r, **kw):
        points = []
        for (cx, cy, sa) in [
            (x2 - r, y1 + r, -90), (x2 - r, y2 - r, 0),
            (x1 + r, y2 - r, 90), (x1 + r, y1 + r, 180)
        ]:
            for i in range(13):
                a = math.radians(sa + i * 90 / 12)
                points.extend([cx + r * math.cos(a), cy + r * math.sin(a)])
        return canvas.create_polygon(points, smooth=True, **kw)

    def _draw_progress(self, event=None):
        c = self.prog_canvas
        c.delete("all")
        w, h = c.winfo_width()

        self._draw_rounded_rect(c, 0, 0, w, h, 3, fill=CARD, outline="")

        if self.progress_max > 0 and self.progress_value > 0:
            fill_w = max(6, int(w * self.progress_value / self.progress_max))
            self._draw_rounded_rect(c, 0, 0, fill_w, h, 3,
                                    fill=GREEN, outline="")

    def _hook_drag_drop(self):
        if USE_TKINTERDND2:
            try:
                tkdnd.TkinterDnD().bindroot(self.root)
                self.root.drop_target_register(tkdnd.DND_FILES)
                self.root.dnd_bind('<<Drop>>', self._on_tkdnd_drop)
            except Exception:
                pass
        elif windnd is not None:
            windnd.hook_dropfiles(self.root, func=self.on_drop)

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

    def browse(self):
        if self.converting:
            return
        paths = filedialog.askopenfilenames(
            title="Select CBR/CBZ files",
            filetypes=[("Comic archives", "*.cbr *.cbz"), ("All files", "*.*")]
        )
        if paths:
            self.start_conversion(list(paths))

    def on_drop(self, files):
        if self.converting:
            return
        paths = [f.decode("utf-8") if isinstance(f, bytes) else f for f in files]
        self.start_conversion(paths)

    def on_file_click(self, pdf_path):
        open_file_or_folder(pdf_path)

    def clear_queue(self):
        if self.converting:
            return
        self.conversion_files = []
        self.file_list.set_files([])
        self.progress_label.configure(text="Drop files to start", fg=TEXT_DIM)
        self.progress_value = 0
        self._draw_progress()
        self.stat_success.configure(text="")
        self.stat_failed.configure(text="")
        self.open_folder_btn.set_enabled(False)
        self.clear_btn.set_enabled(False)

    def start_conversion(self, paths):
        comics = find_comic_files(paths)
        if not comics:
            return
        
        self.conversion_files = [{
            "path": c,
            "status": STATUS_PENDING,
            "pdf_path": None,
            "display_name": os.path.basename(c)
        } for c in comics]
        
        self.file_list.set_files(self.conversion_files)
        self.clear_btn.set_enabled(True)
        self.converting = True
        
        threading.Thread(target=self.run_conversion, args=(comics,), daemon=True).start()

    def run_conversion(self, comics):
        total = len(comics)
        first_dir = os.path.dirname(comics[0])
        pdf_folder = os.path.join(first_dir, "Converted PDFs")
        os.makedirs(pdf_folder, exist_ok=True)
        self.output_folder = pdf_folder

        self.root.after(0, lambda: self.progress_label.configure(
            text=f"Converting {total} file{'s' if total > 1 else ''}...", fg=TEXT_MID
        ))
        self.root.after(0, lambda: self._update_progress(0, total))
        self.root.after(0, lambda: self._update_stats(0, 0))

        success = 0
        failed = 0
        
        for i, comic in enumerate(comics):
            # Update to converting
            self.root.after(0, lambda p=comic: self.file_list.update_file_status(p, STATUS_CONVERTING))
            
            # Convert
            result, pdf_path = convert_one(comic, pdf_folder, lambda *a: None)
            
            if result:
                success += 1
                self.root.after(0, lambda p=comic, pdf=pdf_path: 
                               self.file_list.update_file_status(p, STATUS_DONE, pdf))
            else:
                failed += 1
                self.root.after(0, lambda p=comic: 
                               self.file_list.update_file_status(p, STATUS_FAILED))
            
            self.root.after(0, lambda: self._update_progress(i + 1, total))
            self.root.after(0, lambda: self._update_stats(success, failed))

        # Done
        self.converting = False
        self.root.after(0, self._on_conversion_complete, success, failed)

    def _update_progress(self, value, maximum):
        self.progress_value = value
        self.progress_max = maximum
        self._draw_progress()

    def _update_stats(self, success, failed):
        s = f"✓ {success} converted" if success else ""
        f = f"✗ {failed} failed" if failed else ""
        self.stat_success.configure(text=s)
        self.stat_failed.configure(text=f)

    def _on_conversion_complete(self, success, failed):
        if failed == 0:
            self.progress_label.configure(text="Complete!", fg=SUCCESS)
        else:
            self.progress_label.configure(
                text=f"Done with {failed} error{'s' if failed > 1 else ''}", 
                fg=ERROR if success == 0 else TEXT_MID
            )
        
        self.open_folder_btn.set_enabled(True)

    def open_output_folder(self):
        if self.output_folder:
            open_file_or_folder(self.output_folder)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    missing = []
    try:
        import img2pdf
    except ImportError:
        missing.append("img2pdf")
    
    try:
        import rarfile
    except ImportError:
        missing.append("rarfile")
    
    if missing:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Error", 
            f"Missing dependencies:\n" + "\n".join(f"  - {m}" for m in missing) +
            "\n\nInstall with: pip install -r requirements.txt"
        )
        root.destroy()
        sys.exit(1)
    
    App().run()
