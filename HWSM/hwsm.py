import psutil
import time
import multiprocessing
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
global i
# Default Theme
cpu_peak = 0
ram_peak = 0
current_theme = "dark"
plt.rcParams['toolbar'] = 'None'
i = 6
# Parameters
ram_total = psutil.virtual_memory().total / (1024**3)

# Daemon to measure ram
def monitor_ram(ram_list, time_list, ram_peak):
    while True:
        ram_usage = psutil.virtual_memory().used / (1024 ** 3)  # Convert to GB
        ram_list.append(ram_usage)
        time_list.append(len(time_list))  # Use time index
        if ram_usage > ram_peak:
            ram_peak = ram_usage
        print(ram_peak)
        time.sleep(0.1)

# Daemon to measure cpu
def monitor_cpu(cpu_list, time_list, cpu_peak):
    while True:
        cpu_usage = psutil.cpu_percent(interval=0.05)  # Get CPU usageě in %
        cpu_list.append(cpu_usage)
        if cpu_usage > cpu_peak:
            cpu_peak = cpu_usage
        print(cpu_peak)
        time.sleep(0.1)
        

def update_chart(frame, time_list, ram_list, cpu_list, ram_line, cpu_line, total_cpu_line, total_ram_line, ram_text, cpu_text, ax1, ax2, ax3, ax4, cpu_peak):
    if not ram_list or not cpu_list:
        return ram_line, cpu_line, total_cpu_line, total_ram_line, ram_text, cpu_text
    min_len = min(len(time_list), len(ram_list), len(cpu_list))

    time_values = time_list[:min_len]
    ram_values = ram_list[:min_len]
    cpu_values = cpu_list[:min_len]

    # Update data
    ram_line.set_data(time_values, ram_values)
    cpu_line.set_data(time_values, cpu_values)
    total_cpu_line.set_data(time_values, cpu_values)
    total_ram_line.set_data(time_values, ram_values)

    # Update latest text
    ram_text.set_text(f"Latest RAM Usage: {ram_values[-1]:.2f} GB")
    cpu_text.set_text(f"Latest CPU Usage: {cpu_values[-1]:.2f}%")
    cpu_text.set_text(f"Highest CPU usage: {cpu_peak:.2f}%")
 

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

def Screen1(event):
    #Default screen with latest data brief
    pass

def Screen2(event):
  #Screen with total data  
  if ax3.get_visible() == True:
    ax1.set_visible(True)
    ax2.set_visible(True)
    ax3.set_visible(False)
    ax4.set_visible(False)
  else:  
    ax1.set_visible(False)
    ax2.set_visible(False)
    ax3.set_visible(True)
    ax4.set_visible(True)

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
        ax3.set_facecolor("whitesmoke")
        ax4.set_facecolor("whitesmoke")
        ax_panel.set_facecolor("gray")
        theme_button.color = ("gray")
        Screen2_button.color = ("gray")
        ram_text.set_color("black")
        cpu_text.set_color("black")
        theme_button.label.set_text("Dark Mode")
        theme_button.label.set_color("white")
        Screen2_button.label.set_color("white")
        theme_button.hovercolor="#1e1e1e"
        Screen2_button.hovercolor="#1e1e1e"
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
        coord_display = fig.text(0.02, 0.02, "", fontsize=12, color="black")
        
    else:
        plt.style.use("dark_background")
        fig.patch.set_facecolor("#121212")
        ax1.set_facecolor("#1e1e1e")
        ax2.set_facecolor("#1e1e1e")
        ax3.set_facecolor("#1e1e1e")
        ax4.set_facecolor("#1e1e1e")
        ax_panel.set_facecolor("#1e1e1e")
        theme_button.color=("#1e1e1e")
        Screen2_button.color=("#1e1e1e")
        ram_text.set_color("orange")
        cpu_text.set_color("cyan")
        theme_button.label.set_text("Light Mode")
        theme_button.label.set_color("white")
        Screen2_button.label.set_color("white")
        theme_button.hovercolor="black"
        Screen2_button.hovercolor="black"
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
        coord_display = fig.text(0.02, 0.02, "", fontsize=12, color="white")
        
        
    fig.canvas.draw_idle()

if __name__ == "__main__":
    manager = multiprocessing.Manager()
    ram_list = manager.list()
    cpu_list = manager.list()
    time_list = manager.list()

    ram_process = multiprocessing.Process(target=monitor_ram, args=(ram_list, time_list, ram_peak), daemon=True)
    cpu_process = multiprocessing.Process(target=monitor_cpu, args=(cpu_list, time_list, cpu_peak), daemon=True)
    
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

    # Create theme toggle button
    ax_panel = plt.axes([0, .95, 1, 0.05])
    ax_panel.set_visible(True)
    ax_panel.get_xaxis().set_visible(False)
    ax_panel.set_facecolor("#1e1e1e")
    ax_button1 = plt.axes([.879, 0.95, 0.12, 0.05])  # Button position
    ax_button2 = plt.axes([0, 0.95, 0.12, 0.05])  # Button position
    theme_button = Button(ax_button1, "Light Mode", color="#1e1e1e")
    Screen2_button = Button(ax_button2, "Total data", color="#1e1e1e")
    theme_button.on_clicked(toggle_theme)
    Screen2_button.on_clicked(Screen2)
    theme_button.label.set_color("gray")
    Screen2_button.label.set_color("gray")
    # Enable coordinate display on hover
    fig.canvas.mpl_connect("motion_notify_event", on_hover)
    ani = animation.FuncAnimation(fig, update_chart, fargs=(time_list, ram_list, cpu_list, ram_line, cpu_line, total_cpu_line, total_ram_line, ram_text, cpu_text, ax1, ax2, ax3, ax4, cpu_peak), interval=100)
    
    # Hide system control bar
    try:
        fig_manager = plt.get_current_fig_manager()
        fig_manager.window.attributes("-type", "splash")  # Removes window decorations (Linux)
    except Exception:
        pass  # Ignore if not supported on OS

    plt.show()

#https://github.com/Blue-Killer87