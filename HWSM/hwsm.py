import psutil
import time
import multiprocessing
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
global i
# Default Theme
current_theme = "dark"
plt.rcParams['toolbar'] = 'None'
i = 6
# Parameters
x_len = 200         # Number of points to display
y_range = [0, 10]  # Range of possible Y values to display
ram_total = psutil.virtual_memory().total / (1024**3)

# Daemon to measure ram
def monitor_ram(ram_list, time_list):
    while True:
        ram_usage = psutil.virtual_memory().used / (1024 ** 3)  # Convert to GB
        ram_list.append(ram_usage)
        time_list.append(len(time_list))  # Use time index
        time.sleep(0.1)

# Daemon to measure cpu
def monitor_cpu(cpu_list, time_list):
    while True:
        cpu_usage = psutil.cpu_percent(interval=0.05)  # Get CPU usage in %
        cpu_list.append(cpu_usage)
        time.sleep(0.1)

def update_chart(frame, time_list, ram_list, cpu_list, ram_line, cpu_line, ram_text, cpu_text, ax1, ax2):
    if not ram_list or not cpu_list:
        return ram_line, cpu_line, ram_text, cpu_text
    min_len = min(len(time_list), len(ram_list), len(cpu_list))

    time_values = time_list[:min_len]
    ram_values = ram_list[:min_len]
    cpu_values = cpu_list[:min_len]

    # Update data
    ram_line.set_data(time_values, ram_values)
    cpu_line.set_data(time_values, cpu_values)

    # Update latest text
    ram_text.set_text(f"Latest RAM Usage: {ram_values[-1]:.2f} GB")
    cpu_text.set_text(f"Latest CPU Usage: {cpu_values[-1]:.2f}%")

    i = time_values[-1]
    if i < 100: 
        ax1.set_xlim(0, 100)
        ax2.set_xlim(0, 100)
    else:
        ax1.set_xlim(i-100, i)
        ax2.set_xlim(i-100, i)
    
    return ram_line, cpu_line, ram_text, cpu_text, ax1, ax2


def on_hover(event):
    if event.inaxes:
        x, y = event.xdata, event.ydata
        if x is not None and y is not None:
            coord_display.set_text(f"Time: {int(x)}, Usage: {y:.2f}")

def toggle_theme(event):
    global current_theme

    if current_theme == "dark":
        plt.style.use("default")
        fig.patch.set_facecolor("white")
        ax1.set_facecolor("whitesmoke")
        ax2.set_facecolor("whitesmoke")
        ram_text.set_color("black")
        cpu_text.set_color("black")
        theme_button.label.set_text("Dark Mode")
        theme_button.label.set_color("black")
        theme_button.hovercolor="whitesmoke"
        current_theme = "light"
        ax2.set_ylabel("Usage (%)", color="black")
        ax2.set_xlabel("Time (Updates)", color="black")
        coord_display = fig.text(0.02, 0.02, "", fontsize=12, color="black")
    else:
        plt.style.use("dark_background")
        fig.patch.set_facecolor("#121212")
        ax1.set_facecolor("#1e1e1e")
        ax2.set_facecolor("#1e1e1e")
        ram_text.set_color("red")
        cpu_text.set_color("cyan")
        theme_button.label.set_text("Light Mode")
        theme_button.label.set_color("white")
        theme_button.hovercolor="black"
        current_theme = "dark"
        ax2.set_ylabel("Usage (%)", color="white")
        ax2.set_xlabel("Time (Updates)", color="white")
        coord_display = fig.text(0.02, 0.02, "", fontsize=12, color="white")
        
    fig.canvas.draw_idle()

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
    ram_line, = ax1.plot([], [], "r-", label="RAM Usage (GB)", linewidth=2)
    ax1.set_ylabel("Usage (GB)", color="white")
    ax1.legend()
    ax1.set_xticklabels([])
    ax1.grid(color="gray", linestyle="--", linewidth=0.5)
    ram_text = ax1.text(0.02, 0.9, "", transform=ax1.transAxes, fontsize=12, color="red")
    ax1.set_ylim([0,ram_total+2])
    # CPU Graph
    cpu_line, = ax2.plot([], [], "cyan", label="CPU Usage (%)", linewidth=2)
    ax2.set_ylabel("Usage (%)", color="white")
    ax2.set_xlabel("Time (Updates)", color="white")
    ax2.legend()
    ax2.set_xticklabels([])
    ax2.grid(color="gray", linestyle="--", linewidth=0.5)
    cpu_text = ax2.text(0.02, 0.9, "", transform=ax2.transAxes, fontsize=12, color="cyan")
    ax2.set_ylim([0,100])

    plt.subplots_adjust(hspace=0.4)

    # Display coordinates in bottom left
    coord_display = fig.text(0.02, 0.02, "", fontsize=12, color="white")

    # Create theme toggle button
    ax_button = plt.axes([0.85, 0.92, 0.12, 0.05])  # Button position
    theme_button = Button(ax_button, "Light Mode", color="gray", hovercolor="white")
    theme_button.on_clicked(toggle_theme)

    # Enable coordinate display on hover
    fig.canvas.mpl_connect("motion_notify_event", on_hover)

    ani = animation.FuncAnimation(fig, update_chart, fargs=(time_list, ram_list, cpu_list, ram_line, cpu_line, ram_text, cpu_text, ax1, ax2), interval=100)
    
    # Hide system control bar
    try:
        fig_manager = plt.get_current_fig_manager()
        fig_manager.window.attributes("-type", "splash")  # Removes window decorations (Linux)
    except Exception:
        pass  # Ignore if not supported on OS

    plt.show()

#https://github.com/Blue-Killer87