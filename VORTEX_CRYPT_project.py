import os, bcrypt, base64, threading, time, json
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD 
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from datetime import datetime

CRYPT_EXT = ".crypt"
PROFILE_FILE = "profile.json"
DEFAULT_HASH = b'$2b$12$etosH4DNmrBEJ1C0CNzF1e.jJtlI97HeZiM2eQNAbrPcbzSCYaSmy'.decode() #use the bycrpt to make your hash of the password for the first login the default password is "admin"

file_queue = []
ui_elements = {}
SESSION_KEY = None

def load_profile():
    if not os.path.exists(PROFILE_FILE):
        data = {"admin_name": "admin", "password_hash": DEFAULT_HASH}
        with open(PROFILE_FILE, "w") as f: json.dump(data, f)
        return data
    with open(PROFILE_FILE, "r") as f: return json.load(f)

def save_profile(name, p_hash):
    with open(PROFILE_FILE, "w") as f:
        json.dump({"admin_name": name, "password_hash": p_hash}, f)

def secure_delete(filepath):
    try:
        with open(filepath, "ba+") as f:
            length = f.tell()
            f.seek(0)
            f.write(os.urandom(length))
        os.remove(filepath)
    except Exception:
        pass

class CryptEngine:
    @staticmethod
    def derive_key(password: str):
        salt = b'\x14\xab\xbc\x88\xfe\x01\x99\x22'
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def update_log(msg, color="#10b981"):
    if 'log' in ui_elements:
        ts = datetime.now().strftime('%H:%M:%S')
        lbl = ctk.CTkLabel(ui_elements['log'], text=f" >> {ts} | {msg}", font=("Consolas", 11), text_color=color, anchor="w")
        lbl.pack(fill="x", padx=10, pady=1)
        ui_elements['log']._parent_canvas.yview_moveto(1.0)


class MainApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        
        ctk.set_appearance_mode("dark")
        
        self.profile = load_profile()
        self.login_attempts = 0 
        self.title("VORTEX-CRYPT // DATA SECURE")
        self.geometry("1250x850")
        self.configure(bg="#020617")
        
      
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop_event)

        self.withdraw()
        self.run_auth()

    def handle_drop_event(self, event):
     
        if hasattr(self, 'queue_fm'):
            self.queue_fm.configure(border_color="#1e293b")
        self.handle_inj(event.data)

    def run_auth(self):
        self.login_attempts = 0
        self.auth = ctk.CTkToplevel(self)
        self.auth.geometry("450x550")
        self.auth.configure(fg_color="#020617")
        self.auth.protocol("WM_DELETE_WINDOW", self.quit)
        
        ctk.CTkLabel(self.auth, text="VORTEX-CRYPT", font=("Impact", 44), text_color="#10b981").pack(pady=(60,10))
        ctk.CTkLabel(self.auth, text=f"ACCESS FOR: {self.profile['admin_name'].upper()}", font=("Consolas", 12), text_color="#475569").pack()
        
        pwd_entry = ctk.CTkEntry(self.auth, show="*", width=320, height=50, placeholder_text="ENTER KEY", fg_color="#0f172a", border_color="#1e293b", font=("Consolas", 14))
        pwd_entry.pack(pady=40); pwd_entry.focus_force()
        
        def attempt_login():
            if bcrypt.checkpw(pwd_entry.get().encode(), self.profile['password_hash'].encode()):
                global SESSION_KEY
                SESSION_KEY = CryptEngine.derive_key(pwd_entry.get())
                self.auth.destroy(); self.deiconify(); self.build_ui()
            else:
                self.login_attempts += 1
                remaining = 3 - self.login_attempts
                if remaining > 0:
                    messagebox.showerror("DENIED", f"INVALID KEY. {remaining} ATTEMPTS REMAINING.")
                    pwd_entry.delete(0, 'end')
                else:
                    messagebox.showerror("TERMINATED", "TOO MANY FAILURES. SYSTEM LOCKING.")
                    self.quit()
        
        self.auth.bind('<Return>', lambda e: attempt_login())
        ctk.CTkButton(self.auth, text="[ INITIALIZE ]", fg_color="transparent", border_width=2, border_color="#10b981", text_color="#10b981", font=("Consolas", 14, "bold"), command=attempt_login).pack()

    def build_ui(self):
        nav = ctk.CTkFrame(self, height=90, fg_color="#020617", corner_radius=0, border_width=1, border_color="#0f172a")
        nav.pack(fill="x")
        ctk.CTkLabel(nav, text="VORTEX-CRYPT v1.0", font=("Impact", 32), text_color="#10b981").pack(pady=(15,0))
        self.sp_val = ctk.CTkLabel(nav, text="QUEUED: 0 ITEMS | STATUS: IDLE", font=("Consolas", 12), text_color="#64748b")
        self.sp_val.pack()

        body = ctk.CTkFrame(self, fg_color="transparent"); body.pack(fill="both", expand=True, padx=25, pady=20)
        
        side = ctk.CTkFrame(body, width=260, fg_color="#0b0f1a", corner_radius=12, border_width=1, border_color="#1e293b")
        side.pack(side="left", fill="y", padx=(0,20))
        
        ctk.CTkLabel(side, text="CONTROL PANEL", font=("Impact", 18), text_color="#475569").pack(pady=25)
        ctk.CTkButton(side, text="SETTINGS", fg_color="#334155", command=self.open_settings).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(side, text="ADD FOLDER", fg_color="#1e293b", command=lambda: self.handle_inj([filedialog.askdirectory()])).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(side, text="ADD FILES", fg_color="#1e293b", command=lambda: self.handle_inj(filedialog.askopenfilenames())).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(side, text="ENCRYPT ALL", fg_color="#065f46", command=lambda: threading.Thread(target=self.process, args=("enc",)).start()).pack(pady=(40,5), padx=20, fill="x")
        ctk.CTkButton(side, text="DECRYPT ALL", fg_color="#1e3a8a", command=lambda: threading.Thread(target=self.process, args=("dec",)).start()).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(side, text="LOGOUT", fg_color="#7f1d1d", command=self.logout).pack(side="bottom", pady=20, padx=20, fill="x")
        ctk.CTkButton(side, text="CLEAR QUEUE", fg_color="#991b1b", command=self.clear_queue).pack(side="bottom", pady=5, padx=20, fill="x")
        ctk.CTkButton(side, text="EXPORT LOG", fg_color="#3b82f6", command=self.export_log).pack(side="bottom", pady=5, padx=20, fill="x")

        grid = ctk.CTkFrame(body, fg_color="transparent"); grid.pack(side="right", fill="both", expand=True)
        
        
        self.queue_fm = ctk.CTkScrollableFrame(grid, label_text=" TARGET INJECTION ZONE ", fg_color="#000000", border_width=2, border_color="#1e293b")
        self.queue_fm.pack(fill="both", expand=True, pady=(0,15))
        
  
        self.queue_fm.bind('<<DragEnter>>', lambda e: self.queue_fm.configure(border_color="#10b981"))
        self.queue_fm.bind('<<DragLeave>>', lambda e: self.queue_fm.configure(border_color="#1e293b"))

        ui_elements['log'] = ctk.CTkScrollableFrame(grid, height=180, label_text=" SYSTEM AUDIT ", fg_color="#000000", border_width=1, border_color="#1e293b")
        ui_elements['log'].pack(fill="x")

        self.pb = ctk.CTkProgressBar(self, progress_color="#10b981", height=4); self.pb.pack(fill="x", side="bottom"); self.pb.set(0)

    def handle_inj(self, paths):
        if not paths or paths == ('',): return
        
        if isinstance(paths, str):
            paths = self.tk.splitlist(paths)
            
        for path in [p.strip('{}') for p in paths if os.path.exists(p.strip('{}'))]:
            if os.path.isdir(path):
                update_log(f"SCANNING: {os.path.basename(path)}", "#3b82f6")
                for root, _, files in os.walk(path):
                    for f in files: self.inject_single(os.path.join(root, f))
            else:
                self.inject_single(path)
        self.update_queue_status()

    def inject_single(self, path):
        if path not in file_queue:
            file_queue.append(path)
            row = ctk.CTkFrame(self.queue_fm, fg_color="#0f172a", border_width=1, border_color="#1e293b", corner_radius=6)
            row.pack(fill="x", padx=10, pady=4)
            ctk.CTkLabel(row, text=os.path.basename(path), font=("Segoe UI Semibold", 12)).pack(side="left", padx=15)
            ui_elements[path] = row

    def update_queue_status(self):
        self.sp_val.configure(text=f"QUEUED: {len(file_queue)} ITEMS | STATUS: READY")

    def clear_queue(self):
        file_queue.clear()
        for widget in self.queue_fm.winfo_children(): widget.destroy()
        self.update_queue_status()
        update_log("QUEUE PURGED.", "#ef4444")

    def logout(self):
        if messagebox.askyesno("LOGOUT", "Return to login screen?"):
            self.withdraw()
            for widget in self.winfo_children(): widget.destroy()
            self.run_auth()

    def open_settings(self):
        st = ctk.CTkToplevel(self); st.geometry("400x550"); st.configure(fg_color="#020617")
        ctk.CTkLabel(st, text="PROFILE SETTINGS", font=("Impact", 20), text_color="#10b981").pack(pady=20)
        name_in = ctk.CTkEntry(st, placeholder_text=f"Name: {self.profile['admin_name']}", width=300)
        name_in.pack(pady=10)
        curr_p = ctk.CTkEntry(st, show="*", placeholder_text="Current Password (Required)", width=300)
        curr_p.pack(pady=10)
        new_p = ctk.CTkEntry(st, show="*", placeholder_text="New Password (Optional)", width=300)
        new_p.pack(pady=10)
        def save():
            if bcrypt.checkpw(curr_p.get().encode(), self.profile['password_hash'].encode()):
                name = name_in.get() if name_in.get() else self.profile['admin_name']
                p_hash = self.profile['password_hash']
                if new_p.get(): p_hash = bcrypt.hashpw(new_p.get().encode(), bcrypt.gensalt()).decode()
                save_profile(name, p_hash)
                self.profile = load_profile()
                messagebox.showinfo("SUCCESS", "Profile Updated."); st.destroy()
            else: messagebox.showerror("ERROR", "Auth Failed")
        ctk.CTkButton(st, text="SAVE CHANGES", fg_color="#065f46", command=save).pack(pady=30)

    def export_log(self):
        with open("vortex_audit.txt", "a") as f:
            f.write(f"\n--- AUDIT LOG EXPORT: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            for widget in ui_elements['log'].winfo_children():
                f.write(widget.cget("text") + "\n")
        messagebox.showinfo("EXPORTED", "Audit saved to vortex_audit.txt")

    def process(self, mode):
        if not file_queue:
            messagebox.showwarning("EMPTY", "No files in queue!")
            return
        f_engine = Fernet(SESSION_KEY)
        start_t = time.time()
        for i, path in enumerate(list(file_queue)):
            try:
                out = path + CRYPT_EXT if mode == "enc" else path.replace(CRYPT_EXT, "")
                if (mode=="enc" and path.endswith(CRYPT_EXT)) or (mode=="dec" and not path.endswith(CRYPT_EXT)): continue
                with open(path, "rb") as f: data = f.read()
                res = f_engine.encrypt(data) if mode == "enc" else f_engine.decrypt(data)
                with open(out, "wb") as f: f.write(res)
                secure_delete(path)
                update_log(f"SUCCESS: {os.path.basename(out)}")
                self.pb.set((i+1)/len(file_queue))
                elapsed = max(time.time() - start_t, 0.1)
                self.sp_val.configure(text=f"PROCESSING: {i+1}/{len(file_queue)} | {(len(data)/1024/1024)/elapsed:.2f} MB/s")
            except Exception: update_log(f"FAIL: {os.path.basename(path)}", "#ef4444")
        self.sp_val.configure(text=f"QUEUED: {len(file_queue)} ITEMS | STATUS: IDLE")
        update_log("SEQUENCE FINISHED.")

if __name__ == "__main__":
    MainApp().mainloop()
