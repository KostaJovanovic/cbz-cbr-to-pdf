import tkinter as tk
from tkinter import filedialog
import os
import platform
import threading
import img2pdf
import math
import random
import shutil

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
    
    # Check if we're running from a PyInstaller bundle
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    if system == "windows":
        return os.path.join(base_path, "binaries", "windows", "UnRAR.exe")
    elif system == "darwin":
        return os.path.join(base_path, "binaries", "macos", "unrar")
    else:  # linux and others
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
    """Apply dark title bar on Windows 10+ (optional, fails silently on other platforms)"""
    try:
        if platform.system() == "Windows":
            from ctypes import windll, c_int, byref
            hwnd = windll.user32.GetParent(root.winfo_id())
            windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(c_int(1)), 4)
    except Exception:
        pass  # Silently fail on non-Windows or older Windows


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
    """Build a full theme from 4 palette colors.
    Sorts by luminance: brightest -> accent/green, mid -> accent/blue,
    darker -> cards/purple, darkest -> background base."""
    colors = sorted([c1, c2, c3, c4], key=_luminance)
    darkest, dark, mid, bright = colors

    # If the darkest color is still too light, derive a dark bg from it
    lum = _luminance(darkest)
    if lum > 60:
        bg = _darken(darkest, 0.85)
    else:
        bg = _darken(darkest, 0.35)

    light_text = _luminance(bg) < 100

    # Ensure accent and green are bright enough to be visible on the bg
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


def extract_zip(zip_path, extract_to):
    """Extract ZIP archive using built-in zipfile"""
    import zipfile
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_to)
        return True
    except Exception as e:
        return False


def extract_rar(rar_path, extract_to):
    """Extract RAR archive using rarfile with bundled unrar"""
    import rarfile
    try:
        setup_rarfile()
        with rarfile.RarFile(rar_path) as rf:
            rf.extractall(extract_to)
        return True
    except Exception as e:
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
        return True

    log_func(f"  Extracting: {os.path.basename(comic_path)}", "normal")
    
    # Extract based on file type
    if comic_path.lower().endswith('.cbz'):
        success = extract_zip(comic_path, out_dir)
    elif comic_path.lower().endswith('.cbr'):
        success = extract_rar(comic_path, out_dir)
    else:
        log_func(f"  ERROR: Unsupported format", "error")
        return False
    
    if not success:
        log_func(f"  ERROR: Failed to extract archive", "error")
        return False

    exts = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".gif", ".webp")
    images = sorted([
        os.path.join(r, f)
        for r, _, fs in os.walk(out_dir)
        for f in fs if f.lower().endswith(exts)
    ])

    if not images:
        log_func(f"  ERROR: No images found in archive", "error")
        _cleanup(out_dir)
        return False

    log_func(f"  Converting {len(images)} pages...", "normal")
    try:
        with open(pdf_out, "wb") as f:
            f.write(img2pdf.convert(images))
    except Exception as e:
        log_func(f"  ERROR creating PDF: {e}", "error")
        if os.path.exists(pdf_out):
            os.remove(pdf_out)
        _cleanup(out_dir)
        return False

    _cleanup(out_dir)
    log_func(f"  Done: {basename}.pdf", "success")
    return True


def _cleanup(out_dir):
    try:
        shutil.rmtree(out_dir, ignore_errors=True)
    except Exception:
        pass


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Comic to PDF")
        self.root.geometry("640x540")
        self.root.minsize(480, 400)
        self.root.configure(bg=BG)
        self.converting = False

        # Apply dark title bar on Windows (optional)
        apply_dark_title_bar(self.root)

        # Main container with padding
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill=tk.BOTH, expand=True, padx=28, pady=(24, 24))

        # Header row
        header = tk.Frame(main, bg=BG)
        header.pack(fill=tk.X, pady=(0, 18))

        tk.Label(
            header, text="Comic to PDF",
            font=("Segoe UI", 20, "bold"), fg=TEXT, bg=BG
        ).pack(side=tk.LEFT)

        # Subtitle badge
        badge = tk.Label(
            header, text=" CBR  CBZ ",
            font=("Segoe UI", 8, "bold"), fg=PURPLE, bg=CARD,
            padx=8, pady=2
        )
        badge.pack(side=tk.LEFT, padx=(12, 0), pady=(6, 0))

        # Drop zone
        self.drop_zone = tk.Canvas(
            main, height=140, bg=BG_MID, highlightthickness=0, cursor="hand2"
        )
        self.drop_zone.pack(fill=tk.X)
        self.drop_zone.bind("<Configure>", self._draw_drop_zone)
        self.drop_zone.bind("<Button-1>", lambda e: self.browse())
        self._drop_hover = False
        self.drop_zone.bind("<Enter>", self._on_drop_enter)
        self.drop_zone.bind("<Leave>", self._on_drop_leave)

        # Button row
        btn_frame = tk.Frame(main, bg=BG)
        btn_frame.pack(fill=tk.X, pady=(14, 0))

        self.browse_btn = tk.Canvas(
            btn_frame, height=36, width=150, bg=BG, highlightthickness=0,
            cursor="hand2"
        )
        self.browse_btn.pack()
        self.browse_btn.bind("<Configure>", self._draw_button)
        self.browse_btn.bind("<Button-1>", lambda e: self.browse())
        self.browse_btn.bind("<Enter>", self._on_btn_enter)
        self.browse_btn.bind("<Leave>", self._on_btn_leave)
        self._btn_hover = False

        # Progress section
        prog_frame = tk.Frame(main, bg=BG)
        prog_frame.pack(fill=tk.X, pady=(16, 0))

        self.progress_label = tk.Label(
            prog_frame, text="Waiting for files...",
            font=("Segoe UI", 9), fg=TEXT_DIM, bg=BG, anchor="w"
        )
        self.progress_label.pack(fill=tk.X)

        # Progress bar canvas
        self.prog_canvas = tk.Canvas(
            prog_frame, height=8, bg=CARD, highlightthickness=0
        )
        self.prog_canvas.pack(fill=tk.X, pady=(6, 0))
        self.prog_canvas.bind("<Configure>", self._draw_progress)
        self.progress_value = 0
        self.progress_max = 1

        # Stats row
        self.stats_frame = tk.Frame(main, bg=BG)
        self.stats_frame.pack(fill=tk.X, pady=(4, 0))

        self.stat_success = tk.Label(
            self.stats_frame, text="", font=("Segoe UI", 8),
            fg=SUCCESS, bg=BG
        )
        self.stat_success.pack(side=tk.LEFT)

        self.stat_failed = tk.Label(
            self.stats_frame, text="", font=("Segoe UI", 8),
            fg=ERROR, bg=BG
        )
        self.stat_failed.pack(side=tk.LEFT, padx=(10, 0))

        # Log area with header
        log_header = tk.Frame(main, bg=BG)
        log_header.pack(fill=tk.X, pady=(14, 0))
        tk.Label(
            log_header, text="Activity Log",
            font=("Segoe UI Semibold", 9), fg=TEXT_DIM, bg=BG
        ).pack(side=tk.LEFT)

        # Log container with border effect
        log_border = tk.Frame(main, bg=CARD_BORDER)
        log_border.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        log_inner = tk.Frame(log_border, bg=LOG_BG)
        log_inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        self.log_text = tk.Text(
            log_inner, bg=LOG_BG, fg=TEXT_MID,
            font=("Cascadia Code", 9),
            relief=tk.FLAT, state=tk.DISABLED, wrap=tk.WORD,
            borderwidth=0, padx=14, pady=10,
            selectbackground=BLUE, selectforeground=TEXT,
            insertbackground=GREEN, spacing1=2, spacing3=2
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Frame(log_inner, bg=LOG_BG, width=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.scroll_thumb = tk.Canvas(
            scrollbar, bg=LOG_BG, highlightthickness=0, width=6
        )
        self.scroll_thumb.pack(fill=tk.BOTH, expand=True, padx=2, pady=4)

        self.log_text.tag_configure("normal", foreground=TEXT_MID)
        self.log_text.tag_configure("dim", foreground=TEXT_DIM)
        self.log_text.tag_configure("success", foreground=SUCCESS)
        self.log_text.tag_configure("error", foreground=ERROR)
        self.log_text.tag_configure("header", foreground=TEXT, font=("Cascadia Code", 9, "bold"))
        self.log_text.tag_configure("accent", foreground=ACCENT)

        # Hook drag and drop
        self._hook_drag_drop()

    def _hook_drag_drop(self):
        """Setup cross-platform drag-and-drop"""
        if USE_TKINTERDND2:
            try:
                tkdnd.TkinterDnD().bindroot(self.root)
                self.root.drop_target_register(tkdnd.DND_FILES)
                self.root.dnd_bind('<<Drop>>', self._on_tkdnd_drop)
            except Exception as e:
                self.log("Warning: tkinterdnd2 available but failed to initialize", "dim")
        elif windnd is not None:
            windnd.hook_dropfiles(self.root, func=self.on_drop)
        else:
            self.log("Warning: No drag-and-drop support available.\nInstall tkinterdnd2 for cross-platform support.", "dim")

    def _on_tkdnd_drop(self, event):
        """Handle tkinterdnd2 drop event"""
        if self.converting:
            return
        # Parse the dropped files
        files_str = event.data
        # Handle different formats: can be space-separated or enclosed in braces
        if files_str.startswith('{') and files_str.endswith('}'):
            files_str = files_str[1:-1]
        
        # Split by space, respecting quoted paths
        import shlex
        try:
            paths = shlex.split(files_str)
        except:
            paths = files_str.split()
        
        self.start_conversion(paths)

    # --- Drawing Methods ---

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

    def _draw_drop_zone(self, event=None):
        c = self.drop_zone
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        pad = 2

        # Outer shape
        fill = BG_LIGHT if self._drop_hover else BG_MID
        self._draw_rounded_rect(c, pad, pad, w - pad, h - pad, 16,
                                fill=fill, outline=CARD_BORDER, width=1.5)

        # Dashed inner border
        inset = 12
        dash_color = PURPLE_LIGHT if self._drop_hover else PURPLE
        self._draw_rounded_rect(
            c, inset, inset, w - inset, h - inset, 10,
            fill="", outline=dash_color, width=1, dash=(6, 4)
        )

        cx = w // 2
        cy = h // 2

        # Folder icon using simple shapes
        icon_color = GREEN if self._drop_hover else ACCENT
        c.create_text(cx, cy - 14, text="\u21E9",
                      font=("Segoe UI", 28), fill=icon_color)

        label_color = TEXT if self._drop_hover else TEXT_MID
        c.create_text(cx, cy + 26, text="Drop CBR / CBZ files or folders here",
                      font=("Segoe UI", 10), fill=label_color)
        c.create_text(cx, cy + 44, text="or click to browse",
                      font=("Segoe UI", 8), fill=TEXT_DIM)

    def _on_drop_enter(self, e):
        self._drop_hover = True
        self._draw_drop_zone()

    def _on_drop_leave(self, e):
        self._drop_hover = False
        self._draw_drop_zone()

    def _draw_button(self, event=None):
        c = self.browse_btn
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()

        if self.converting:
            fill = CARD
            text_color = TEXT_DIM
        elif self._btn_hover:
            fill = ACCENT_HOVER
            text_color = BG
        else:
            fill = ACCENT
            text_color = BG

        self._draw_rounded_rect(c, 0, 0, w, h, 8, fill=fill, outline="")
        c.create_text(w // 2, h // 2, text="Browse Files",
                      font=("Segoe UI Semibold", 10), fill=text_color)

    def _on_btn_enter(self, e):
        if not self.converting:
            self._btn_hover = True
            self._draw_button()

    def _on_btn_leave(self, e):
        self._btn_hover = False
        self._draw_button()

    def _draw_progress(self, event=None):
        c = self.prog_canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()

        # Track
        self._draw_rounded_rect(c, 0, 0, w, h, 4, fill=CARD, outline="")

        # Fill
        if self.progress_max > 0 and self.progress_value > 0:
            fill_w = max(8, int(w * self.progress_value / self.progress_max))
            self._draw_rounded_rect(c, 0, 0, fill_w, h, 4,
                                    fill=GREEN, outline="")

            # Glow effect
            glow_w = min(fill_w, 40)
            self._draw_rounded_rect(c, fill_w - glow_w, 0, fill_w, h, 4,
                                    fill=GREEN, outline="")

    # --- Logic ---

    def log(self, msg, tag="normal"):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n", tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def log_threadsafe(self, msg, tag="normal"):
        self.root.after(0, self.log, msg, tag)

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

    def start_conversion(self, paths):
        comics = find_comic_files(paths)
        if not comics:
            self.log("No CBR/CBZ files found.", "error")
            return
        self.converting = True
        self._draw_button()
        threading.Thread(target=self.run_conversion, args=(comics,), daemon=True).start()

    def _update_progress(self, value, maximum, label_text):
        self.progress_value = value
        self.progress_max = maximum
        self._draw_progress()
        self.progress_label.configure(text=label_text, fg=TEXT_MID)

    def _update_stats(self, success, failed):
        s = f"{success} converted" if success else ""
        f = f"{failed} failed" if failed else ""
        self.stat_success.configure(text=s)
        self.stat_failed.configure(text=f)

    def run_conversion(self, comics):
        total = len(comics)

        first_dir = os.path.dirname(comics[0])
        pdf_folder = os.path.join(first_dir, "Converted PDFs")
        os.makedirs(pdf_folder, exist_ok=True)

        self.root.after(0, self.log, f"Found {total} file(s) to convert.", "header")
        self.root.after(0, self.log, f"Output: {pdf_folder}\n", "dim")
        self.root.after(0, self._update_progress, 0, total, f"Converting 0/{total}...")
        self.root.after(0, self._update_stats, 0, 0)

        success = 0
        failed = 0
        for i, comic in enumerate(comics):
            name = os.path.basename(comic)
            self.root.after(
                0, self._update_progress, i, total, f"[{i + 1}/{total}]  {name}"
            )
            if convert_one(comic, pdf_folder, self.log_threadsafe):
                success += 1
            else:
                failed += 1
            self.root.after(0, self._update_progress, i + 1, total, f"[{i + 1}/{total}]  {name}")
            self.root.after(0, self._update_stats, success, failed)

        tag = "success" if failed == 0 else "error"
        self.root.after(0, self.log, f"\nAll done!", tag)
        self.root.after(0, self._update_progress, total, total, "Complete")
        self.root.after(0, lambda: self.progress_label.configure(
            fg=SUCCESS if failed == 0 else ERROR
        ))
        self.converting = False
        self.root.after(0, self._draw_button)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    import sys
    
    # Check for required dependencies
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
        tk.messagebox.showerror(
            "Error", 
            f"Missing dependencies:\n" + "\n".join(f"  - {m}" for m in missing) +
            "\n\nInstall with: pip install -r requirements.txt"
        )
        root.destroy()
        sys.exit(1)
    
    App().run()
