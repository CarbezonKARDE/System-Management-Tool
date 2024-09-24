import time
import os
import shutil
import threading

class BackupCore:
    def __init__(self, log_callback):
        self.backup_process = None
        self.backup_running = False
        self.log_callback = log_callback  # Function to log messages in the GUI

    def log_message(self, message):
        if self.log_callback:
            self.log_callback(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}")

    def backup(self, source_dir, dest_dir):
        self.log_message(f"Backing up from {source_dir} to {dest_dir}")

        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        backups = sorted(
            [f for f in os.listdir(dest_dir) if os.path.isdir(os.path.join(dest_dir, f))],
            key=lambda x: os.path.getctime(os.path.join(dest_dir, x))
        )

        if len(backups) >= 10:
            oldest_backup = backups[0]
            oldest_backup_path = os.path.join(dest_dir, oldest_backup)
            self.log_message(f"Deleting oldest backup: {oldest_backup}")
            shutil.rmtree(oldest_backup_path)

        timestamp = time.strftime("%Y%m%d%H%M%S")
        try:
            new_backup_path = os.path.join(dest_dir, f"backup_{timestamp}")
            shutil.copytree(source_dir, new_backup_path)
            self.log_message(f"Backup successful: {new_backup_path}")
        except Exception as e:
            self.log_message(f"Backup failed: {str(e)}")

    def run_backup(self, source_dir, dest_dir, interval_seconds):
        self.backup_running = True
        self.log_message("Backup process started")
        while self.backup_running:
            self.backup(source_dir, dest_dir)
            time.sleep(interval_seconds)

    def stop_backup(self):
        if self.backup_running:
            self.backup_running = False
            self.log_message("Stopping backup process...")
        else:
            self.log_message("No backup process is currently running.")

    def start_backup_thread(self, source_dir, dest_dir, interval_seconds):
        if self.backup_process and self.backup_process.is_alive():
            self.log_message("Backup process is already running!")
            return

        self.backup_process = threading.Thread(target=self.run_backup, args=(source_dir, dest_dir, interval_seconds))
        self.backup_process.start()
        self.log_message(f"Backup scheduled for every {interval_seconds} seconds.")
