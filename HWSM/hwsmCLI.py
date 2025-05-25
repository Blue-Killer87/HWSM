#!/usr/bin/env python3
"""
Simple hardware system monitor CLI using psutil.
Usage:
  ./hwsmCLI -cpu    # CPU stats
  ./hwsmCLI -mem    # Memory stats
  ./hwsmCLI -disk   # Disk and partition stats
  ./hwsmCLI -io     # Disk I/O stats
  ./hwsmCLI -gpu    # GPU stats
  ./hwsmCLI -net    # Network stats (IP address, interface data)
  ./hwsmCLI -sys    # System info (OS, kernel, architecture)
  ./hwsmCLI -bat    # Battery statistics
  ./hwsmCLI -all    # All above statistics
  ./hwsmCLI -help   # Show this help message
If no parameters provided, shows help.
"""
import sys
import psutil
import platform
import subprocess
import shutil
import re
import socket
import os
import cpuinfo


def print_help():
    help_text = ("Usage: ./hwsmCLI [option]\n"
                 "Options:\n"
                 "  -cpu    Show CPU statistics (vendor, model, usage%)\n"
                 "  -mem    Show memory statistics (total, used, free, swap)\n"
                 "  -disk   Show disk and partition statistics\n"
                 "  -io     Show disk I/O statistics\n"
                 "  -gpu    Show GPU statistics\n"
                 "  -net    Show network statistics (IP address, interfaces)\n"
                 "  -sys    Show system information (OS, kernel, architecture)\n"
                 "  -bat    Show battery statistics\n"
                 "  -all    Show CPU, memory, disk, I/O, Net, GPU, battery, system info\n"
                 "  -help   Show this help message")
    print("\n+---------------- Help ----------------+")
    print(help_text)
    print("+-------------------------------------+\n")

def get_size(num_bytes, suffix="B"):
    factor = 1024
    for unit in ["","K","M","G","T","P"]:
        if num_bytes < factor:
            return f"{num_bytes:.2f}{unit}{suffix}"
        num_bytes /= factor
    return f"{num_bytes:.2f}Y{suffix}"

def print_cpu():
    proc = cpuinfo.get_cpu_info()["brand_raw"]
    print("\n+--------------- CPU Info ---------------+")
    print(f"| Vendor/Model   : {proc}")
    print(f"| Physical cores : {psutil.cpu_count(logical=False)}")
    print(f"| Total cores    : {psutil.cpu_count(logical=True)}")
    usage = psutil.cpu_percent(percpu=True, interval=1)
    print("| Usage per core:")
    for i, u in enumerate(usage): print(f"|   Core {i+1:<2}: {u}%")
    print(f"| Total usage : {psutil.cpu_percent()}%")
    print("+----------------------------------------+\n")

def print_mem():
    vm = psutil.virtual_memory(); sm = psutil.swap_memory()
    print("\n+--------------- Memory Info ------------+")
    print(f"| Total Memory     : {get_size(vm.total)}")
    print(f"| Used Memory      : {get_size(vm.used)}")
    print(f"| Free Memory      : {get_size(vm.available)}")
    print(f"| Usage            : {vm.percent}%")
    print(f"+----------------------------------------+")
    print(f"| Total Swap       : {get_size(sm.total)}")
    print(f"| Used Swap        : {get_size(sm.used)}")
    print(f"| Free Swap        : {get_size(sm.free)}")
    print(f"| Swap Usage       : {sm.percent}%")
    print("+----------------------------------------+\n")

def print_disk():
    print("\n+---------------- Disk Info ----------------+")
    partitions = psutil.disk_partitions()
    for p in partitions:
        print(f"| Device: {p.device}")
        print(f"|   Mountpoint : {p.mountpoint}")
        print(f"|   File System: {p.fstype}")
        try:
            usage = psutil.disk_usage(p.mountpoint)
            print(f"|   Total Size : {get_size(usage.total)}")
            print(f"|   Used       : {get_size(usage.used)}")
            print(f"|   Free       : {get_size(usage.free)}")
            print(f"|   Usage      : {usage.percent}%")
        except PermissionError:
            print("|   [Permission Denied]")
        print("|")
    print("+------------------------------------------+\n")

def print_io():
    io = psutil.disk_io_counters(perdisk=True)
    print("\n+----------------- Disk I/O -----------------+")
    for disk, stats in io.items():
        print(f"| Disk: {disk}")
        print(f"|   Read Count     : {stats.read_count}")
        print(f"|   Write Count    : {stats.write_count}")
        print(f"|   Read Bytes     : {get_size(stats.read_bytes)}")
        print(f"|   Write Bytes    : {get_size(stats.write_bytes)}")
        print(f"|   Read Time (ms) : {stats.read_time}")
        print(f"|   Write Time (ms): {stats.write_time}")
        print("|")
    print("+-------------------------------------------+\n")

def print_net():
    print("\n+----------------- Network Info -----------------+")
    hostname = socket.gethostname()
    try:
        ip = socket.gethostbyname(hostname)
        print(f"| Hostname       : {hostname}")
        print(f"| IP Address     : {ip}")
    except socket.gaierror:
        print("| IP Address     : [Unavailable]")
    net_io = psutil.net_io_counters(pernic=True)
    for iface, stats in net_io.items():
        print(f"| Interface: {iface}")
        print(f"|   Bytes Sent    : {get_size(stats.bytes_sent)}")
        print(f"|   Bytes Received: {get_size(stats.bytes_recv)}")
        print("|")
    print("+------------------------------------------------+\n")

# GPU section

def get_nvidia_info():
    nv=[]
    if shutil.which("nvidia-smi"):
        out=subprocess.check_output([
            "nvidia-smi","--query-gpu=index,name,utilization.gpu,temperature.gpu,pci.bus_id",
            "--format=csv,noheader,nounits"],universal_newlines=True)
        for l in out.strip().splitlines():
            idx,name,u,t,b=l.split(',')
            nv.append({"Bus":b.strip(),"Product":name.strip(),"Vendor":"NVIDIA","Usage":u.strip()+"%","Temperature":t.strip()+"°C"})
    return nv

def get_intel_gpu_info():
    intel_gpu = {
        'Usage': 'N/A',
        'Temperature': 'N/A'
    }
    try:
        # Try intel_gpu_top for live usage
        if shutil.which("intel_gpu_top"):
            proc = subprocess.Popen(["intel_gpu_top", "-J", "-s", "200", "-n", "1"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            out, _ = proc.communicate(timeout=2)
            match = re.search(r'"busy":\s*(\d+)', out.decode())
            if match:
                intel_gpu['Usage'] = match.group(1) + '%'
    except Exception:
        pass

    # Try reading temp from /sys/class/drm/card0/device/hwmon/.../temp*_input
    try:
        hwmon_path = "/sys/class/drm/card0/device/hwmon"
        if os.path.isdir(hwmon_path):
            for d in os.listdir(hwmon_path):
                tpath = os.path.join(hwmon_path, d, "temp1_input")
                if os.path.isfile(tpath):
                    with open(tpath) as f:
                        val = int(f.read().strip())
                        intel_gpu['Temperature'] = f"{val / 1000:.1f}°C"
                        break
    except Exception:
        pass

    return intel_gpu

def parse_lshw_output():
    hw=[]
    if shutil.which("lshw"):
        try: out=subprocess.check_output(["lshw","-C","display"],universal_newlines=True)
        except: return hw
        for blk in re.split(r'\*-display',out):
            info={}
            for ln in blk.splitlines():
                ln=ln.strip()
                if ln.startswith("bus info:"): info["Bus"]=ln.split("bus info:")[1].strip()
                if ln.startswith("product:"): info["Product"]=ln.split("product:")[1].strip()
                if ln.startswith("vendor:"): info["Vendor"]=ln.split("vendor:")[1].strip()
                if ln.startswith("configuration:"): info["Config"]=ln.split("configuration:")[1].strip()
            if info and not re.search(r'nvidia',info.get('Vendor',''),re.I): hw.append(info)
    return hw

def print_gpu():
    print("\n+----------------- GPU Info -----------------+")
    nv=get_nvidia_info(); hw=parse_lshw_output(); intel_info = get_intel_gpu_info()
    buses={g['Bus'] for g in nv}
    for h in hw:
        if h.get('Bus') in buses:
            for g in nv:
                if g['Bus']==h['Bus']:
                    g.update({k:v for k,v in h.items() if k not in g})
                    break
        else:
            h.setdefault('Usage','N/A'); h.setdefault('Temperature','N/A')
            if 'Intel' in h.get('Vendor',''):
                h.update(intel_info)
            nv.append(h)
    if not nv: print("| No GPUs found.")
    else:
        for i,g in enumerate(nv,1):
            print(f"| GPU {i}:")
            for k in ["Product","Vendor","Bus","Config","Usage","Temperature"]:
                print(f"|   {k:<12}: {g.get(k,'N/A')}")
            print("|")
    print("+-------------------------------------------+\n")

def print_sys():
    print("\n+----------------- System Info -----------------+")
    uname = platform.uname()
    print(f"| System       : {uname.system}")
    print(f"| Node Name    : {uname.node}")
    print(f"| Release      : {uname.release}")
    print(f"| Version      : {uname.version}")
    print(f"| Machine      : {uname.machine}")
    print(f"| Processor    : {cpuinfo.get_cpu_info()["brand_raw"]}")
    print("+------------------------------------------------+\n")

def print_bat():
    print("\n+----------------- Battery Info -----------------+")
    batt = psutil.sensors_battery()
    if not batt:
        print("| No battery found.")
    else:
        status = "Charging" if batt.power_plugged else "Discharging"
        print(f"| Percent: {round(batt.percent, 2)}%")
        print(f"| Status : {status}")
        if batt.secsleft not in (psutil.POWER_TIME_UNLIMITED, psutil.POWER_TIME_UNKNOWN):
            hrs, rem = divmod(batt.secsleft, 3600)
            mins, _ = divmod(rem, 60)
            print(f"| Time Left: {hrs}h {mins}m")
    print("+------------------------------------------------+\n")

def main():
    ops = {
        '-cpu': print_cpu,
        '-mem': print_mem,
        '-disk': print_disk,
        '-io': print_io,
        '-net': print_net,
        '-gpu': print_gpu,
        '-sys': print_sys,
        '-bat': print_bat,
        '-help': print_help
    }
    if len(sys.argv) < 2:
        print_help()
        sys.exit()
    cmd = sys.argv[1].lower()
    if cmd == '-all':
        print_help()
        [f() for _, f in ops.items() if _ not in ('-help',)]
    elif cmd in ops:
        ops[cmd]()
    else:
        print(f"Unknown option: {cmd}")
        print_help()

if __name__=='__main__': main()