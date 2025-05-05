#!/bin/python3

import psutil
import GPUtil
import time
import numpy as np
import multiprocessing
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
import matplotlib.gridspec as gridspec
from tabulate import tabulate
from datetime import datetime
import threading
from collections import defaultdict
from collections import defaultdict
import os
import subprocess
import re
import json
import platform

system = platform.system()



# Default Theme
current_theme = "dark"
current_screen = 'Screen1'

plt.rcParams['toolbar'] = 'None'
i = 6
# Parameters
ram_total = psutil.virtual_memory().total / (1024**3)
LINES_PER_PAGE = 50
start_index = 0


# GUI state tracking
proc_list = []
start_index = 0
displayed_rows = 15
text_objects = []         
kill_buttons = []    
partition_buttons = []     
device_buttons = []
current_device = None
nav_buttons = {}
gpu_count = 3
gpu_render = False
gpu_timer = None

manager = multiprocessing.Manager()
ram_list = manager.list()
cpu_list = manager.list()
time_list = manager.list()




# Daemon to measure ram
def monitor_ram(ram_list, time_list):
    while True:
        ram_usage = psutil.virtual_memory().used / (1024 ** 3)  # Convert to GB
        ram_list.append(ram_usage)
        time_list.append(len(time_list))  # Use time index
        time.sleep(0.2)

# Daemon to measure cpu
def monitor_cpu(cpu_list, time_list):
    while True:
        cpu_usage = psutil.cpu_percent(interval=0.05)  # Get CPU usage in %
        cpu_list.append(cpu_usage)
        time.sleep(0.15)



ram_process = multiprocessing.Process(target=monitor_ram, args=(ram_list, time_list), daemon=True)
cpu_process = multiprocessing.Process(target=monitor_cpu, args=(cpu_list, time_list), daemon=True)

def update_chart(frame, time_list, ram_list, cpu_list, ram_line, cpu_line, total_cpu_line, total_ram_line, ram_text, cpu_text, ax1, ax2, ax3, ax4):
    if not ram_list or not cpu_list:
        
        return ram_line, cpu_line, total_cpu_line, total_ram_line, ram_text, cpu_text, total_cpu_text
    min_len = min(len(time_list), len(ram_list), len(cpu_list))
    time_values = np.array(time_list[:min_len])
    ram_values = np.array(ram_list[:min_len])
    cpu_values = np.array(cpu_list[:min_len])

    # Update data
    ram_line.set_data(time_values, ram_values)
    cpu_line.set_data(time_values, cpu_values)
    total_cpu_line.set_data(time_values, cpu_values)
    total_ram_line.set_data(time_values, ram_values)

    # Update latest text
    ram_text.set_text(f"Latest RAM Usage: {ram_values[-1]:.2f} GB")
    cpu_text.set_text(f"Latest CPU Usage: {cpu_values[-1]:.2f}%")

    i = time_values[-1]
    if i < 100: 
        ax1.set_xlim(0, 100)
        ax2.set_xlim(0, 100)
        ax3.set_xlim(0, 100)
        ax4.set_xlim(0, 100)
    else:
        ax1.set_xlim(i-100, i+1)
        ax2.set_xlim(i-100, i+1)
        ax3.set_xlim(0, i)
        ax4.set_xlim(0, i)
        
    return ram_line, cpu_line, total_cpu_line, total_ram_line, ram_text, cpu_text, ax1, ax2, ax3, ax4

# Screen handling
# Monitor Screen
def Screen1(event):
    global current_screen
    current_screen = 'Screen1'
    toggle_theme(event, current_theme)
    Screen1_button.label.set_color("red")
    hide_all()
    ax1.set_visible(True)
    ax2.set_visible(True)

# Processes Screen
def Screen2(event):
    global current_screen, proc_list, start_index
    current_screen = 'Screen2'
    hide_process_elements()
    toggle_theme(event, current_theme)
    Screen2_button.label.set_color("red")
    hide_all()
    ax_processes.set_visible(True)

    proc_list = []
    for i in psutil.process_iter():
        try:
            proc = [i.pid, i.name(), i.status(), i.exe()]
            proc_list.append(proc)
        except:
            continue

    start_index = 0
    ax_next_button.set_visible(True)
    ax_prev_button.set_visible(True)
    update_display()


def Screen3(event):
    global current_screen, device_buttons, partition_buttons, current_device
    current_screen = 'Screen3'
    toggle_theme(event, current_theme)
    Screen3_button.label.set_color("red")
   
    hide_all()
    ax_disk_pie.set_visible(True)
    ax_disk_stats.set_visible(True)
    ax_disk_list.set_visible(True)

    device_buttons.clear()
    partition_buttons.clear()

    device_map = group_physical_partitions_by_device()
    devices = list(device_map.keys())
    # Detect root partition's base device
    root_partition = next((p for p in psutil.disk_partitions(all=True) if p.mountpoint == "/"), None)
    if root_partition:
        system_device = os.path.basename(root_partition.device.split('p')[0])  # For nvmeXn1pY
        if system_device not in devices:  # fallback if using lsblk which may have different names
            system_device = next((d for d in devices if system_device in d), devices[0])
    else:
        system_device = devices[0]  # Fallback

    current_device = system_device

    # Create Device Buttons
    Screen3.device_button_axes = []
    Screen3.device_buttons = []
    
    for i, device in enumerate(devices):
        x0 = 0.02 + i * (0.96 / len(devices))
        width = 0.94 / len(devices)
        ax = fig.add_axes([x0, 0.91, width, 0.035])
        btn = Button(ax, device, color="#2a2a2a")
        
        btn.on_clicked(lambda event, dev=device, b=btn: (highlight_device_button(dev), on_device_select(dev)))
        Screen3.device_button_axes.append(ax)
        Screen3.device_buttons.append(btn)
        device_buttons.append(btn)

    # Initially select first device
    on_device_select(current_device)

# GPU Screen
def Screen4(event):
    global current_screen, gpu_render, gpu_timer
    current_screen = 'Screen4'
    toggle_theme(event, current_theme)
    Screen4_button.label.set_color("red")
    
    hide_all()
    gpu_render = True

    def update_loop():
        update_gpu_display(gpu_render)

    # Stop any existing timer first
    if gpu_timer is not None:
        gpu_timer.stop()

    gpu_timer = fig.canvas.new_timer(interval=2000)  # every 2 seconds
    gpu_timer.add_callback(update_loop)
    gpu_timer.start()

    update_gpu_display(gpu_render)

    

# Statistics Screen
def Screen5(event):
    global current_screen
    current_screen = 'Screen5'
    #Screen with total data  
    toggle_theme(event, current_theme)
    Screen5_button.label.set_color("red")
    hide_all()
    ax3.set_visible(True)
    ax4.set_visible(True)
    
# Hardware Screen
def Screen6(event):
    global current_screen
    current_screen = 'Screen6'
    toggle_theme(event, current_theme)
    Screen6_button.label.set_color("red")
    hide_all()

# Settings Screen
def Settings(event):
    global current_screen
    current_screen = 'Settings'
    # Not sure what this will contain yet
    toggle_theme(event, current_theme)
    Settings_button.label.set_color("red")
    hide_all()

# Theme toggle button handler (changing themes)
def toggle_theme(event, target=None):
    global current_theme
    
    if target == "dark":
        current_theme = "light"
    elif target == "light":
        current_theme = "dark"

    if current_theme == "dark":
        plt.style.use("default")
        fig.patch.set_facecolor("white")
        ax1.set_facecolor("whitesmoke")
        ax2.set_facecolor("whitesmoke")
        ax3.set_facecolor("whitesmoke")
        ax4.set_facecolor("whitesmoke")
        ax_panel.set_facecolor("gray")
        theme_button.color = ("gray")
        Screen1_button.color = ("gray")
        Screen2_button.color = ("gray")
        Screen3_button.color =("gray")
        Screen4_button.color =("gray")
        Screen5_button.color =("gray")
        Screen6_button.color =("gray")
        Settings_button.color =("gray")
        ram_text.set_color("black")
        cpu_text.set_color("black")
        theme_button.label.set_text("Dark Mode")
        theme_button.label.set_color("white")
        Screen1_button.label.set_color("white")
        Screen2_button.label.set_color("white")
        Screen3_button.label.set_color("white")
        Screen4_button.label.set_color("white")
        Screen5_button.label.set_color("white")
        Screen6_button.label.set_color("white")
        Settings_button.label.set_color("white")
        theme_button.hovercolor="#1e1e1e"
        Screen1_button.hovercolor="#1e1e1e"
        Screen2_button.hovercolor="#1e1e1e"
        Screen3_button.hovercolor="#1e1e1e"
        Screen4_button.hovercolor="#1e1e1e"
        Screen5_button.hovercolor="#1e1e1e"
        Screen6_button.hovercolor="#1e1e1e"
        Settings_button.hovercolor="#1e1e1e"
        
        current_theme = "light"
        ax1.set_ylabel("Usage (%)", color="black")
        ax1.set_xlabel("Time (Updates)", color="black")
        ax2.set_ylabel("Usage (%)", color="black")
        ax2.set_xlabel("Time (Updates)", color="black")
        ax3.set_ylabel("Usage (%)", color="black")
        ax3.set_xlabel("Time (Updates)", color="black")
        ax4.set_ylabel("Usage (%)", color="black")
        ax4.set_xlabel("Time (Updates)", color="black")
        ax1.spines['bottom'].set_color('black')
        ax1.spines['top'].set_color('black')
        ax1.spines['left'].set_color('black')
        ax1.spines['right'].set_color('black')
        ax2.spines['bottom'].set_color('black')
        ax2.spines['top'].set_color('black')
        ax2.spines['left'].set_color('black')
        ax2.spines['right'].set_color('black')
        ax3.spines['bottom'].set_color('black')
        ax3.spines['top'].set_color('black')
        ax3.spines['left'].set_color('black')
        ax3.spines['right'].set_color('black')
        ax4.spines['bottom'].set_color('black')
        ax4.spines['top'].set_color('black')
        ax4.spines['left'].set_color('black')
        ax4.spines['right'].set_color('black')
        ax1.tick_params(axis='y', colors='black')
        ax2.tick_params(axis='y', colors='black')
        ax3.tick_params(axis='y', colors='black')
        ax4.tick_params(axis='y', colors='black')
        
    else:
        plt.style.use("dark_background")
        fig.patch.set_facecolor("#121212")
        ax1.set_facecolor("#1e1e1e")
        ax2.set_facecolor("#1e1e1e")
        ax3.set_facecolor("#1e1e1e")
        ax4.set_facecolor("#1e1e1e")
        ax_panel.set_facecolor("#1e1e1e")
        theme_button.color=("#1e1e1e")
        Screen1_button.color=("#1e1e1e")
        Screen2_button.color=("#1e1e1e")
        Screen3_button.color=("#1e1e1e")
        Screen4_button.color=("#1e1e1e")
        Screen5_button.color=("#1e1e1e")
        Screen6_button.color=("#1e1e1e")
        Settings_button.color=("#1e1e1e")
        ram_text.set_color("red")
        cpu_text.set_color("blue")
        theme_button.label.set_text("Light Mode")
        theme_button.label.set_color("white")
        Screen1_button.label.set_color("white")
        Screen2_button.label.set_color("white")
        Screen3_button.label.set_color("white")
        Screen4_button.label.set_color("white")
        Screen5_button.label.set_color("white")
        Screen6_button.label.set_color("white")
        Settings_button.label.set_color("white")
        theme_button.hovercolor="gray"
        Screen1_button.hovercolor="gray"
        Screen2_button.hovercolor="gray"
        Screen3_button.hovercolor="gray"
        Screen4_button.hovercolor="gray"
        Screen5_button.hovercolor="gray"
        Screen6_button.hovercolor="gray"
        Settings_button.hovercolor="gray"
        current_theme = "dark"
        ax1.set_ylabel("Usage (%)", color="white")
        ax1.set_xlabel("Time (Updates)", color="white")
        ax2.set_ylabel("Usage (%)", color="white")
        ax2.set_xlabel("Time (Updates)", color="white")
        ax3.set_ylabel("Usage (%)", color="white")
        ax3.set_xlabel("Time (Updates)", color="white")
        ax4.set_ylabel("Usage (%)", color="white")
        ax4.set_xlabel("Time (Updates)", color="white")
        ax1.spines['bottom'].set_color('white')
        ax1.spines['top'].set_color('white')
        ax1.spines['left'].set_color('white')
        ax1.spines['right'].set_color('white')
        ax2.spines['bottom'].set_color('white')
        ax2.spines['top'].set_color('white')
        ax2.spines['left'].set_color('white')
        ax2.spines['right'].set_color('white')
        ax3.spines['bottom'].set_color('white')
        ax3.spines['top'].set_color('white')
        ax3.spines['left'].set_color('white')
        ax3.spines['right'].set_color('white')
        ax4.spines['bottom'].set_color('white')
        ax4.spines['top'].set_color('white')
        ax4.spines['left'].set_color('white')
        ax4.spines['right'].set_color('white')
        ax1.tick_params(axis='y', colors='white')
        ax2.tick_params(axis='y', colors='white')
        ax3.tick_params(axis='y', colors='white')
        ax4.tick_params(axis='y', colors='white')
        
    fig.canvas.draw_idle()


def export_data(event):
    if len(time_list) == 0 or len(ram_list) == 0 or len(cpu_list) == 0:
        print("No data to export.")
        return


    # Use NumPy arrays
    min_len = min(len(time_list), len(ram_list), len(cpu_list))
    time_vals = np.array(time_list[:min_len])
    ram_vals = np.array(ram_list[:min_len])
    cpu_vals = np.array(cpu_list[:min_len])


    # Create table-like text
    export_lines = ["TimeIndex\tRAM_Usage_GB\tCPU_Usage_%"]
    for t, r, c in zip(time_vals, ram_vals, cpu_vals):
        export_lines.append(f"{t}\t{r:.2f}\t{c:.2f}")

    
    # Save to file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"system_usage_export_{timestamp}.txt"
    with open(filename, "w") as f:
        f.write("\n".join(export_lines))
    full_path = f"./{filename}"  # or use absolute path if needed
    print(f"Exported to {full_path}")


    # Show status text
    status_text.set_text(f"Saved to {full_path}")
    plt.draw()
    # Function to clear the text
    def clear_status():
        status_text.set_text("")
        plt.draw()
    # Clear it after 3 seconds
    threading.Timer(3.0, clear_status).start()

def is_physical_partition(part):
    if not part.device or not part.device.startswith("/dev/"):
        return False
    if part.fstype.lower() in ["tmpfs", "proc", "sysfs", "devtmpfs", "devpts", "overlay", "squashfs"]:
        return False
    if part.mountpoint.startswith(("/proc", "/sys", "/dev")):
        return False
    return True

def group_physical_partitions_by_device():
    device_dict = get_all_block_devices()
    partition_dict = defaultdict(list)

    for device, parts in device_dict.items():
        for part in parts:
            # Simulate psutil-like object for compatibility
            part_obj = type('Partition', (object,), {
                "device": part["device"],
                "mountpoint": part["mountpoint"],
                "fstype": part["fstype"]
            })()
            partition_dict[device].append(part_obj)

    return partition_dict


def group_partitions_by_device():
    device_dict = defaultdict(list)
    for part in psutil.disk_partitions(all=True):
        dev_path = os.path.basename(part.device)
        # Match nvme0n1p1 ➝ nvme0n1, or sda1 ➝ sda
        base = dev_path
        if "nvme" in dev_path:
            base = dev_path.split('p')[0]
        else:
            # Strip trailing digits (e.g. sda1 ➝ sda)
            base = ''.join(filter(lambda c: not c.isdigit(), dev_path))
        device_dict[base].append(part)
    return device_dict



def on_device_select(device):
    global current_device, partition_buttons
    current_device = device

    # Clear previous partition buttons
    for btn in partition_buttons:
        destroy_button(btn)
    partition_buttons.clear()

    partitions = group_partitions_by_device().get(device, [])

    if not partitions:
        ax_disk_pie.clear()
        ax_disk_pie.set_visible(False)
        ax_disk_stats.clear()
        ax_disk_stats.set_visible(False)
        plt.draw()
        return
    else:
        ax_disk_pie.set_visible(True)
        ax_disk_stats.set_visible(True)

    # Create partition buttons
    for i, partition in enumerate(partitions):
        x0 = 0.02 + i * (0.96 / len(partitions))
        width = 0.94 / len(partitions)
        ax = fig.add_axes([x0, 0.85, width, 0.04])
        btn = Button(ax, partition.device, color="#1e1e1e")
        btn.on_clicked(lambda event, part=partition, b=btn: on_partition_select(part, b))
        partition_buttons.append(btn)

    # Highlight device button
    highlight_device_button(device)
    

    # Update initial partition view
    on_partition_select(partitions[0], partition_buttons[0])
    plt.draw()



def on_partition_select(partition, button):
    update_disk_display(ax_disk_pie, ax_disk_stats, partition)
    highlight_partition_button(button)

def highlight_device_button(selected_device):
    for btn in device_buttons:
        if btn.label.get_text() == selected_device:
            btn.label.set_color("red")
        else:
            btn.label.set_color("white")

def highlight_partition_button(selected_button):
    for btn in partition_buttons:
        btn.label.set_color("white")
    selected_button.label.set_color("red")

def get_all_block_devices():
    result = subprocess.run(['lsblk', '-J', '-o', 'NAME,TYPE,MOUNTPOINT,FSTYPE'], capture_output=True, text=True)
    data = json.loads(result.stdout)
    device_dict = defaultdict(list)

    def process_device(dev):
        if dev["type"] == "disk":
            device_name = dev["name"]  # e.g., nvme0n1
            device_dict[device_name]  # initialize
        if "children" in dev:
            for child in dev["children"]:
                part_name = child["name"]  # e.g., nvme0n1p2
                mountpoint = child.get("mountpoint") or ""
                fstype = child.get("fstype") or ""
                device_name = dev["name"]
                device_dict[device_name].append({
                    "device": f"/dev/{part_name}",
                    "mountpoint": mountpoint,
                    "fstype": fstype
                })

    for blockdev in data["blockdevices"]:
        process_device(blockdev)

    return device_dict

# Get all the disk partitions
def get_disk_partitions():
    partitions = psutil.disk_partitions()
    return partitions

# Get disk usage for a given partition
def get_disk_usage(partition):
    usage = psutil.disk_usage(partition.mountpoint)
    return usage

# Create pie chart of disk usage
def plot_disk_usage(ax, partition):
    usage = get_disk_usage(partition)
    labels = ['Used', 'Free']
    sizes = [usage.used, usage.free]
    ax.clear()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['red', 'green'])
    ax.axis('equal')  # Equal aspect ratio ensures pie chart is circular

# Display disk stats under pie chart
def display_disk_stats(ax_stats, partition):
    usage = get_disk_usage(partition)
    ax_stats.clear()
    stats = [
        f"Total Space: {usage.total / (1024**3):.2f} GB",
        f"Used Space: {usage.used / (1024**3):.2f} GB",
        f"Free Space: {usage.free / (1024**3):.2f} GB",
        f"Format: {partition.fstype}",
        f"Disk Type: {partition.device}"
    ]
    for i, stat in enumerate(stats):
        ax_stats.text(0.05, 1 - i * 0.2, stat, transform=ax_stats.transAxes, fontsize=12, color="white")
    ax_stats.set_axis_off()

# Function to update the disk stats and pie chart when a disk is selected
def update_disk_display(ax, ax_stats, partition):
    plot_disk_usage(ax, partition)
    display_disk_stats(ax_stats, partition)
    plt.draw()


def get_windows_gpus():
    gpus = []
    try:
        output = subprocess.check_output(["wmic", "path", "win32_videocontroller", "get", "name"], universal_newlines=True)
        lines = output.strip().split("\n")[1:]  # skip the header
        for line in lines:
            gpu_name = line.strip()
            if gpu_name:
                gpus.append({'name': gpu_name, 'load': None, 'memory_used': None, 'memory_total': None, 'temperature': None})
    except Exception as e:
        print(f"Error detecting GPUs on Windows: {e}")
    return gpus

def get_linux_gpus():
    gpus = []
    try:
        output = subprocess.check_output(["lshw", "-C", "display"], universal_newlines=True)
        entries = output.split("*-display")
        for entry in entries:
            if "product:" in entry:
                lines = entry.splitlines()
                name_line = next((line for line in lines if "product:" in line), None)
                if name_line:
                    gpu_name = name_line.split("product:")[1].strip()
                    gpus.append({'name': gpu_name, 'load': None, 'memory_used': None, 'memory_total': None, 'temperature': None})
    except Exception as e:
        print(f"Error detecting GPUs on Linux: {e}")
    return gpus


def get_nvidia_gpu_stats():
    gpus = []
    try:
        nvidia_gpus = GPUtil.getGPUs()
        for ngpu in nvidia_gpus:
            gpus.append({
                'name': ngpu.name,
                'load': ngpu.load * 100,  # Load in percentage
                'memory_used': ngpu.memoryUsed,  # Memory used in MB
                'memory_total': ngpu.memoryTotal,  # Total memory in MB
                'temperature': ngpu.temperature  # Temperature in Celsius
            })
    except Exception as e:
        print(f"Error fetching NVIDIA GPU stats: {e}")
    return gpus

def get_intel_gpu_stats():
    gpus = []

    try:
        drm_cards = [
            p for p in os.listdir('/sys/class/drm') if re.match(r'card\d+$', p)
        ]

        for card in drm_cards:
            device_path = f"/sys/class/drm/{card}/device"
            vendor_path = os.path.join(device_path, "vendor")

            if not os.path.exists(vendor_path):
                continue

            with open(vendor_path) as f:
                vendor = f.read().strip()

            if vendor != "0x8086":
                continue  # Not Intel

            print(f"[Intel GPU Detected] {card}")

            name = f"Intel GPU ({card})"
            temperature = 0.0
            load = 0.0

            # Temperature
            temperature = 0.0
            hwmon_base = os.path.join(device_path, "hwmon")
            if os.path.exists(hwmon_base):
                hwmons = os.listdir(hwmon_base)
                if hwmons:
                    temp_path = os.path.join(hwmon_base, hwmons[0], "temp1_input")
                    if os.path.exists(temp_path):
                        with open(temp_path) as f:
                            temperature = int(f.read().strip()) / 1000.0
                    else:
                        print(f"Temperature file missing: {temp_path}")
                else:
                    print(f"No hwmon dirs found in: {hwmon_base}")
            else:
                print(f"No hwmon path for Intel GPU: {hwmon_base}")

            # Load (estimated from frequency)
            load = 0.0
            cur_freq_path = os.path.join(device_path, "gt_cur_freq_mhz")
            max_freq_path = os.path.join(device_path, "gt_max_freq_mhz")

            if os.path.exists(cur_freq_path) and os.path.exists(max_freq_path):
                with open(cur_freq_path) as f:
                    cur = int(f.read().strip())
                with open(max_freq_path) as f:
                    maxf = int(f.read().strip())
                if maxf > 0:
                    load = (cur / maxf) * 100
            else:
                print("Intel GPU freq paths not found.")

            gpus.append({
                'name': name,
                'load': load,
                'memory_used': 0.0,
                'memory_total': 0.0,
                'temperature': temperature
            })

    except Exception as e:
        print(f"[Intel GPU Stats Error] {e}")

    return gpus


def get_amd_gpu_stats():
    gpus = []
    try:
        load = 0.0
        memory_used = 0.0
        memory_total = 0.0
        temperature = 0.0

        try:
            rocm_output = subprocess.check_output(["rocm-smi", "--showuse", "--showtemp", "--showmemuse"]).decode()

            # Example parsing logic (will vary by rocm-smi version)
            load_match = re.search(r'GPU\s+\d+\s+:\s+(\d+)%', rocm_output)
            load = float(load_match.group(1)) if load_match else 0.0

            temp_match = re.search(r'Temperature.*?:\s+(\d+)\.\d+C', rocm_output)
            temperature = float(temp_match.group(1)) if temp_match else 0.0

            mem_match = re.search(r'Memory Used.*?:\s+(\d+)\s+MiB\s*/\s*(\d+)\s+MiB', rocm_output)
            if mem_match:
                memory_used = float(mem_match.group(1))
                memory_total = float(mem_match.group(2))

        except Exception:
            # Fallback to `sensors` for temp
            sensors_output = subprocess.check_output(["sensors"]).decode()
            temp_match = re.search(r"edge:\s+\+?([\d.]+)°C", sensors_output)
            temperature = float(temp_match.group(1)) if temp_match else 0.0

        gpus.append({
            'name': 'AMD Radeon GPU',
            'load': load,
            'memory_used': memory_used,
            'memory_total': memory_total,
            'temperature': temperature
        })
    except Exception as e:
        print(f"[AMD] Error fetching GPU stats: {e}")
    return gpus

def get_gpu_info():
    detected_gpus = []

    if system == "Windows":
        detected_gpus = get_windows_gpus()
    elif system == "Linux":
        detected_gpus = get_linux_gpus()

    nvidia_stats = get_nvidia_gpu_stats()
    intel_stats = get_intel_gpu_stats()
    amd_stats = get_amd_gpu_stats()

    for gpu in detected_gpus:
        name = gpu['name'].lower()

        if "nvidia" in name or "geforce" in name:
            match = next((g for g in nvidia_stats if any(part.lower() in name for part in g['name'].split())), None)
        elif "intel" in name or "uhd" in name:
            match = next((g for g in intel_stats if any(part.lower() in name for part in g['name'].split())), None)
        elif "amd" in name or "radeon" in name:
            match = next((g for g in amd_stats if any(part.lower() in name for part in g['name'].split())), None)
        else:
            match = None

        if match:
            gpu.update(match)
            print(f"Matched: {gpu['name']} with stats: {match}")

    return detected_gpus

def update_gpu_display(render):
    gpus = get_gpu_info()
    #print("Detected GPUs:", gpus) #For debug
    
    try:
        for ax in gpu_axes:
            ax.set_visible(False)
        plt.draw()
    except:
        print("cannot unload or start daemon")

    for ax in gpu_axes:
        ax.clear()
        ax.set_visible(False)

    if not gpus:
        gpu_axes[0].text(0.5, 0.5, "No GPU detected", ha='center', va='center', color="white", fontsize=14)
        if render == True:
            gpu_axes[0].set_visible(True)
        plt.draw()
        return

    for i, gpu in enumerate(gpus):
        if i >= len(gpu_axes):
            break  # Don't exceed available axes

        ax = gpu_axes[i]
        if render == True:
            ax.set_visible(True)
        ax.set_facecolor("#1e1e1e")

        # Gather data
        
        values = [
            gpu['load'] if gpu['load'] is not None else 0,
            gpu['temperature'] if gpu['temperature'] is not None else 0,
            gpu['memory_used'] if gpu['memory_used'] is not None else 0,
            gpu['memory_total'] if gpu['memory_total'] is not None else 1  # prevent zero-division
        ]
        labels = ['Usage (%)', 'Temp (°C)', f'VRAM Used (MB)\n{values[2]}/{values[3]} MB']
        # Normalize usage/temperature to percentage-style for bar sizes
        if values[3] != 0:
            vram_percent = (values[2] / values[3]) * 100
        else:
            vram_percent = 0

        display_values = [values[0], values[1], vram_percent]
        colors = ['limegreen', 'red', 'cyan']

        bars = ax.bar(labels, display_values, color=colors)

        for bar, val in zip(bars, display_values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                    f"{val:.1f}", ha='center', va='bottom', color="white", fontsize=8)

        ax.set_ylim(0, 110)
        ax.set_title(gpu['name'], color="white", fontsize=10)
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color("white")
        ax.spines['bottom'].set_color("white")
        ax.yaxis.label.set_color("white")
        ax.xaxis.label.set_color("white")

    plt.draw()

    
   



def hide_all():
    global device_buttons, partition_buttons, gpu_render, gpu_timer

    ax_disk_pie.set_visible(False)
    ax_disk_stats.set_visible(False)
    ax_disk_list.set_visible(False)
    ax1.set_visible(False)
    ax2.set_visible(False)
    ax3.set_visible(False)
    ax4.set_visible(False)
    ax_processes.set_visible(False)
    hide_process_elements()
    hide_partition_buttons()

    for btn in partition_buttons:
        destroy_button(btn)
    partition_buttons.clear()

    for btn in device_buttons:
        destroy_button(btn)
    device_buttons.clear()

    #Clear GPU screen
    for ax in gpu_axes:
        ax.set_visible(False)
    plt.draw()
    gpu_render = False

    if gpu_timer:
        gpu_timer.stop()
        gpu_timer = None


if __name__ == "__main__":
    
    # Setup Matplotlib with dark mode as default
    plt.style.use("dark_background")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6))
    fig.patch.set_facecolor("#121212")
    ax1.set_facecolor("#1e1e1e")
    ax2.set_facecolor("#1e1e1e")
    
    # RAM Graph
    ram_line, = ax1.plot([], [], "red", label="RAM Usage (GB)", linewidth=2)
    ax1.set_ylabel("Usage (GB)", color="white")
    ax1.legend()
    ax1.set_xticklabels([])
    ax1.grid(color="gray", linestyle="--", linewidth=0.5)
    ram_text = ax1.text(0.02, 0.9, "", transform=ax1.transAxes, fontsize=12, color="red")
    ax1.set_ylim([0,ram_total+2])
    
    # CPU Graph
    cpu_line, = ax2.plot([], [], "blue", label="CPU Usage (%)", linewidth=2)
    ax2.set_ylabel("Usage (%)", color="white")
    ax2.set_xlabel("Time (Updates)", color="white")
    ax2.legend()
    ax2.set_xticklabels([])
    ax2.grid(color="gray", linestyle="--", linewidth=0.5)
    cpu_text = ax2.text(0.02, 0.9, "", transform=ax2.transAxes, fontsize=12, color="blue")
    ax2.set_ylim([0,100])

    # CPU Graph - Total
    ax3 = plt.axes([.15, .55, .75, .3])
    ax3.set_facecolor("#1e1e1e")
    total_cpu_line, = ax3.plot([], [], "blue", label="Total CPU usage (%)", linewidth=2)
    ax3.set_ylabel("Usage (%)", color="white")
    ax3.set_xlabel("Time (Updates)", color="white")
    ax3.legend()
    ax3.grid(color="gray", linestyle="--", linewidth=0.5)
    total_cpu_text = ax3.text(0.02, 0.9, "", transform=ax3.transAxes, fontsize=12, color="blue")
    ax3.set_ylim([0,100])
    ax3.set_visible(False)

    # Ram Graph - Total
    ax4 = plt.axes([.15, .15, .75, .3])
    ax4.set_facecolor("#1e1e1e")
    total_ram_line, = ax4.plot([], [], "red", label="Total RAM usage (GB)", linewidth=2)
    ax4.set_ylabel("Usage (GB)", color="white")
    ax4.set_xlabel("Time (Updates)", color="white")
    ax4.legend()
    ax4.grid(color="gray", linestyle="--", linewidth=0.5)
    total_ram_text = ax4.text(0.02, 0.9, "", transform=ax4.transAxes, fontsize=12, color="red")
    ax4.set_ylim([0,ram_total+2])
    ax4.set_visible(False)
    
    plt.subplots_adjust(hspace=0.4)

    # Display coordinates in bottom left
    coord_display = fig.text(0.02, 0.02, "", fontsize=12, color="white")

    # Buttons and Panel
    # Panel
    ax_panel = plt.axes([0, .95, 1, 0.05])
    ax_panel.set_visible(True)
    ax_panel.get_xaxis().set_visible(False)
    ax_panel.set_facecolor("#1e1e1e")

    # Buttons
    
    ax_button1 = plt.axes([0, .95, .12, .05])
    ax_button2 = plt.axes([.121, .95, .12, .05])  
    ax_button3 = plt.axes([.241, .95, .12, .05])
    ax_button4 = plt.axes([.361,.95,.12,.05])   
    ax_button5 = plt.axes([.481,.95,.12,.05])
    ax_button6 = plt.axes([.601,.95,.12,.05])
    ax_settings_button = plt.axes([.721, .95, .14, .05])
    theme_button = plt.axes([.861, .95, .138, .05])
    

    ax_export_button = plt.axes([0.02, 0.01, 0.14, 0.04])
    export_button = Button(ax_export_button, "Export Data", color="gray")
    export_button.on_clicked(export_data)
    status_text = ax_export_button.figure.text(0.18, 0.025, "", fontsize=9, color="green")


    theme_button = Button(theme_button, "Light Mode", color="#1e1e1e")
    Screen1_button = Button(ax_button1, "Monitor", color=("#1e1e1e"))
    Screen2_button = Button(ax_button2, "Processes", color=("#1e1e1e"))
    Screen3_button = Button(ax_button3, "Disk", color=("#1e1e1e"))
    Screen4_button = Button(ax_button4, "GPU", color=("#1e1e1e"))
    Screen5_button = Button(ax_button5, "Statistics", color=("#1e1e1e"))
    Screen6_button = Button(ax_button6, "Hardware", color=("#1e1e1e"))
    Settings_button = Button(ax_settings_button, "Settings", color=("#1e1e1e"))
    
    # Event Handling
    theme_button.on_clicked(toggle_theme)
    Screen1_button.on_clicked(Screen1)
    Screen2_button.on_clicked(Screen2)
    Screen3_button.on_clicked(Screen3)
    Screen4_button.on_clicked(Screen4)
    Screen5_button.on_clicked(Screen5)
    Screen6_button.on_clicked(Screen6)
    Settings_button.on_clicked(Settings)

    
    toggle_theme(1, current_theme)
    Screen1_button.label.set_color("red")

    # Process Screen
    ax_processes = plt.axes([0,0,1,0.95])
    ax_processes.get_xaxis().set_visible(False)
    ax_processes.set_facecolor("#1e1e1e")

    
   

    gpu_axes = []  # Global list to hold one axes per GPU (max 4 as example)


    ram_process.start()
    cpu_process.start()
    

    for i in range(gpu_count):  # Assume max 4 GPUs; adjust if needed
        ax = fig.add_subplot(3, 1, i + 1)
        ax.set_facecolor("#1e1e1e")
        ax.set_visible(False)
        gpu_axes.append(ax)


    def next_page(event):
        global start_index
        if start_index + displayed_rows < len(proc_list):
            start_index += displayed_rows
            update_display()

    def prev_page(event):
        global start_index
        if start_index - displayed_rows >= 0:
            start_index -= displayed_rows
            update_display()

    def update_display():
        global text_objects, kill_buttons

        # Clear previous text and buttons
        for txt in text_objects:
            txt.remove()
        text_objects = []
            
        for btn in kill_buttons:
            btn.ax.set_visible(False)
            btn.ax.remove()
        kill_buttons = []

        ax_processes.clear()
        ax_processes.set_facecolor("#1e1e1e")
        ax_processes.get_xaxis().set_visible(False)
        ax_processes.get_yaxis().set_visible(False)

        # Column headers
        headers = ["PID", "Name", "Status", "Path"]
        y = 0.9
        for j, header in enumerate(headers):
            txt = ax_processes.text(0.05 + j * 0.2, y, header, fontsize=10, color="white", transform=ax_processes.transAxes)
            text_objects.append(txt)

        # Display process rows with kill buttons
        for idx in range(start_index, min(start_index + displayed_rows, len(proc_list))):
            proc = proc_list[idx]
            y -= 0.05
            for j, value in enumerate(proc):
                txt = ax_processes.text(0.05 + j * 0.2, y, str(value), fontsize=9, color="white", transform=ax_processes.transAxes)
                text_objects.append(txt)

            # Create Kill button
            ax_kill = plt.axes([0.91, y - 0.03, 0.08, 0.02])
            btn = Button(ax_kill, 'Kill', color='gray')
            btn.on_clicked(lambda event, pid=proc[0]: kill_process(pid))
            kill_buttons.append(btn)

        fig.canvas.draw_idle()

    # Create buttons for next and previous pages
    ax_next_button = plt.axes([.88, 0.02, .1, .05])
    ax_prev_button = plt.axes([.77, 0.02, .1, .05])

    btn_next = Button(ax_next_button, "Next", color='gray')
    btn_prev = Button(ax_prev_button, "Previous", color='gray')

    # Link buttons to pagination functions
    btn_next.on_clicked(next_page)
    btn_prev.on_clicked(prev_page)

    def on_key(event):
        global start_index
        if event.key == 'down':
            if start_index + LINES_PER_PAGE < len(proc_list):
                start_index += 1
                update_display()
        elif event.key == 'up':
            if start_index > 0:
                start_index -= 1
                update_display()

    def destroy_button(btn):
        if hasattr(btn, 'disconnect_events'):
            btn.disconnect_events()
        if btn.ax in fig.axes:
            btn.ax.remove()

    def kill_process(pid):
        try:
            p = psutil.Process(pid)
            p.terminate()
            print(f"Terminated process {pid}")
            # Refresh process list
            Screen2(None)
        except Exception as e:
            print(f"Failed to terminate process {pid}: {e}")

    def hide_process_elements():
        global text_objects, kill_buttons
        for txt in text_objects:
            txt.remove()
        text_objects.clear()
        for btn in kill_buttons:
            btn.ax.set_visible(False)
            btn.ax.remove()
        kill_buttons.clear()
        ax_next_button.set_visible(False)
        ax_prev_button.set_visible(False)

    def hide_partition_buttons():
        global partition_buttons
        for i in partition_buttons:
            i.ax.remove()
            i.ax.set_visible(False)
        partition_buttons = []


    # Disk usage pie chart
    ax_disk_pie = plt.axes([.15, .55, .75, .3])
    ax_disk_pie.set_facecolor("#1e1e1e")
    ax_disk_pie.set_visible(False)

    # Stats display
    ax_disk_stats = plt.axes([.15, .2, .75, .3])
    ax_disk_stats.set_facecolor("#1e1e1e")
    ax_disk_stats.set_visible(False)

    ax_disk_list = plt.axes([0, .90, 1, 0.05])
    ax_disk_list.set_visible(False)
    ax_disk_list.set_facecolor("#1e1e1e")
    ax_disk_list.get_xaxis().set_visible(False)


    fig.canvas.mpl_connect('key_press_event', on_key)
    update_display()
    Screen1(1)

    ani = animation.FuncAnimation(
        fig,
        update_chart,
        fargs=(
            time_list,
            ram_list,
            cpu_list,
            ram_line,
            cpu_line,
            total_cpu_line,
            total_ram_line,
            ram_text,
            cpu_text,
            ax1,
            ax2,
            ax3,
            ax4
        ),
        interval=200,  # Refresh every 200ms
        blit=False,
        save_count=20
    )

    plt.show()
    
#https://github.com/Blue-Killer87