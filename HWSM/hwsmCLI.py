#!/usr/bin/env python3
"""
Simple hardware system monitor CLI using psutil.
Usage:
  ./hwsmCLI -cpu    # CPU stats
  ./hwsmCLI -mem    # Memory stats
  ./hwsmCLI -disk   # Disk and partition stats
  ./hwsmCLI -io     # Disk I/O stats
  ./hwsmCLI -gpu    # GPU stats
  ./hwsmCLI -net    # Network I/O stats
  ./hwsmCLI -all    # CPU, Memory, Disk, I/O, Network, and GPU stats
  ./hwsmCLI -help   # Show this help message
If no parameters provided, shows help.
"""
import sys
import psutil
import platform
import subprocess
import shutil
import re

def print_help():
    help_text = ("Usage: ./hwsmCLI [option]\n"
                 "Options:\n"
                 "  -cpu    Show CPU statistics (vendor, model, usage%)\n"
                 "  -mem    Show memory statistics (total, used, free, swap)\n"
                 "  -disk   Show disk and partition statistics\n"
                 "  -io     Show disk I/O statistics\n"
                 "  -net    Show network I/O statistics\n"
                 "  -gpu    Show GPU statistics\n"
                 "  -all    Show CPU, memory, disk, I/O, network, and GPU statistics\n"
                 "  -help   Show this help message\n")
    print("+---------------- Help ----------------+")
    print(help_text)
    print("+-------------------------------------+")

def print_cpu():
    processor_info = platform.processor() or platform.uname().processor
    physical = psutil.cpu_count(logical=False)
    logical = psutil.cpu_count(logical=True)
    per_core = psutil.cpu_percent(percpu=True, interval=1)
    total_cpu = psutil.cpu_percent()

    print("+--------------- CPU Info ---------------+")
    print(f"| Vendor/Model     : {processor_info}")
    print(f"| Physical cores   : {physical}")
    print(f"| Total cores      : {logical}")
    print("| CPU Usage Per Core:")
    for i, percentage in enumerate(per_core):
        print(f"|   Core {i:<2}         : {percentage}%")
    print(f"| Total CPU Usage  : {total_cpu}%")
    print("+----------------------------------------+")

def print_mem():
    vm = psutil.virtual_memory()
    sm = psutil.swap_memory()

    print("+--------------- Memory Info ------------+")
    print(f"| Total Memory     : {get_size(vm.total)}")
    print(f"| Used Memory      : {get_size(vm.used)}")
    print(f"| Available Memory : {get_size(vm.available)}")
    print(f"| Memory Usage     : {vm.percent}%")
    print("|")
    print(f"| Total Swap       : {get_size(sm.total)}")
    print(f"| Used Swap        : {get_size(sm.used)}")
    print(f"| Free Swap        : {get_size(sm.free)}")
    print(f"| Swap Usage       : {sm.percent}%")
    print("+----------------------------------------+")

def print_disk():
    print("+---------------- Disk Info ----------------+")
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
    print("+------------------------------------------+")

def print_io():
    io = psutil.disk_io_counters(perdisk=True)
    print("+----------------- Disk I/O -----------------+")
    for disk, stats in io.items():
        print(f"| Disk: {disk}")
        print(f"|   Read Count     : {stats.read_count}")
        print(f"|   Write Count    : {stats.write_count}")
        print(f"|   Read Bytes     : {get_size(stats.read_bytes)}")
        print(f"|   Write Bytes    : {get_size(stats.write_bytes)}")
        print(f"|   Read Time (ms) : {stats.read_time}")
        print(f"|   Write Time (ms): {stats.write_time}")
        print("|")
    print("+-------------------------------------------+")

def print_net():
    net_io = psutil.net_io_counters(pernic=True)
    print("+---------------- Network I/O ----------------+")
    for nic, stats in net_io.items():
        print(f"| Interface: {nic}")
        print(f"|   Bytes Sent    : {get_size(stats.bytes_sent)}")
        print(f"|   Bytes Received: {get_size(stats.bytes_recv)}")
        print(f"|   Packets Sent  : {stats.packets_sent}")
        print(f"|   Packets Recv  : {stats.packets_recv}")
        print("|")
    print("+--------------------------------------------+")

def parse_lshw_output(output):
    gpus = []
    blocks = re.split(r'\*-display', output)
    for block in blocks:
        lines = block.strip().split('\n')
        gpu = {}
        for line in lines:
            line = line.strip()
            if line.startswith("product:"):
                gpu['Product'] = line.split("product:")[1].strip()
            elif line.startswith("vendor:"):
                gpu['Vendor'] = line.split("vendor:")[1].strip()
            elif line.startswith("configuration:"):
                gpu['Config'] = line.split("configuration:")[1].strip()
            elif line.startswith("bus info:"):
                gpu['Bus'] = line.split("bus info:")[1].strip()
        if gpu:
            gpus.append(gpu)
    return gpus

def print_gpu():
    print("+----------------- GPU Info -----------------+")
    if shutil.which("lshw") is None:
        print("| 'lshw' utility is not installed. Please install it to use GPU stats.")
        print("+-------------------------------------------+")
        return

    try:
        output = subprocess.check_output(["lshw", "-C", "display"], universal_newlines=True)
        gpus = parse_lshw_output(output)
        if not gpus:
            print("| No GPUs detected.")
        for i, gpu in enumerate(gpus):
            print(f"| GPU {i + 1}:")
            for key, value in gpu.items():
                print(f"|   {key:<10}: {value}")
            print("|")
    except subprocess.CalledProcessError:
        print("| Failed to retrieve GPU information.")
    print("+-------------------------------------------+")

def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor
    return f"{bytes:.2f}Y{suffix}"

def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    arg = sys.argv[1].lower()
    if arg == '-cpu':
        print_cpu()
    elif arg == '-mem':
        print_mem()
    elif arg == '-disk':
        print_disk()
    elif arg == '-io':
        print_io()
    elif arg == '-net':
        print_net()
    elif arg == '-gpu':
        print_gpu()
    elif arg == '-all':
        print_cpu()
        print_mem()
        print_disk()
        print_io()
        print_net()
        print_gpu()
    elif arg == '-help':
        print_help()
    else:
        print(f"Unknown option: {arg}\n")
        print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
