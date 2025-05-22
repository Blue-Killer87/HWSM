#!/usr/bin/env python3
"""
Simple hardware system monitor CLI using psutil.
Usage:
  ./hwsmCLI -cpu   # CPU stats
  ./hwsmCLI -mem   # Memory stats
  ./hwsmCLI -all   # Both CPU and Memory stats
  ./hwsmCLI -help  # Show this help message
If no parameters provided, shows help.
"""
import sys
import psutil
import platform
from textwrap import indent

def print_help():
    help_text = ("Usage: ./hwsmCLI [option]\n"
                 "Options:\n"
                 "  -cpu    Show CPU statistics (vendor, model, usage%)\n"
                 "  -mem    Show memory statistics (total, used, free, swap)\n"
                 "  -all    Show both CPU and memory statistics\n"
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
    elif arg == '-all':
        print_cpu()
        print_mem()
    elif arg == '-help':
        print_help()
    else:
        print(f"Unknown option: {arg}\n")
        print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()