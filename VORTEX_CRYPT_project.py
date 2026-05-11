import os, bcrypt, base64, threading, time, json
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from datetime import datetime

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
CRYPT_EXT    = ".crypt"
PROFILE_FILE = "profile.json"
DEFAULT_HASH = b'$2b$12$etosH4DNmrBEJ1C0CNzF1e.jJtlI97HeZiM2eQNAbrPcbzSCYaSmy'.decode()

# ─── Midnight-Purple Palette ──────────────────
C = {
    "bg":           "#09010f",   # near-black
    "surface":      "#120526",   # dark purple
    "card":         "#1b0a36",   # card bg
    "border":       "#3a1a6b",   # subtle border
    "border_hi":    "#7c3aed",   # highlighted border
    "accent":       "#9333ea",   # main accent
    "accent_dim":   "#6d28d9",   # darker accent
    "accent_glow":  "#c084fc",   # lighter accent
    "text":         "#e9d5ff",   # primary text
    "text_dim":     "#9474c0",   # secondary text
    "text_muted":   "#4d3175",   # muted text
    "success":      "#4ade80",
    "error":        "#f87171",
    "warning":      "#fbbf24",
    "info":         "#818cf8",
    "enc_btn":      "#4c1d95",   # encrypt button
    "dec_btn":      "#1e1b4b",   # decrypt button
    "danger":       "#7f1d1d",
    "danger_hi":    "#991b1b",
    "scrollbar":    "#3a1a6b",
}

# ─────────────────────────────────────────────
#  GLOBALS
# ─────────────────────────────────────────────
file_queue  = []       # list of dicts: {path, size, status}
ui_elements = {}       # path → CTkFrame; path+"__status" → status label
LOG_ENTRIES = []
SESSION_KEY = None


# ─────────────────────────────────────────────
#  PROFILE MANAGEMENT
# ─────────────────────────────────────────────
def load_profile():
    if not os.path.exists(PROFILE_FILE):
        data = {"admin_name": "admin", "password_hash": DEFAULT_HASH}
        with open(PROFILE_FILE, "w") as f:
            json.dump(data, f)
        return data
    with open(PROFILE_FILE, "r") as f:
        return json.load(f)

def save_profile(name, p_hash):
    with open(PROFILE_FILE, "w") as f:
        json.dump({"admin_name": name, "password_hash": p_hash}, f)


# ─────────────────────────────────────────────
#  UTILITIES
# ─────────────────────────────────────────────
def secure_delete(filepath):
    """3-pass random overwrite before unlinking."""
    try:
        size = os.path.getsize(filepath)
        with open(filepath, "r+b") as f:
            for _ in range(3):
                f.seek(0)
                f.write(os.urandom(size))
                f.flush()
        os.remove(filepath)
    except Exception:
        try:
            os.remove(filepath)
        except Exception:
            pass

def format_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} {unit}"
        n /= 1024
    return f"{n:.2f} TB"

def file_icon(path):
    ext = os.path.splitext(path)[1].lower()
    return {
        ".pdf":"📄", ".txt":"📝", ".doc":"📝", ".docx":"📝",
        ".jpg":"🖼", ".jpeg":"🖼", ".png":"🖼", ".gif":"🖼", ".webp":"🖼",
        ".mp4":"🎬", ".avi":"🎬", ".mkv":"🎬", ".mov":"🎬",
        ".mp3":"🎵", ".wav":"🎵", ".flac":"🎵", ".ogg":"🎵",
        ".zip":"📦", ".rar":"📦", ".7z":"📦", ".tar":"📦", ".gz":"📦",
        ".py":"🐍", ".js":"⚡", ".ts":"⚡", ".html":"🌐", ".css":"🎨",
        ".crypt":"🔐", ".exe":"⚙", ".sh":"⚙", ".bat":"⚙",
        ".json":"🗃", ".xml":"🗃", ".csv":"📊", ".xlsx":"📊",
        ".db":"🗄", ".sqlite":"🗄",
    }.get(ext, "📁")


# ─────────────────────────────────────────────
#  CRYPTO ENGINE
# ─────────────────────────────────────────────
class CryptEngine:
    _SALT = b'\x14\xab\xbc\x88\xfe\x01\x99\x22'

    @staticmethod
    def derive_key(password: str) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=CryptEngine._SALT,
            iterations=100_000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))


# ─────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────
def update_log(msg: str, color: str = None):
    if color is None:
        color = C["success"]
    if "log" not in ui_elements:
        return
    ts    = datetime.now().strftime("%H:%M:%S")
    text  = f" ▸ {ts}  {msg}"
    LOG_ENTRIES.append(text)
    lbl = ctk.CTkLabel(
        ui_elements["log"], text=text,
        font=("Consolas", 11), text_color=color, anchor="w"
    )
    lbl.pack(fill="x", padx=8, pady=1)
    try:
        ui_elements["log"]._parent_canvas.yview_moveto(1.0)
    except Exception:
        pass


# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class MainApp(TkinterDnD.Tk):

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.profile       = load_profile()
        self.login_attempts = 0
        self.is_processing  = False

        self.title("VORTEX-CRYPT  //  PHANTOM EDITION")
        self.geometry("1320x900")
        self.minsize(1100, 720)
        self.configure(bg=C["bg"])

        # DnD on root (catches drops anywhere)
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self._on_root_drop)

        self.withdraw()
        self.run_auth()

    # ── DnD helper ──────────────────────────────
    def _parse_dnd_paths(self, raw: str):
        """Correctly splits TkinterDnD2 path strings (handles spaces / curly braces)."""
        paths = []
        for p in self.tk.splitlist(raw):
            p = p.strip().strip('{}').strip('"').strip("'")
            if p and os.path.exists(p):
                paths.append(p)
        return paths

    def _on_root_drop(self, event):
        if hasattr(self, "drop_outer"):
            self.drop_outer.configure(border_color=C["border"])
        self.handle_inj(self._parse_dnd_paths(event.data))

    # ── Auth ─────────────────────────────────────
    def run_auth(self):
        self.login_attempts = 0

        dlg = ctk.CTkToplevel(self)
        dlg.geometry("480x590")
        dlg.configure(fg_color=C["bg"])
        dlg.resizable(False, False)
        dlg.title("Authentication")
        dlg.protocol("WM_DELETE_WINDOW", self.quit)
        self._auth_dlg = dlg

        # Logo
        ctk.CTkLabel(dlg, text="⬡", font=("Segoe UI Emoji", 52), text_color=C["accent"]).pack(pady=(45, 0))
        ctk.CTkLabel(dlg, text="VORTEX-CRYPT", font=("Impact", 46), text_color=C["accent_glow"]).pack()
        ctk.CTkLabel(dlg, text="PHANTOM  EDITION", font=("Consolas", 11), text_color=C["accent_dim"]).pack()
        ctk.CTkLabel(dlg, text=f"OPERATOR:  {self.profile['admin_name'].upper()}",
                     font=("Consolas", 12), text_color=C["text_dim"]).pack(pady=(16, 0))

        # Password field
        field_frame = ctk.CTkFrame(dlg, fg_color=C["surface"], corner_radius=12,
                                   border_width=1, border_color=C["border"])
        field_frame.pack(pady=28, padx=52, fill="x")
        self._pwd_entry = ctk.CTkEntry(
            field_frame, show="●", height=52,
            placeholder_text="ENTER MASTER KEY",
            fg_color="transparent", border_width=0,
            font=("Consolas", 15), text_color=C["text"],
        )
        self._pwd_entry.pack(padx=14, pady=10, fill="x")
        self._pwd_entry.focus_force()

        # Status label
        self._auth_status = ctk.CTkLabel(dlg, text="", font=("Consolas", 11), text_color=C["error"])
        self._auth_status.pack()

        ctk.CTkButton(
            dlg, text="[ AUTHENTICATE ]", height=48,
            fg_color=C["accent_dim"], hover_color=C["accent"],
            text_color="white", font=("Consolas", 14, "bold"),
            corner_radius=8, command=self._attempt_login,
        ).pack(pady=14, padx=52, fill="x")

        dlg.bind("<Return>", lambda _: self._attempt_login())

    def _attempt_login(self):
        pwd = self._pwd_entry.get()
        if not pwd:
            self._auth_status.configure(text="⚠  KEY REQUIRED")
            return
        if bcrypt.checkpw(pwd.encode(), self.profile["password_hash"].encode()):
            global SESSION_KEY
            SESSION_KEY = CryptEngine.derive_key(pwd)
            self._auth_status.configure(text="✓  ACCESS GRANTED", text_color=C["success"])
            self._auth_dlg.after(500, lambda: (
                self._auth_dlg.destroy(), self.deiconify(), self.build_ui()
            ))
        else:
            self.login_attempts += 1
            remaining = 3 - self.login_attempts
            if remaining > 0:
                self._auth_status.configure(
                    text=f"✗  INVALID KEY  —  {remaining} ATTEMPT{'S' if remaining != 1 else ''} REMAINING",
                    text_color=C["error"]
                )
                self._pwd_entry.delete(0, "end")
                self._shake(self._auth_dlg)
            else:
                messagebox.showerror("SYSTEM LOCK", "MAXIMUM FAILURES EXCEEDED.\nSESSION TERMINATED.")
                self.quit()

    def _shake(self, win):
        ox, oy = win.winfo_x(), win.winfo_y()
        for i in range(7):
            d = 9 if i % 2 == 0 else -9
            win.after(i * 38, lambda dx=d: win.geometry(f"+{ox + dx}+{oy}"))
        win.after(270, lambda: win.geometry(f"+{ox}+{oy}"))

    # ── Main UI build ────────────────────────────
    def build_ui(self):
        # ── Top bar ──────────────────────────────
        nav = ctk.CTkFrame(self, height=72, fg_color=C["surface"],
                           corner_radius=0, border_width=1, border_color=C["border"])
        nav.pack(fill="x"); nav.pack_propagate(False)

        ni = ctk.CTkFrame(nav, fg_color="transparent")
        ni.pack(fill="both", expand=True, padx=24)

        ctk.CTkLabel(ni, text="⬡  VORTEX-CRYPT", font=("Impact", 30),
                     text_color=C["accent_glow"]).pack(side="left", pady=12)
        ctk.CTkLabel(ni, text="PHANTOM EDITION v2.0", font=("Consolas", 9),
                     text_color=C["text_muted"]).pack(side="left", padx=12, pady=(22, 0))

        self._clock_lbl = ctk.CTkLabel(ni, text="", font=("Consolas", 11), text_color=C["accent"])
        self._clock_lbl.pack(side="right", pady=20)
        self._tick_clock()

        self.sp_val = ctk.CTkLabel(ni, text="QUEUED: 0  |  STATUS: IDLE",
                                   font=("Consolas", 12), text_color=C["text_dim"])
        self.sp_val.pack(side="right", padx=22, pady=20)

        # ── Body ─────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=16)

        # ── Left sidebar ─────────────────────────
        self._build_sidebar(body)

        # ── Right panel ──────────────────────────
        self._build_main_panel(body)

    def _build_sidebar(self, parent):
        side = ctk.CTkFrame(parent, width=228, fg_color=C["surface"],
                            corner_radius=12, border_width=1, border_color=C["border"])
        side.pack(side="left", fill="y", padx=(0, 16))
        side.pack_propagate(False)

        ctk.CTkLabel(side, text="⚙  CONTROLS", font=("Impact", 17),
                     text_color=C["text_dim"]).pack(pady=(20, 14))

        def section(label):
            ctk.CTkLabel(side, text=label, font=("Consolas", 9),
                         text_color=C["text_muted"]).pack(anchor="w", padx=16, pady=(8, 2))

        def btn(parent_widget, text, color, hover, command, **kw):
            return ctk.CTkButton(
                parent_widget, text=text, fg_color=color, hover_color=hover,
                text_color=C["text"], font=("Consolas", 12), corner_radius=7,
                command=command, **kw
            )

        # File operations
        section("FILE OPERATIONS")
        btn(side, "📂  ADD FILES",   C["card"], C["border"],
            lambda: self.handle_inj(filedialog.askopenfilenames())).pack(pady=3, padx=16, fill="x")
        btn(side, "📁  ADD FOLDER",  C["card"], C["border"],
            lambda: self.handle_inj([filedialog.askdirectory()])).pack(pady=3, padx=16, fill="x")

        ctk.CTkFrame(side, height=1, fg_color=C["border"]).pack(fill="x", padx=16, pady=12)

        # Crypto operations
        section("CRYPTOGRAPHIC OPS")
        ctk.CTkButton(
            side, text="🔐  ENCRYPT ALL", height=44,
            fg_color=C["enc_btn"], hover_color="#5b21b6",
            text_color="white", font=("Consolas", 13, "bold"), corner_radius=8,
            command=lambda: self._start_process("enc")
        ).pack(pady=4, padx=16, fill="x")
        ctk.CTkButton(
            side, text="🔓  DECRYPT ALL", height=44,
            fg_color=C["dec_btn"], hover_color="#312e81",
            text_color="white", font=("Consolas", 13, "bold"), corner_radius=8,
            command=lambda: self._start_process("dec")
        ).pack(pady=4, padx=16, fill="x")

        ctk.CTkFrame(side, height=1, fg_color=C["border"]).pack(fill="x", padx=16, pady=12)

        # Queue management
        section("QUEUE MANAGEMENT")
        btn(side, "🗑  CLEAR QUEUE", C["danger"], C["danger_hi"],
            self.clear_queue).pack(pady=3, padx=16, fill="x")

        # Stats box
        sf = ctk.CTkFrame(side, fg_color=C["card"], corner_radius=8,
                          border_width=1, border_color=C["border"])
        sf.pack(padx=16, pady=14, fill="x")
        ctk.CTkLabel(sf, text="QUEUE STATS", font=("Consolas", 9, "bold"),
                     text_color=C["accent"]).pack(pady=(8, 2))
        self._stat_files = ctk.CTkLabel(sf, text="Files: 0", font=("Consolas", 10),
                                        text_color=C["text_dim"])
        self._stat_files.pack()
        self._stat_size = ctk.CTkLabel(sf, text="Total: 0 B", font=("Consolas", 10),
                                       text_color=C["text_dim"])
        self._stat_size.pack(pady=(0, 8))

        # Bottom actions
        btn(side, "📤  EXPORT LOG",  C["info"], "#6366f1", self.export_log
            ).pack(side="bottom", pady=4, padx=16, fill="x")
        btn(side, "⚙  SETTINGS",   C["card"], C["border"], self.open_settings
            ).pack(side="bottom", pady=4, padx=16, fill="x")
        ctk.CTkButton(
            side, text="🚪  LOGOUT", fg_color=C["danger"], hover_color=C["danger_hi"],
            text_color="white", font=("Consolas", 12), corner_radius=7,
            command=self.logout
        ).pack(side="bottom", pady=4, padx=16, fill="x")

    def _build_main_panel(self, parent):
        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.pack(side="right", fill="both", expand=True)

        # Queue header + search
        qh = ctk.CTkFrame(right, fg_color="transparent")
        qh.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(qh, text="TARGET INJECTION ZONE", font=("Impact", 17),
                     text_color=C["accent"]).pack(side="left")

        self._search_var = ctk.StringVar()
        self._search_var.trace("w", self._filter_queue)
        ctk.CTkEntry(
            qh, textvariable=self._search_var, width=210, height=30,
            placeholder_text="🔍  Search queue…",
            fg_color=C["card"], border_color=C["border"],
            font=("Consolas", 11), text_color=C["text"]
        ).pack(side="right")

        # Drop zone
        self.drop_outer = ctk.CTkFrame(right, fg_color=C["surface"],
                                        border_width=2, border_color=C["border"],
                                        corner_radius=12)
        self.drop_outer.pack(fill="both", expand=True, pady=(0, 12))

        self._drop_hint = ctk.CTkLabel(
            self.drop_outer,
            text="◈  DROP FILES OR FOLDERS HERE  ◈\n\nor use  ADD FILES  /  ADD FOLDER  above",
            font=("Impact", 19), text_color=C["text_muted"]
        )
        self._drop_hint.place(relx=0.5, rely=0.42, anchor="center")

        # Scrollable queue
        self.queue_fm = ctk.CTkScrollableFrame(
            self.drop_outer, fg_color="transparent", border_width=0,
            scrollbar_button_color=C["scrollbar"],
            scrollbar_button_hover_color=C["border_hi"]
        )
        self.queue_fm.pack(fill="both", expand=True, padx=6, pady=6)

        # Register DnD on the scrollable inner frame too
        self.queue_fm.drop_target_register(DND_FILES)
        self.queue_fm.dnd_bind("<<Drop>>", self._on_root_drop)
        self.queue_fm.dnd_bind(
            "<<DragEnter>>", lambda _: self.drop_outer.configure(border_color=C["border_hi"]))
        self.queue_fm.dnd_bind(
            "<<DragLeave>>", lambda _: self.drop_outer.configure(border_color=C["border"]))

        # Progress bar
        pb_frame = ctk.CTkFrame(right, fg_color=C["surface"], corner_radius=8,
                                border_width=1, border_color=C["border"])
        pb_frame.pack(fill="x", pady=(0, 10))
        pb_inner = ctk.CTkFrame(pb_frame, fg_color="transparent")
        pb_inner.pack(fill="x", padx=12, pady=(8, 4))
        self._pb_label = ctk.CTkLabel(pb_inner, text="READY", font=("Consolas", 10),
                                      text_color=C["accent"])
        self._pb_label.pack(side="left")
        self._pb_pct = ctk.CTkLabel(pb_inner, text="0%", font=("Consolas", 10, "bold"),
                                    text_color=C["accent_glow"])
        self._pb_pct.pack(side="right")
        self.pb = ctk.CTkProgressBar(pb_frame, progress_color=C["accent"],
                                     fg_color=C["card"], height=6, corner_radius=3)
        self.pb.pack(fill="x", padx=12, pady=(0, 8))
        self.pb.set(0)

        # Audit log
        log_hdr = ctk.CTkFrame(right, fg_color="transparent")
        log_hdr.pack(fill="x")
        ctk.CTkLabel(log_hdr, text="SYSTEM AUDIT LOG", font=("Impact", 14),
                     text_color=C["accent"]).pack(side="left")
        ctk.CTkButton(log_hdr, text="CLEAR", width=68, height=26,
                      fg_color=C["card"], hover_color=C["border"],
                      font=("Consolas", 10), command=self.clear_log).pack(side="right")

        ui_elements["log"] = ctk.CTkScrollableFrame(
            right, height=165, fg_color=C["surface"],
            border_width=1, border_color=C["border"], corner_radius=8,
            scrollbar_button_color=C["scrollbar"],
            scrollbar_button_hover_color=C["border_hi"]
        )
        ui_elements["log"].pack(fill="x", pady=(5, 0))

        update_log("VORTEX-CRYPT PHANTOM v2.0  ——  SYSTEM ONLINE", C["accent_glow"])
        update_log("Drag & drop files or folders anywhere into the window.", C["info"])

    # ── Clock ────────────────────────────────────
    def _tick_clock(self):
        if self._clock_lbl.winfo_exists():
            self._clock_lbl.configure(
                text=datetime.now().strftime("  %H:%M:%S   %Y-%m-%d"))
            self.after(1000, self._tick_clock)

    # ── Queue search/filter ──────────────────────
    def _filter_queue(self, *_):
        q = self._search_var.get().lower()
        for key, widget in ui_elements.items():
            if key in ("log",) or key.endswith("__status"):
                continue
            if isinstance(widget, ctk.CTkFrame):
                visible = q in os.path.basename(key).lower()
                if visible:
                    widget.pack(fill="x", padx=5, pady=3)
                else:
                    widget.pack_forget()

    # ── Injection ────────────────────────────────
    def handle_inj(self, paths):
        if not paths:
            return
        added = 0
        for path in paths:
            if not path:
                continue
            path = path.strip().strip("{}").strip('"').strip("'")
            if not os.path.exists(path):
                continue
            if os.path.isdir(path):
                update_log(f"SCANNING DIR:  {os.path.basename(path)}", C["info"])
                n = 0
                for root, _, files in os.walk(path):
                    for fname in files:
                        if self._inject_single(os.path.join(root, fname)):
                            n += 1
                update_log(f"LOADED {n} FILE(S) FROM:  {os.path.basename(path)}", C["info"])
                added += n
            else:
                if self._inject_single(path):
                    added += 1
        if added:
            self._update_queue_status()

    def _inject_single(self, path: str) -> bool:
        if any(f["path"] == path for f in file_queue):
            return False
        try:
            size = os.path.getsize(path)
        except Exception:
            size = 0

        file_queue.append({"path": path, "size": size, "status": "pending"})
        self._drop_hint.place_forget()

        # Build row
        row = ctk.CTkFrame(self.queue_fm, fg_color=C["card"],
                           border_width=1, border_color=C["border"], corner_radius=8)
        row.pack(fill="x", padx=5, pady=3)

        icon  = file_icon(path)
        fname = os.path.basename(path)
        dname = os.path.dirname(path)
        dname_short = ("…" + dname[-28:]) if len(dname) > 30 else dname

        # Left: icon + names
        lf = ctk.CTkFrame(row, fg_color="transparent")
        lf.pack(side="left", fill="x", expand=True, padx=10, pady=7)
        ctk.CTkLabel(lf, text=icon, font=("Segoe UI Emoji", 16)).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(lf, text=fname, font=("Consolas", 12, "bold"),
                     text_color=C["text"], anchor="w").pack(side="left")
        ctk.CTkLabel(lf, text=f"  {dname_short}", font=("Consolas", 9),
                     text_color=C["text_muted"]).pack(side="left")

        # Right: size | status | remove
        rf = ctk.CTkFrame(row, fg_color="transparent")
        rf.pack(side="right", padx=8)

        status_lbl = ctk.CTkLabel(rf, text="◉ PENDING", font=("Consolas", 10),
                                   text_color=C["warning"])
        status_lbl.pack(side="left", padx=8)

        ctk.CTkLabel(rf, text=format_size(size), font=("Consolas", 10),
                     text_color=C["text_dim"]).pack(side="left", padx=5)

        ctk.CTkButton(
            rf, text="✕", width=28, height=28,
            fg_color=C["danger"], hover_color=C["danger_hi"],
            font=("Consolas", 12, "bold"), corner_radius=6,
            command=lambda p=path, r=row: self._remove_item(p, r)
        ).pack(side="left", padx=(5, 0))

        ui_elements[path]               = row
        ui_elements[f"{path}__status"] = status_lbl
        return True

    def _remove_item(self, path: str, row):
        global file_queue
        file_queue = [f for f in file_queue if f["path"] != path]
        row.destroy()
        ui_elements.pop(path, None)
        ui_elements.pop(f"{path}__status", None)
        self._update_queue_status()
        if not file_queue:
            self._drop_hint.place(relx=0.5, rely=0.42, anchor="center")

    def _update_queue_status(self):
        total = sum(f["size"] for f in file_queue)
        n     = len(file_queue)
        self.sp_val.configure(
            text=f"QUEUED: {n}  |  {format_size(total)}  |  STATUS: READY")
        self._stat_files.configure(text=f"Files: {n}")
        self._stat_size.configure(text=f"Total: {format_size(total)}")

    # ── Queue control ────────────────────────────
    def clear_queue(self):
        if file_queue and not messagebox.askyesno("CLEAR QUEUE", "Remove all files from queue?"):
            return
        file_queue.clear()
        for w in self.queue_fm.winfo_children():
            w.destroy()
        for key in [k for k in ui_elements if k != "log"]:
            del ui_elements[key]
        self.sp_val.configure(text="QUEUED: 0  |  STATUS: IDLE")
        self._stat_files.configure(text="Files: 0")
        self._stat_size.configure(text="Total: 0 B")
        self.pb.set(0)
        self._pb_label.configure(text="READY")
        self._pb_pct.configure(text="0%")
        self._drop_hint.place(relx=0.5, rely=0.42, anchor="center")
        update_log("QUEUE PURGED.", C["error"])

    def clear_log(self):
        for w in ui_elements["log"].winfo_children():
            w.destroy()
        LOG_ENTRIES.clear()

    # ── Logout ───────────────────────────────────
    def logout(self):
        if not messagebox.askyesno("LOGOUT", "Clear session and return to login?"):
            return
        global SESSION_KEY
        SESSION_KEY = None
        file_queue.clear()
        ui_elements.clear()
        self.withdraw()
        for w in self.winfo_children():
            w.destroy()
        self.run_auth()

    # ── Settings ─────────────────────────────────
    def open_settings(self):
        st = ctk.CTkToplevel(self)
        st.geometry("430x590")
        st.configure(fg_color=C["bg"])
        st.title("Settings")
        st.resizable(False, False)

        ctk.CTkLabel(st, text="⚙  PROFILE SETTINGS", font=("Impact", 22),
                     text_color=C["accent_glow"]).pack(pady=22)

        def section_frame():
            f = ctk.CTkFrame(st, fg_color=C["surface"], corner_radius=10,
                             border_width=1, border_color=C["border"])
            f.pack(padx=30, fill="x", pady=5)
            return f

        def field(parent, placeholder):
            e = ctk.CTkEntry(parent, placeholder_text=placeholder, height=40,
                             fg_color=C["card"], border_color=C["border"], text_color=C["text"],
                             font=("Consolas", 12))
            e.pack(padx=14, pady=(4, 10), fill="x")
            return e

        id_f = section_frame()
        ctk.CTkLabel(id_f, text="IDENTITY", font=("Consolas", 9),
                     text_color=C["text_muted"]).pack(anchor="w", padx=14, pady=(10, 2))
        name_in = field(id_f, f"Display name  (current: {self.profile['admin_name']})")

        sec_f = section_frame()
        ctk.CTkLabel(sec_f, text="SECURITY", font=("Consolas", 9),
                     text_color=C["text_muted"]).pack(anchor="w", padx=14, pady=(10, 2))
        curr_p = ctk.CTkEntry(sec_f, show="●", placeholder_text="Current Password  (required)",
                              height=40, fg_color=C["card"], border_color=C["border"],
                              text_color=C["text"], font=("Consolas", 12))
        curr_p.pack(padx=14, pady=(4, 6), fill="x")
        new_p  = ctk.CTkEntry(sec_f, show="●", placeholder_text="New Password  (leave blank to keep)",
                              height=40, fg_color=C["card"], border_color=C["border"],
                              text_color=C["text"], font=("Consolas", 12))
        new_p.pack(padx=14, pady=(0, 6), fill="x")
        conf_p = ctk.CTkEntry(sec_f, show="●", placeholder_text="Confirm New Password",
                              height=40, fg_color=C["card"], border_color=C["border"],
                              text_color=C["text"], font=("Consolas", 12))
        conf_p.pack(padx=14, pady=(0, 12), fill="x")

        status_lbl = ctk.CTkLabel(st, text="", font=("Consolas", 11), text_color=C["error"])
        status_lbl.pack()

        def save():
            if not bcrypt.checkpw(curr_p.get().encode(),
                                  self.profile["password_hash"].encode()):
                status_lbl.configure(text="✗  AUTHENTICATION FAILED", text_color=C["error"])
                return
            if new_p.get() and new_p.get() != conf_p.get():
                status_lbl.configure(text="✗  PASSWORDS DO NOT MATCH", text_color=C["error"])
                return
            name   = name_in.get() or self.profile["admin_name"]
            p_hash = self.profile["password_hash"]
            if new_p.get():
                p_hash = bcrypt.hashpw(new_p.get().encode(), bcrypt.gensalt()).decode()
                global SESSION_KEY
                SESSION_KEY = CryptEngine.derive_key(new_p.get())
                update_log("SESSION KEY UPDATED WITH NEW PASSWORD.", C["warning"])
            save_profile(name, p_hash)
            self.profile = load_profile()
            status_lbl.configure(text="✓  PROFILE UPDATED", text_color=C["success"])
            st.after(1400, st.destroy)

        ctk.CTkButton(st, text="[ SAVE CHANGES ]", height=46,
                      fg_color=C["accent_dim"], hover_color=C["accent"],
                      text_color="white", font=("Consolas", 13, "bold"), corner_radius=8,
                      command=save).pack(pady=18, padx=30, fill="x")

    # ── Export log ───────────────────────────────
    def export_log(self):
        default = f"vortex_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        fpath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=default,
        )
        if not fpath:
            return
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("VORTEX-CRYPT PHANTOM — AUDIT LOG EXPORT\n")
            f.write(f"Exported : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Operator : {self.profile['admin_name']}\n")
            f.write("=" * 62 + "\n\n")
            for line in LOG_ENTRIES:
                f.write(line.strip() + "\n")
        messagebox.showinfo("EXPORTED", f"Audit log saved to:\n{fpath}")
        update_log(f"LOG EXPORTED → {os.path.basename(fpath)}", C["info"])

    # ── Processing ───────────────────────────────
    def _start_process(self, mode: str):
        if self.is_processing:
            messagebox.showwarning("BUSY", "A process is already running!")
            return
        if not file_queue:
            messagebox.showwarning("EMPTY", "No files in queue!")
            return
        threading.Thread(target=self._process, args=(mode,), daemon=True).start()

    def _process(self, mode: str):
        self.is_processing = True
        f_engine = Fernet(SESSION_KEY)
        start_t  = time.time()
        total    = len(file_queue)
        ok = fail = skip = 0
        label    = "ENCRYPTING" if mode == "enc" else "DECRYPTING"
        update_log(f"{label} {total} FILE(S)…", C["accent_glow"])

        for i, item in enumerate(list(file_queue)):
            path = item["path"]
            try:
                if mode == "enc":
                    if path.endswith(CRYPT_EXT):
                        update_log(f"SKIP (already encrypted): {os.path.basename(path)}",
                                   C["warning"])
                        skip += 1
                        continue
                    out_path = path + CRYPT_EXT
                else:
                    if not path.endswith(CRYPT_EXT):
                        update_log(f"SKIP (not .crypt): {os.path.basename(path)}",
                                   C["warning"])
                        skip += 1
                        continue
                    out_path = path[: -len(CRYPT_EXT)]

                with open(path, "rb") as f:
                    data = f.read()

                result = f_engine.encrypt(data) if mode == "enc" else f_engine.decrypt(data)

                with open(out_path, "wb") as f:
                    f.write(result)

                secure_delete(path)
                ok += 1

                pct     = (i + 1) / total
                elapsed = max(time.time() - start_t, 0.01)
                speed   = (item["size"] / 1_048_576) / elapsed   # MB/s

                self.after(0, lambda p=pct, s=speed, n=i+1:
                           self._ui_progress(p, s, n, total))
                self.after(0, lambda p=path: self._ui_mark(p, "done"))
                update_log(f"✓  {os.path.basename(out_path)}", C["success"])

            except Exception as ex:
                fail += 1
                self.after(0, lambda p=path: self._ui_mark(p, "fail"))
                update_log(f"✗  FAIL:  {os.path.basename(path)}  ——  {str(ex)[:50]}",
                           C["error"])

        elapsed_total = time.time() - start_t
        summary = (f"COMPLETE  ——  ✓ {ok} OK  |  ✗ {fail} FAILED  |  "
                   f"⊘ {skip} SKIPPED  |  {elapsed_total:.2f}s")
        update_log(summary, C["accent_glow"])
        self.after(0, lambda: self.sp_val.configure(
            text=f"QUEUED: {len(file_queue)}  |  STATUS: IDLE"))
        self.after(0, lambda: self._pb_label.configure(
            text=f"COMPLETE  —  {ok}/{total} OK"))
        self.is_processing = False

    def _ui_progress(self, pct, speed, current, total):
        self.pb.set(pct)
        self._pb_pct.configure(text=f"{int(pct * 100)}%")
        self._pb_label.configure(text=f"PROCESSING {current}/{total}  |  {speed:.2f} MB/s")
        self.sp_val.configure(
            text=f"PROCESSING: {current}/{total}  |  {speed:.2f} MB/s")

    def _ui_mark(self, path: str, status: str):
        key = f"{path}__status"
        if key in ui_elements:
            if status == "done":
                ui_elements[key].configure(text="✓ DONE", text_color=C["success"])
                if path in ui_elements:
                    ui_elements[path].configure(border_color=C["success"])
            elif status == "fail":
                ui_elements[key].configure(text="✗ FAILED", text_color=C["error"])
                if path in ui_elements:
                    ui_elements[path].configure(border_color=C["error"])


# ─────────────────────────────────────────────
if __name__ == "__main__":
    MainApp().mainloop()
