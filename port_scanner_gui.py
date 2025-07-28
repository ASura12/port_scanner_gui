import socket
import threading
import queue
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from concurrent.futures import ThreadPoolExecutor

# Queue for thread-safe GUI updates
update_queue = queue.Queue()

def scan_port(target, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.2)  # Fast timeout
        result = sock.connect_ex((target, port))
        if result == 0:
            update_queue.put(f"Port {port}: Open\n")
        sock.close()
    except Exception as e:
        update_queue.put(f"Error scanning port {port}: {e}\n")
    finally:
        update_queue.put("PROGRESS")

def process_queue():
    """Process updates from the queue safely in the Tkinter main loop."""
    while not update_queue.empty():
        msg = update_queue.get()
        if msg == "PROGRESS":
            progress.step(1)
        else:
            result_area.insert(tk.END, msg)
    root.after(50, process_queue)  # Keep checking the queue

def run_scan(target):
    start_port, end_port = 1, 1025  # Avoid port 0 (can cause hangs)
    total_ports = end_port - start_port + 1
    progress["value"] = 0
    progress["maximum"] = total_ports

    update_queue.put(f"Scanning {target} ({start_port}-{end_port})...\n")

    # ThreadPool: only 50 workers at a time for stability
    with ThreadPoolExecutor(max_workers=50) as executor:
        for port in range(start_port, end_port + 1):
            executor.submit(scan_port, target, port)

    update_queue.put("Scan complete!\n")

def start_scan(target):
    result_area.delete(1.0, tk.END)
    if not target:
        messagebox.showerror("Error", "Please enter a target IP")
        return
    # Run scan in background so GUI never blocks
    threading.Thread(target=run_scan, args=(target,), daemon=True).start()

# GUI Setup
root = tk.Tk()
root.title("Fast Port Scanner (No Freezing)")
root.geometry("500x500")

tk.Label(root, text="Enter Target IP:").pack(pady=5)
ip_entry = tk.Entry(root, width=30)
ip_entry.pack(pady=5)

scan_button = tk.Button(root, text="Start Scan", command=lambda: start_scan(ip_entry.get()))
scan_button.pack(pady=10)

progress = ttk.Progressbar(root, orient="horizontal", length=350, mode="determinate")
progress.pack(pady=10)

result_area = scrolledtext.ScrolledText(root, width=60, height=15)
result_area.pack(pady=5)

# Start processing the queue for GUI updates
process_queue()

root.mainloop()