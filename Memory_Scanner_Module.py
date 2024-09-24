import sqlite3
import hashlib
import ctypes
import psutil

class MemoryScannerCore:
    def __init__(self, queue):
        self.queue = queue

    def connect_to_database(self):
        conn = sqlite3.connect('hash_database.db')
        cursor = conn.cursor()
        return conn, cursor

    def compute_memory_hash(self, memory_block, hash_algorithm='sha256'):
        hash_func = getattr(hashlib, hash_algorithm)()
        hash_func.update(memory_block)
        return hash_func.hexdigest()

    def is_malicious(self, memory_hash, cursor):
        cursor.execute('SELECT * FROM hash_database WHERE hash_value=?', (memory_hash,))
        result = cursor.fetchone()
        return result is not None

    def read_memory(self, process_handle, address, size):
        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t()
        if not ctypes.windll.kernel32.ReadProcessMemory(process_handle, address, buffer, size, ctypes.byref(bytes_read)):
            raise ctypes.WinError()
        return buffer.raw

    def get_memory_regions(self, process_handle):
        class MEMORY_BASIC_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BaseAddress", ctypes.c_void_p),
                ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", ctypes.c_ulong),
                ("RegionSize", ctypes.c_size_t),
                ("State", ctypes.c_ulong),
                ("Protect", ctypes.c_ulong),
                ("Type", ctypes.c_ulong)
            ]

        def query_virtual_memory(address):
            mbi = MEMORY_BASIC_INFORMATION()
            ctypes.windll.kernel32.VirtualQueryEx(process_handle, address, ctypes.byref(mbi), ctypes.sizeof(mbi))
            return mbi

        base_address = 0
        while True:
            mbi = query_virtual_memory(base_address)
            if mbi.RegionSize == 0:
                break
            if mbi.State == 0x1000:
                yield mbi.BaseAddress, mbi.RegionSize
            base_address = mbi.BaseAddress + mbi.RegionSize

    def scan_memory(self):
        conn, cursor = self.connect_to_database()
        malicious_found = False
        processes = list(psutil.process_iter(['pid', 'name']))
        total_processes = len(processes)
        processed_processes = 0

        for proc in processes:
            try:
                self.queue.put(f"Scanning process: {proc.info['name']} (PID: {proc.info['pid']})")
                process_handle = ctypes.windll.kernel32.OpenProcess(0x10 | 0x20, False, proc.info['pid'])  # PROCESS_VM_READ | PROCESS_QUERY_INFORMATION
                
                if not process_handle:
                    continue
                try:
                    memory_regions = list(self.get_memory_regions(process_handle))
                    total_regions = len(memory_regions)
                    for i, (base_address, region_size) in enumerate(memory_regions):
                        try:
                            memory_block = self.read_memory(process_handle, base_address, region_size)
                            file_hash = self.compute_memory_hash(memory_block, 'sha256')
                            
                            if self.is_malicious(file_hash, cursor):
                                self.queue.put(f"[ALERT] Malicious memory detected in process {proc.info['name']} (PID: {proc.info['pid']})")
                                malicious_found = True
                        
                        except Exception as e:
                            self.queue.put(f"Error reading memory from address {base_address}: {e}")
                        
                        # Update progress for each memory region
                        progress = (processed_processes + (i + 1) / total_regions) / total_processes
                        self.queue.put(("PROGRESS", progress))

                except Exception as e:
                    self.queue.put(f"Error scanning memory regions for process {proc.info['pid']}: {e}")

                ctypes.windll.kernel32.CloseHandle(process_handle)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

            processed_processes += 1

        if not malicious_found:
            self.queue.put("No malicious memory regions found.")
        
        conn.close()
        self.queue.put("SCAN_COMPLETE")
