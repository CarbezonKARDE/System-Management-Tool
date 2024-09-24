import customtkinter as ctk
import threading
import queue
import time
from tkinter import ttk, filedialog, messagebox
from tkinter import font as tkfont
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Import necessary functions and classes from core files
from Memory_Scanner_Module import *
from Task_Manager_Module import *
from Backup_Scheduler_Module import *

class IntegratedGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("System Management Tool")
        self.geometry("1200x800")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.tab_control = ctk.CTkTabview(self)
        self.tab_memory = self.tab_control.add("Memory Scanner")
        self.tab_task = self.tab_control.add("Task Manager")
        self.tab_backup = self.tab_control.add("Backup Scheduler")
        self.tab_control.pack(expand=1, fill='both', padx=10, pady=10)

        self.setup_memory_scanner_tab()
        self.setup_task_manager_tab()
        self.setup_backup_scheduler_tab()

    def setup_memory_scanner_tab(self):
        self.memory_frame = ctk.CTkFrame(self.tab_memory)
        self.memory_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.scan_button = ctk.CTkButton(self.memory_frame, text="Start Scan", command=self.start_memory_scan)
        self.scan_button.pack(pady=20)

        self.progress_text = ctk.CTkTextbox(self.memory_frame, height=200, state="disabled")
        self.progress_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.progress_bar = ctk.CTkProgressBar(self.memory_frame)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 20))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self.memory_frame, text="Ready to scan")
        self.status_label.pack(pady=(0, 20))

        self.memory_queue = queue.Queue()
        self.memory_core = MemoryScannerCore(self.memory_queue)

    def setup_task_manager_tab(self):
        self.task_frame = ctk.CTkFrame(self.tab_task)
        self.task_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Task Manager Treeview setup
        large_font = tkfont.Font(family="Helvetica", size=12)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", fieldbackground="#2b2b2b", foreground="white", font=large_font)
        style.configure("Treeview.Heading", background="#1f1f1f", foreground="white", font=large_font)

        self.tree = ttk.Treeview(self.task_frame, columns=('Process Name', 'CPU Usage', 'Power Consumption', 'Disk Read (MB/s)', 'Disk Write (MB/s)'), show="headings")
        self.tree.heading('Process Name', text='Name')
        self.tree.heading('CPU Usage', text='CPU')
        self.tree.heading('Power Consumption', text='Power Usage')
        self.tree.heading('Disk Read (MB/s)', text='Disk Read (MB/s)')
        self.tree.heading('Disk Write (MB/s)', text='Disk Write (MB/s)')

        self.tree.column('Process Name', width=300, anchor='w')
        self.tree.column('CPU Usage', width=100, anchor='center')
        self.tree.column('Power Consumption', width=150, anchor='center')
        self.tree.column('Disk Read (MB/s)', width=150, anchor='center')
        self.tree.column('Disk Write (MB/s)', width=150, anchor='center')

        self.tree.tag_configure('high_cpu', foreground='red')
        self.tree.tag_configure('custom_font', font=large_font)
        self.tree.tag_configure('total_row', background='#1f1f1f')
        self.tree.pack(expand=True, fill='both', padx=10, pady=10)

        # Graph setup
        graph_frame = ctk.CTkFrame(self.task_frame)
        graph_frame.pack(expand=True, fill='both', padx=10, pady=10)

        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.fig.patch.set_facecolor('#2b2b2b')
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(side=ctk.LEFT, expand=True, fill='both')

        btn_frame = ctk.CTkFrame(graph_frame)
        btn_frame.pack(side=ctk.RIGHT, fill=ctk.Y, padx=10)

        btn_cpu = ctk.CTkButton(btn_frame, text="CPU", command=lambda: self.set_graph_type("CPU"))
        btn_read = ctk.CTkButton(btn_frame, text="Disk Read", command=lambda: self.set_graph_type("Disk Read"))
        btn_write = ctk.CTkButton(btn_frame, text="Disk Write", command=lambda: self.set_graph_type("Disk Write"))

        btn_cpu.pack(pady=10)
        btn_read.pack(pady=10)
        btn_write.pack(pady=10)

        self.current_graph = "CPU"

    def setup_backup_scheduler_tab(self):
        self.backup_frame = ctk.CTkFrame(self.tab_backup)
        self.backup_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title = ctk.CTkLabel(self.backup_frame, text="Backup Scheduler", font=("Roboto", 24))
        title.pack(pady=10)

        self.source_entry = self.create_directory_input(self.backup_frame, "Source Directory:", self.browse_source)
        self.destination_entry = self.create_directory_input(self.backup_frame, "Destination Directory:", self.browse_destination)

        interval_frame = ctk.CTkFrame(self.backup_frame)
        interval_frame.pack(pady=10, fill="x")

        interval_label = ctk.CTkLabel(interval_frame, text="Backup Interval (seconds):")
        interval_label.pack(side="left", padx=10)

        self.interval_entry = ctk.CTkEntry(interval_frame, width=100)
        self.interval_entry.pack(side="left", padx=10)

        button_frame = ctk.CTkFrame(self.backup_frame)
        button_frame.pack(pady=20, fill="x")

        start_button = ctk.CTkButton(button_frame, text="Start Backup", command=self.start_backup_thread, fg_color="green", hover_color="dark green")
        start_button.pack(side="left", padx=10, expand=True)

        stop_button = ctk.CTkButton(button_frame, text="Stop Backup", command=self.stop_backup, fg_color="red", hover_color="dark red")
        stop_button.pack(side="right", padx=10, expand=True)

        log_label = ctk.CTkLabel(self.backup_frame, text="Backup Log:", font=("Roboto", 16))
        log_label.pack(pady=(20, 5))

        self.log_area = ctk.CTkTextbox(self.backup_frame, height=150, width=600, state="disabled")
        self.log_area.pack(pady=10, padx=10, fill="both", expand=True)

        self.backup_core = BackupCore(self.log_message)

    # Memory Scanner methods
    def start_memory_scan(self):
        self.scan_button.configure(state="disabled")
        self.progress_text.configure(state="normal")
        self.progress_text.delete("1.0", ctk.END)
        self.progress_text.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_label.configure(text="Scanning...")

        thread = threading.Thread(target=self.memory_core.scan_memory)
        thread.start()

        self.after(100, self.check_memory_queue)

    def check_memory_queue(self):
        try:
            while True:
                message = self.memory_queue.get_nowait()
                if message == "SCAN_COMPLETE":
                    self.scan_button.configure(state="normal")
                    self.status_label.configure(text="Scan complete")
                    self.progress_bar.set(1)
                    return
                elif isinstance(message, tuple) and message[0] == "PROGRESS":
                    self.progress_bar.set(message[1])
                else:
                    self.update_progress_text(message)
        except queue.Empty:
            self.after(100, self.check_memory_queue)

    def update_progress_text(self, message):
        self.progress_text.configure(state="normal")
        self.progress_text.insert(ctk.END, message + "\n")
        self.progress_text.see(ctk.END)
        self.progress_text.configure(state="disabled")

    # Task Manager methods
    def update_process_view(self):
        processes, total_cpu_percent, total_read_rate, total_write_rate = update_process_info()

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.tree.insert('', 'end', values=("Total", f"{total_cpu_percent:.2f}%", "", f"{total_read_rate:.2f} MB/s", f"{total_write_rate:.2f} MB/s"), tags=('custom_font', 'total_row'))

        for process in processes:
            process_name, cpu_percent, power_consumption, read_rate, write_rate = process
            values = (process_name, f"{cpu_percent:.2f}%", power_consumption, read_rate, write_rate)
            tags = ('high_cpu', 'custom_font') if cpu_percent > 20 else ('custom_font',)
            self.tree.insert('', 'end', values=values, tags=tags)

    def plot_graph(self):
        self.ax.clear()
        if self.current_graph == "CPU":
            self.ax.plot(cpu_percent_data[-30:], label="CPU Usage (%)", color="#1f77b4")
            self.ax.set_title("CPU Usage Over Time")
            self.ax.set_ylabel("CPU Usage (%)")
        elif self.current_graph == "Disk Read":
            self.ax.plot(disk_read_data[-30:], label="Disk Read (MB/s)", color="#2ca02c")
            self.ax.set_title("Disk Read Rate Over Time")
            self.ax.set_ylabel("Read Rate (MB/s)")
        elif self.current_graph == "Disk Write":
            self.ax.plot(disk_write_data[-30:], label="Disk Write (MB/s)", color="#d62728")
            self.ax.set_title("Disk Write Rate Over Time")
            self.ax.set_ylabel("Write Rate (MB/s)")

        self.ax.set_xlabel("Time (s)")
        self.ax.legend()
        self.ax.set_facecolor("#2b2b2b")
        self.ax.tick_params(colors='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.title.set_color('white')
        self.canvas.draw()

    def set_graph_type(self, graph_type):
        self.current_graph = graph_type
        self.plot_graph()

    # Backup Scheduler methods
    def create_directory_input(self, parent, label_text, browse_command):
        frame = ctk.CTkFrame(parent)
        frame.pack(pady=10, fill="x")

        label = ctk.CTkLabel(frame, text=label_text)
        label.pack(side="left", padx=10)

        entry = ctk.CTkEntry(frame, width=400)
        entry.pack(side="left", padx=10)

        browse_button = ctk.CTkButton(frame, text="Browse", command=browse_command)
        browse_button.pack(side="right", padx=10)

        return entry

    def browse_source(self):
        self.browse_directory(self.source_entry)

    def browse_destination(self):
        self.browse_directory(self.destination_entry)

    def browse_directory(self, entry):
        directory = filedialog.askdirectory()
        if directory:
            entry.delete(0, "end")
            entry.insert(0, directory)

    def log_message(self, message):
        self.log_area.configure(state="normal")
        self.log_area.insert("end", f"{message}\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def stop_backup(self):
        self.backup_core.stop_backup()

    def start_backup_thread(self):
        source_dir = self.source_entry.get()
        dest_dir = self.destination_entry.get()

        try:
            interval_seconds = int(self.interval_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for the backup interval.")
            return

        if not os.path.exists(source_dir):
            messagebox.showerror("Error", "Source directory does not exist!")
            return
        if not os.path.exists(dest_dir):
            messagebox.showerror("Error", "Destination directory does not exist!")
            return

        self.backup_core.start_backup_thread(source_dir, dest_dir, interval_seconds)

    def run(self):
        # Start update thread for process view
        threading.Thread(target=self.start_update_thread, daemon=True).start()

        # Start automatic graph update
        self.after(1000, self.auto_update_graph)

        self.mainloop()

    def start_update_thread(self):
        while True:
            self.update_process_view()
            time.sleep(1)

    def auto_update_graph(self):
        self.plot_graph()
        self.after(1000, self.auto_update_graph)

if __name__ == "__main__":
    app = IntegratedGUI()
    app.run()