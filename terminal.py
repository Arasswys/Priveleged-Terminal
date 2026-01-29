import os
import sys
import ctypes
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime

# Windows API
kernel32 = ctypes.windll.kernel32
advapi32 = ctypes.windll.advapi32

# Windows Constants
SE_PRIVILEGE_ENABLED = 0x00000002
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008
PROCESS_QUERY_INFORMATION = 0x0400

class LUID(ctypes.Structure):
    _fields_ = [
        ("LowPart", ctypes.c_ulong),
        ("HighPart", ctypes.c_long)
    ]

class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("Luid", LUID),
        ("Attributes", ctypes.c_ulong)
    ]

class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [
        ("PrivilegeCount", ctypes.c_ulong),
        ("Privileges", LUID_AND_ATTRIBUTES * 1)
    ]

class FullPrivilegeUnlocker:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ FULL PRIVILEGE UNLOCKER")
        self.root.geometry("1400x900")
        self.root.minsize(1300, 800)
        
        # Colors
        self.bg_color = "#0a0a0a"
        self.fg_color = "#00ff00"
        self.accent_color = "#0078d4"
        self.warning_color = "#ffb900"
        self.error_color = "#d13438"
        self.success_color = "#16c60c"
        self.disabled_color = "#666666"
        self.cmd_bg = "#1a1a1a"
        
        self.root.configure(bg=self.bg_color)
        
        # SENİN LİSTENDEN TÜM YETKİLER
        self.privileges = [
            ("SeIncreaseQuotaPrivilege", "Bellek kotaları ayarla"),
            ("SeSecurityPrivilege", "Denetim ve güvenlik günlüğünü yönet"),
            ("SeTakeOwnershipPrivilege", "Dosyaların sahipliğini al"),
            ("SeLoadDriverPrivilege", "Aygıt sürücüleri yükle"),
            ("SeSystemProfilePrivilege", "Sistem performans profili oluştur"),
            ("SeSystemtimePrivilege", "Sistem saatini değiştir"),
            ("SeProfileSingleProcessPrivilege", "Tek işlem profili oluştur"),
            ("SeIncreaseBasePriorityPrivilege", "Zamanlama önceliğini artır"),
            ("SeCreatePagefilePrivilege", "Disk belleği dosyası oluştur"),
            ("SeBackupPrivilege", "Dosya ve dizinleri yedekle"),
            ("SeRestorePrivilege", "Dosya ve dizinleri geri yükle"),
            ("SeShutdownPrivilege", "Sistemi kapat"),
            ("SeDebugPrivilege", "Programların hatalarını ayıkla"),
            ("SeSystemEnvironmentPrivilege", "Üretici yazılım ortam değerlerini değiştir"),
            ("SeChangeNotifyPrivilege", "Çapraz geçiş denetimini atla"),
            ("SeRemoteShutdownPrivilege", "Uzak sistemden kapatmayı zorla"),
            ("SeUndockPrivilege", "Bilgisayar takma biriminden çıkar"),
            ("SeManageVolumePrivilege", "Birim bakım görevleri gerçekleştir"),
            ("SeImpersonatePrivilege", "Kimlik doğrulamasından sonra istemcinin özelliklerini al"),
            ("SeCreateGlobalPrivilege", "Genel nesneler oluştur"),
            ("SeIncreaseWorkingSetPrivilege", "İşlem alma kümesini artır"),
            ("SeTimeZonePrivilege", "Saat dilimini değiştir"),
            ("SeCreateSymbolicLinkPrivilege", "Simgesel bağlantılar oluştur"),
            ("SeDelegateSessionUserImpersonatePrivilege", "Kimliğe bürünme belirteci edin"),
        ]
        
        self.privilege_status = {}
        self.privilege_labels = {}
        self.command_history = []
        self.history_index = -1
        
        self.build_ui()
        self.root.after(100, self.auto_start)
    
    def build_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame, text="⚡", 
                font=("Consolas", 28), 
                bg=self.bg_color, fg=self.accent_color).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Label(header_frame, text="FULL PRIVILEGE UNLOCKER", 
                font=("Consolas", 16, "bold"), 
                bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT)
        
        tk.Label(header_frame, text=f"Total Privileges: {len(self.privileges)}", 
                font=("Consolas", 10), 
                bg=self.bg_color, fg="#666666").pack(side=tk.RIGHT)
        
        # Status bar
        self.status_var = tk.StringVar(value="⚡ Initializing...")
        status_bar = tk.Label(main_frame, textvariable=self.status_var,
                             font=("Consolas", 10), 
                             bg="#1a1a1a", fg=self.fg_color,
                             anchor=tk.W, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Control panel
        control_frame = tk.Frame(main_frame, bg=self.bg_color)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Buttons
        self.scan_btn = tk.Button(control_frame, text="🔍 SCAN ALL PRIVILEGES",
                                 command=self.scan_all_privileges,
                                 bg="#0078d4", fg="white",
                                 font=("Consolas", 11, "bold"),
                                 relief=tk.RAISED,
                                 padx=15, pady=8)
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.enable_disabled_btn = tk.Button(control_frame, text="⚡ ENABLE ALL DISABLED",
                                           command=self.enable_all_disabled,
                                           bg="#16c60c", fg="white",
                                           font=("Consolas", 11, "bold"),
                                           relief=tk.RAISED,
                                           padx=15, pady=8,
                                           state=tk.DISABLED)
        self.enable_disabled_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Stats frame
        stats_frame = tk.Frame(control_frame, bg=self.bg_color)
        stats_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        self.enabled_var = tk.StringVar(value="Enabled: 0")
        self.disabled_var = tk.StringVar(value="Disabled: 0")
        
        tk.Label(stats_frame, textvariable=self.enabled_var,
                font=("Consolas", 10, "bold"),
                bg=self.bg_color, fg=self.success_color).pack(anchor=tk.E)
        
        tk.Label(stats_frame, textvariable=self.disabled_var,
                font=("Consolas", 10, "bold"),
                bg=self.bg_color, fg=self.error_color).pack(anchor=tk.E)
        
        # Main content area
        content_frame = tk.Frame(main_frame, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Privilege list (2 columns)
        left_panel = tk.Frame(content_frame, bg=self.bg_color)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        privilege_frame = tk.LabelFrame(left_panel, text=" 🔐 PRIVILEGE STATUS ",
                                       font=("Consolas", 11, "bold"),
                                       bg=self.bg_color, fg=self.accent_color,
                                       relief=tk.GROOVE)
        privilege_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create 2 columns
        columns_frame = tk.Frame(privilege_frame, bg=self.bg_color)
        columns_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left column
        left_column = tk.Frame(columns_frame, bg=self.bg_color)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Right column
        right_column = tk.Frame(columns_frame, bg=self.bg_color)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Split privileges between columns
        mid_index = len(self.privileges) // 2
        
        for i, (priv_name, priv_desc) in enumerate(self.privileges):
            # Choose column
            if i < mid_index:
                column = left_column
            else:
                column = right_column
            
            frame = tk.Frame(column, bg=self.bg_color)
            frame.pack(fill=tk.X, pady=2)
            
            # Status indicator
            status_canvas = tk.Canvas(frame, width=12, height=12, 
                                     bg=self.bg_color, highlightthickness=0)
            status_canvas.pack(side=tk.LEFT, padx=(0, 8))
            status_circle = status_canvas.create_oval(2, 2, 10, 10, fill="gray")
            
            # Privilege info
            info_frame = tk.Frame(frame, bg=self.bg_color)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            name_label = tk.Label(info_frame, text=priv_name,
                                 font=("Consolas", 9),
                                 bg=self.bg_color, fg=self.disabled_color)
            name_label.pack(anchor=tk.W)
            
            status_label = tk.Label(info_frame, text="Checking...",
                                   font=("Consolas", 8),
                                   bg=self.bg_color, fg="#888888")
            status_label.pack(anchor=tk.W)
            
            # Store references
            self.privilege_labels[priv_name] = {
                'canvas': status_canvas,
                'circle': status_circle,
                'name_label': name_label,
                'status_label': status_label
            }
        
        # Right panel - Terminal
        right_panel = tk.Frame(content_frame, bg=self.bg_color)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        terminal_frame = tk.LabelFrame(right_panel, text=" 💻 PRIVILEGED TERMINAL ",
                                      font=("Consolas", 11, "bold"),
                                      bg=self.bg_color, fg=self.success_color,
                                      relief=tk.GROOVE)
        terminal_frame.pack(fill=tk.BOTH, expand=True)
        
        # Command input
        cmd_frame = tk.Frame(terminal_frame, bg=self.cmd_bg)
        cmd_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(cmd_frame, text="Command:", 
                font=("Consolas", 10),
                bg=self.cmd_bg, fg=self.fg_color).pack(side=tk.LEFT, padx=(0, 10))
        
        self.cmd_entry = tk.Entry(cmd_frame,
                                 font=("Consolas", 10),
                                 bg="#2a2a2a", fg=self.fg_color,
                                 insertbackground=self.fg_color,
                                 relief=tk.SUNKEN,
                                 width=40)
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.cmd_entry.bind("<Return>", lambda e: self.execute_command())
        self.cmd_entry.bind("<Up>", lambda e: self.navigate_history(-1))
        self.cmd_entry.bind("<Down>", lambda e: self.navigate_history(1))
        
        execute_btn = tk.Button(cmd_frame, text="▶ EXECUTE",
                               command=self.execute_command,
                               bg=self.success_color, fg="white",
                               font=("Consolas", 10, "bold"),
                               relief=tk.RAISED,
                               padx=12, pady=4)
        execute_btn.pack(side=tk.RIGHT)
        
        # Quick commands
        quick_frame = tk.Frame(terminal_frame, bg=self.cmd_bg)
        quick_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(quick_frame, text="Quick:", 
                font=("Consolas", 9),
                bg=self.cmd_bg, fg="#aaaaaa").pack(side=tk.LEFT, padx=(0, 10))
        
        quick_cmds = [
            ("whoami /priv", "Priv"),
            ("tasklist", "Procs"),
            ("sc query", "Services"),
            ("net user", "Users"),
            ("dir", "Dir"),
        ]
        
        for cmd, label in quick_cmds:
            btn = tk.Button(quick_frame, text=label,
                          command=lambda c=cmd: self.insert_command(c),
                          bg="#333333", fg="#cccccc",
                          font=("Consolas", 8),
                          relief=tk.FLAT,
                          padx=6, pady=2)
            btn.pack(side=tk.LEFT, padx=2)
        
        # Output area
        output_frame = tk.Frame(terminal_frame, bg="#0f0f0f")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.output_text = scrolledtext.ScrolledText(output_frame,
                                                    bg="#0f0f0f", fg=self.fg_color,
                                                    font=("Consolas", 9),
                                                    insertbackground=self.fg_color,
                                                    relief=tk.FLAT,
                                                    wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Welcome message
        self.output_text.insert(tk.END, "⚡ FULL PRIVILEGE UNLOCKER\n")
        self.output_text.insert(tk.END, "=" * 60 + "\n")
        self.output_text.insert(tk.END, f"Total Privileges: {len(self.privileges)}\n")
        self.output_text.insert(tk.END, "Scans and enables ALL disabled privileges\n")
        self.output_text.insert(tk.END, "Terminal runs with activated privileges\n")
        self.output_text.insert(tk.END, "=" * 60 + "\n\n")
        self.output_text.see(tk.END)
        
        # Footer
        footer_frame = tk.Frame(main_frame, bg=self.bg_color)
        footer_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(footer_frame, text="⚡ Unlocks ALL disabled Windows privileges | Terminal with active privileges",
                font=("Consolas", 9), 
                bg=self.bg_color, fg=self.accent_color).pack(side=tk.LEFT)
    
    def auto_start(self):
        """Otomatik başlatma"""
        self.log_message("=== FULL PRIVILEGE UNLOCKER ===")
        self.log_message("Initializing system...")
        
        # Admin kontrolü
        is_admin = self.verify_admin_status()
        
        if not is_admin:
            self.log_message("❌ CRITICAL: Not running as Administrator!")
            self.status_var.set("❌ ERROR: Run as Administrator required!")
            
            response = messagebox.askyesno("Admin Required", 
                "This program MUST run with Administrator privileges!\n\n"
                "Do you want to restart as Administrator now?")
            
            if response:
                self.restart_as_admin()
            return
        
        self.log_message("✅ Running as Administrator")
        self.status_var.set("✅ Ready - Running as Administrator")
        self.scan_btn.config(state=tk.NORMAL)
        
        # Otomatik tarama
        self.root.after(500, self.scan_all_privileges)
    
    def restart_as_admin(self):
        """Administrator olarak yeniden başlat"""
        try:
            script = sys.executable
            params = ' '.join([f'"{arg}"' for arg in sys.argv])
            
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", script, params, None, 1
            )
            
            self.root.after(1000, self.root.destroy)
            
        except Exception as e:
            self.log_message(f"❌ Failed to restart as admin: {str(e)}")
            messagebox.showerror("Fatal Error",
                "Cannot restart as Administrator!\n\n"
                "Please manually right-click and select 'Run as administrator'")
    
    def verify_admin_status(self):
        """Admin olup olmadığını kontrol et"""
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            return is_admin
        except:
            return False
    
    def log_message(self, message):
        """Log'a mesaj ekle"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_line = f"[{timestamp}] {message}\n"
            
            self.output_text.insert(tk.END, log_line)
            self.output_text.see(tk.END)
            self.root.update_idletasks()
        except:
            pass
    
    def run_command_safe(self, cmd, timeout=5):
        """Komut çalıştır"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                timeout=timeout,
                startupinfo=startupinfo,
                encoding='utf-8',
                errors='ignore'
            )
            
            return result
        except subprocess.TimeoutExpired:
            self.log_message(f"⚠️ Command timeout: {cmd[:50]}...")
            return None
        except Exception as e:
            self.log_message(f"⚠️ Command error: {str(e)}")
            return None
    
    def get_last_error_message(self):
        """Son Windows hata mesajını al"""
        error_code = kernel32.GetLastError()
        if error_code:
            buf = ctypes.create_unicode_buffer(1024)
            kernel32.FormatMessageW(
                0x1000, None, error_code, 0, buf, 1024, None
            )
            return f"Error {error_code}: {buf.value.strip()}"
        return "No error"
    
    def enable_privilege(self, privilege_name):
        """Windows privilege'ını etkinleştir"""
        try:
            self.log_message(f"Enabling {privilege_name}...")
            
            # Process handle al
            process_id = kernel32.GetCurrentProcessId()
            process_handle = kernel32.OpenProcess(
                PROCESS_QUERY_INFORMATION,
                False,
                process_id
            )
            
            if not process_handle:
                self.log_message(f"❌ OpenProcess failed: {self.get_last_error_message()}")
                return False
            
            # Token al
            token = ctypes.c_void_p()
            TOKEN_RIGHTS = TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY
            
            if not advapi32.OpenProcessToken(
                process_handle,
                TOKEN_RIGHTS,
                ctypes.byref(token)
            ):
                kernel32.CloseHandle(process_handle)
                self.log_message(f"❌ OpenProcessToken failed: {self.get_last_error_message()}")
                return False
            
            # Privilege value bul
            luid = LUID()
            if not advapi32.LookupPrivilegeValueW(
                None,
                ctypes.c_wchar_p(privilege_name),
                ctypes.byref(luid)
            ):
                kernel32.CloseHandle(process_handle)
                kernel32.CloseHandle(token)
                self.log_message(f"❌ LookupPrivilegeValue failed: {self.get_last_error_message()}")
                return False
            
            # Privilege ayarla
            tp = TOKEN_PRIVILEGES()
            tp.PrivilegeCount = 1
            tp.Privileges[0].Luid = luid
            tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED
            
            previous_state = TOKEN_PRIVILEGES()
            return_length = ctypes.c_ulong()
            
            if not advapi32.AdjustTokenPrivileges(
                token,
                False,
                ctypes.byref(tp),
                ctypes.sizeof(tp),
                ctypes.byref(previous_state),
                ctypes.byref(return_length)
            ):
                kernel32.CloseHandle(process_handle)
                kernel32.CloseHandle(token)
                self.log_message(f"❌ AdjustTokenPrivileges failed: {self.get_last_error_message()}")
                return False
            
            # Hata kontrolü
            error_code = kernel32.GetLastError()
            
            # Handle'ları kapat
            kernel32.CloseHandle(process_handle)
            kernel32.CloseHandle(token)
            
            if error_code != 0:
                self.log_message(f"❌ Failed to enable {privilege_name}: Error {error_code}")
                return False
            
            self.log_message(f"✅ {privilege_name} enabled successfully")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Error enabling {privilege_name}: {str(e)}")
            return False
    
    def check_privilege_status(self, privilege_name):
        """Tek bir yetkinin durumunu kontrol et"""
        try:
            cmd = 'whoami /priv'
            result = self.run_command_safe(cmd, timeout=5)
            
            if result and result.returncode == 0:
                for line in result.stdout.split('\n'):
                    line_lower = line.lower()
                    priv_lower = privilege_name.lower()
                    
                    if priv_lower in line_lower:
                        if "enabled" in line_lower:
                            return True, "Enabled"
                        else:
                            return False, "Disabled"
            
            return False, "Not Found"
            
        except Exception as e:
            return False, "Error"
    
    def scan_all_privileges(self):
        """Tüm yetkileri tarar"""
        self.log_message("=== SCANNING ALL PRIVILEGES ===")
        
        self.scan_btn.config(state=tk.DISABLED, text="⏳ SCANNING...")
        self.enable_disabled_btn.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=self._scan_all_privileges_thread)
        thread.daemon = True
        thread.start()
    
    def _scan_all_privileges_thread(self):
        """Thread içinde tüm yetkileri tara"""
        try:
            enabled_count = 0
            disabled_count = 0
            
            for priv_name, priv_desc in self.privileges:
                is_enabled, status_text = self.check_privilege_status(priv_name)
                self.privilege_status[priv_name] = is_enabled
                
                self.root.after(0, self._update_privilege_ui, priv_name, is_enabled, status_text)
                
                if is_enabled:
                    enabled_count += 1
                else:
                    disabled_count += 1
                
                status_icon = "✅" if is_enabled else "❌"
                self.root.after(0, self.log_message, f"{status_icon} {priv_name}: {status_text}")
                
                time.sleep(0.1)
            
            # Update stats
            self.root.after(0, self._update_stats, enabled_count, disabled_count)
            
            if disabled_count > 0:
                self.root.after(0, self.enable_disabled_btn.config, {'state': tk.NORMAL})
            
        except Exception as e:
            self.root.after(0, self.log_message, f"❌ Scan error: {str(e)}")
        
        finally:
            self.root.after(0, self.scan_btn.config, {'state': tk.NORMAL, 'text': '🔍 SCAN ALL PRIVILEGES'})
    
    def _update_privilege_ui(self, priv_name, is_enabled, status_text):
        """UI'ı güncelle"""
        if priv_name in self.privilege_labels:
            label_info = self.privilege_labels[priv_name]
            
            if is_enabled:
                label_info['canvas'].itemconfig(label_info['circle'], fill=self.success_color)
                label_info['name_label'].config(fg=self.success_color)
                label_info['status_label'].config(text=f"✓ {status_text}", fg=self.success_color)
            else:
                label_info['canvas'].itemconfig(label_info['circle'], fill=self.error_color)
                label_info['name_label'].config(fg=self.error_color)
                label_info['status_label'].config(text=f"✗ {status_text}", fg=self.error_color)
    
    def _update_stats(self, enabled_count, disabled_count):
        """İstatistikleri güncelle"""
        self.enabled_var.set(f"Enabled: {enabled_count}")
        self.disabled_var.set(f"Disabled: {disabled_count}")
        
        total = enabled_count + disabled_count
        self.status_var.set(f"✅ Scan Complete: {enabled_count}/{total} enabled")
        
        self.log_message(f"=== SCAN COMPLETE: {enabled_count}/{total} privileges enabled ===")
        
        if disabled_count > 0:
            self.log_message(f"⚠️ {disabled_count} privileges are disabled and can be enabled")
    
    def enable_all_disabled(self):
        """Tüm disabled yetkileri etkinleştir"""
        disabled_privileges = []
        
        for priv_name, _ in self.privileges:
            if priv_name in self.privilege_status and not self.privilege_status[priv_name]:
                disabled_privileges.append(priv_name)
        
        if not disabled_privileges:
            self.log_message("✅ All privileges are already enabled!")
            return
        
        self.log_message(f"=== ENABLING {len(disabled_privileges)} DISABLED PRIVILEGES ===")
        
        self.enable_disabled_btn.config(state=tk.DISABLED, text="⏳ ENABLING...")
        
        thread = threading.Thread(target=self._enable_all_disabled_thread, args=(disabled_privileges,))
        thread.daemon = True
        thread.start()
    
    def _enable_all_disabled_thread(self, disabled_privileges):
        """Thread içinde disabled yetkileri etkinleştir"""
        try:
            total = len(disabled_privileges)
            enabled_count = 0
            
            for priv_name in disabled_privileges:
                success = self.enable_privilege(priv_name)
                
                if success:
                    enabled_count += 1
                    self.root.after(0, self._update_privilege_ui, priv_name, True, "Enabled")
                else:
                    self.root.after(0, self._update_privilege_ui, priv_name, False, "Failed")
                
                time.sleep(0.2)
            
            self.root.after(0, self.log_message, f"=== ENABLEMENT COMPLETE: {enabled_count}/{total} privileges enabled ===")
            
            if enabled_count == total:
                self.root.after(0, self.log_message, "🎉 SUCCESS: All disabled privileges enabled!")
                self.root.after(0, lambda: self.status_var.set("✅ All privileges enabled!"))
            else:
                self.root.after(0, self.log_message, f"⚠️ Partial: {enabled_count}/{total} privileges enabled")
                self.root.after(0, lambda: self.status_var.set(f"⚠️ {enabled_count}/{total} enabled"))
            
            self.root.after(2000, self.scan_all_privileges)
            
        except Exception as e:
            self.root.after(0, self.log_message, f"❌ Enablement error: {str(e)}")
        
        finally:
            self.root.after(0, self.enable_disabled_btn.config, {'state': tk.NORMAL, 'text': '⚡ ENABLE ALL DISABLED'})
    
    def execute_command(self):
        """Komutu çalıştır"""
        cmd = self.cmd_entry.get().strip()
        
        if not cmd:
            return
        
        # History
        if not self.command_history or self.command_history[-1] != cmd:
            self.command_history.append(cmd)
        self.history_index = -1
        
        # Clear entry
        self.cmd_entry.delete(0, tk.END)
        
        # Show command
        self.log_message(f"\n$ {cmd}")
        
        # Thread'de çalıştır
        thread = threading.Thread(target=self._execute_command_thread, args=(cmd,))
        thread.daemon = True
        thread.start()
    
    def _execute_command_thread(self, cmd):
        """Thread içinde komut çalıştır"""
        try:
            # Özel komutlar
            if cmd.lower() in ['clear', 'cls']:
                self.root.after(0, self.output_text.delete, 1.0, tk.END)
                return
            
            # Komutu çalıştır
            result = self.run_command_safe(cmd, timeout=30)
            
            # Sonuçları göster
            self.root.after(0, self._show_command_result, cmd, result)
            
        except Exception as e:
            self.root.after(0, self.log_message, f"❌ Command execution error: {str(e)}")
    
    def _show_command_result(self, cmd, result):
        """Komut sonucunu göster"""
        if result.stdout:
            self.output_text.insert(tk.END, result.stdout)
            if not result.stdout.endswith('\n'):
                self.output_text.insert(tk.END, '\n')
        
        if result.stderr:
            self.output_text.insert(tk.END, "STDERR:\n")
            self.output_text.insert(tk.END, result.stderr)
            if not result.stderr.endswith('\n'):
                self.output_text.insert(tk.END, '\n')
        
        if result.returncode != 0:
            self.output_text.insert(tk.END, f"\n[Exit Code: {result.returncode}]\n")
        
        self.output_text.see(tk.END)
    
    def insert_command(self, cmd):
        """Quick command'ı entry'ye ekle"""
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, cmd)
        self.cmd_entry.focus()
    
    def navigate_history(self, direction):
        """Command history'de gez"""
        if not self.command_history:
            return
        
        self.history_index += direction
        
        if self.history_index < 0:
            self.history_index = -1
            self.cmd_entry.delete(0, tk.END)
            return
        
        if self.history_index >= len(self.command_history):
            self.history_index = len(self.command_history) - 1
        
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, self.command_history[self.history_index])

def main():
    # Check if running as administrator
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
    
    if not is_admin:
        try:
            # Try to restart as admin
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
        except:
            messagebox.showerror("Error", 
                "This program requires Administrator privileges!\n\n"
                "Please right-click and select 'Run as administrator'")
        sys.exit(0)
    
    # Create window
    root = tk.Tk()
    
    # Set window icon if available
    try:
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
        else:
            icon_path = 'icon.ico'
        root.iconbitmap(default=icon_path)
    except:
        pass
    
    app = FullPrivilegeUnlocker(root)
    
    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()