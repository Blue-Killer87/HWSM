import psutil
import time
import numpy as np
import multiprocessing
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
from tabulate import tabulate
from datetime import datetime
import threading
from collections import defaultdict
from collections import defaultdict
import os


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
disk_buttons = []     



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
    global current_screen, disk_buttons
    current_screen = 'Screen3'
    toggle_theme(event, current_theme)
    Screen3_button.label.set_color("red")
    
    hide_all()

    # Get partitions
    partitions = get_disk_partitions()

    # Show disk panels
    ax_disk_pie.set_visible(True)
    ax_disk_stats.set_visible(True)
    ax_disk_list.set_visible(True)

    Screen3.button_axes = []
    Screen3.buttons = []
   

    # Dynamically create button axes
    num_disks = len(partitions)
    for i, partition in enumerate(partitions):
        x0 = 0.02 + i * (0.96 / num_disks)
        width = 0.94 / num_disks
        button_ax = fig.add_axes([x0, 0.905, width, 0.04])
        button = Button(button_ax, f"{partition.device}", color="#1e1e1e")
        
        # Use a default argument to fix late binding
        def on_click(event, part=partition):
            update_disk_display(ax_disk_pie, ax_disk_stats, part)

        button.on_clicked(on_click)
        Screen3.button_axes.append(button_ax)
        Screen3.buttons.append(button) 
        disk_buttons.append(button)

    

    # Display the first disk by default
    update_disk_display(ax_disk_pie, ax_disk_stats, partitions[0])

    plt.draw()


# GPU Screen
def Screen4(event):
    global current_screen
    current_screen = 'Screen4'
    toggle_theme(event, current_theme)
    Screen4_button.label.set_color("red")
    hide_all()
    

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

def group_partitions_by_device():
    device_dict = defaultdict(list)
    for part in psutil.disk_partitions(all=False):
        device = os.path.basename(part.device.split('p')[0])  # /dev/sda1 → sda
        device_dict[device].append(part)
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

def hide_all():
    ax_disk_pie.set_visible(False)
    ax_disk_stats.set_visible(False)
    ax_disk_list.set_visible(False)
    ax1.set_visible(False)
    ax2.set_visible(False)
    ax3.set_visible(False)
    ax4.set_visible(False)
    ax_processes.set_visible(False)
    hide_process_elements()
    hide_disk_buttons()

if __name__ == "__main__":
    manager = multiprocessing.Manager()
    ram_list = manager.list()
    cpu_list = manager.list()
    time_list = manager.list()

    ram_process = multiprocessing.Process(target=monitor_ram, args=(ram_list, time_list), daemon=True)
    cpu_process = multiprocessing.Process(target=monitor_cpu, args=(cpu_list, time_list), daemon=True)
    
    ram_process.start()
    cpu_process.start()
    
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

    def hide_disk_buttons():
        global disk_buttons
        for i in disk_buttons:
            i.ax.remove()
            i.ax.set_visible(False)
        disk_buttons = []


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
        blit=False
    )

    plt.show()
    
#https://github.com/Blue-Killer87