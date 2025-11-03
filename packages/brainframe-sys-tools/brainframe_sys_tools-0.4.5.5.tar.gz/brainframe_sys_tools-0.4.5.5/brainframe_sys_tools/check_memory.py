import os
import resource
import random
import psutil
import argparse
from datetime import datetime
import time


def read_file(file_path):
    with open(file_path, "r") as f:
        return f.read().strip()


def bytes_to_mib(bytes):
    return int(bytes) / 1024 / 1024


def cgroup_usage(uid):
    limit_in_bytes = read_file(
        f"/sys/fs/cgroup/memory/user.slice/user-{uid}.slice/memory.limit_in_bytes"
    )
    max_usage_in_bytes = read_file(
        f"/sys/fs/cgroup/memory/user.slice/user-{uid}.slice/memory.max_usage_in_bytes"
    )
    usage_in_bytes = read_file(
        f"/sys/fs/cgroup/memory/user.slice/user-{uid}.slice/memory.usage_in_bytes"
    )
    return limit_in_bytes, max_usage_in_bytes, usage_in_bytes


def print_cgroup_usage(uid):
    limit_in_bytes, max_usage_in_bytes, usage_in_bytes = cgroup_usage(uid)
    print(f"/sys/fs/cgroup/memory/user.slice/user-{uid}.slice/")
    print(f"    Limit in bytes: {bytes_to_mib(limit_in_bytes)} MiB")
    print(f"    Max usage in bytes: {bytes_to_mib(max_usage_in_bytes)} MiB")
    print(f"    Usage in bytes: {bytes_to_mib(usage_in_bytes)} MiB")


def print_resource_usage():
    # Print memory usage
    usage = resource.getrusage(resource.RUSAGE_SELF)
    print(f"resource.getrusage()")
    print(f"    Memory Usage: {usage.ru_maxrss / 1024} MiB bytes")


def process_memory_info(pid):
    try:
        process = psutil.Process(pid)
        process_mem_info = process.memory_info()
        rss_in_bytes = process_mem_info.rss  # in bytes
        return rss_in_bytes
    except psutil.NoSuchProcess:
        return 0


def print_process_memory_info(pid):
    rss_in_bytes = process_memory_info(pid)
    print(f"psutil.Process({pid}).memory_info()")
    if rss_in_bytes is not None:
        print(f"    RSS: {bytes_to_mib(rss_in_bytes)} MiB")  # convert bytes to MiB
    else:
        print(f"    No such process")


def system_memory_usage():
    # Get the system memory usage
    mem_info = psutil.virtual_memory()

    # Total physical memory
    total = mem_info.total  # in bytes

    # Available physical memory
    available = mem_info.available  # in bytes

    # Used physical memory
    used = mem_info.used  # in bytes

    # Memory used for buffering
    buffers = mem_info.buffers if hasattr(mem_info, "buffers") else 0  # in bytes

    # Memory used for caching
    cached = mem_info.cached if hasattr(mem_info, "cached") else 0  # in bytes
    return total, available, used, buffers, cached


def print_system_memory_usage():
    total, available, used, buffers, cached = system_memory_usage()
    print(f"psutil.virtual_memory()")
    print(f"    Total physical memory: {bytes_to_mib(total)} MiB")
    print(f"    Available physical memory: {bytes_to_mib(available)} MiB")
    print(f"    Used physical memory: {bytes_to_mib(used)} MiB")
    print(f"    Buffered memory: {bytes_to_mib(buffers)} MiB")
    print(f"    Cached memory: {bytes_to_mib(cached)} MiB")


def draw_bar_chart(data, graph_max):
    colors = ["\033[91m", "\033[92m", "\033[93m", "\033[94m", "\033[95m", "\033[0m"]
    for i in range(len(data)):
        label, min_val, value, max_val = data[i]
        value = max(min_val, min(value, max_val))

        # Normalize the value to the range of the graph
        normalized_value = (
            int((value - min_val) / (max_val - min_val) * graph_max)
            if max_val != min_val
            else 0
        )

        # Draw the label, min, max, and value with color
        color = colors[i % len(colors)]
        pct = value * 100 / max_val
        print(
            f"{label:<10} {min_val:<2}[{color}{'|' * normalized_value}\033[0m {value:<5} {' ' * (graph_max - normalized_value)}{pct:.2f}%] {max_val:<5}"
        )


def monitor_memory(uid, pid):
    total, available, used, buffers, cached = system_memory_usage()
    limit_in_bytes, max_usage_in_bytes, usage_in_bytes = cgroup_usage(uid)
    rss_in_bytes = process_memory_info(pid)
    data = [
        (
            " system used / system total",
            0,
            int(bytes_to_mib(used)),
            int(bytes_to_mib(total)),
        ),
        (
            "cgroup usage / system  used",
            0,
            int(bytes_to_mib(usage_in_bytes)),
            int(bytes_to_mib(used)),
        ),
        (
            " process rss / cgroup usage",
            0,
            int(bytes_to_mib(rss_in_bytes)),
            int(bytes_to_mib(usage_in_bytes)),
        ),
    ]
    draw_bar_chart(data, 50)


def main():
    parser = argparse.ArgumentParser(description="Get memory usage for a process.")
    parser.add_argument(
        "-u",
        "--uid",
        type=int,
        default=os.getuid(),
        help="The process ID to get memory usage for.",
    )

    parser.add_argument(
        "-p",
        "--pid",
        type=int,
        default=os.getpid(),
        help="The process ID to get memory usage for.",
    )

    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=60,
        help="Interval for the memory usage monitor.",
    )

    parser.add_argument(
        "-k",
        "--key",
        action="store_true",
        help="Wait for a key to monitor the memory usage.",
    )

    args = parser.parse_args()

    print(f"User ID: {args.uid}")
    print(f"Process ID: {args.pid}")

    print_system_memory_usage()
    # No way to specify pid
    # print_resource_usage()
    print_cgroup_usage(args.uid)
    print_process_memory_info(args.pid)

    if args.key:
        print("Enter to continue, Q to quit: ")

    while True:
        # Current date and time
        now = datetime.now()

        # Format timestamp
        timestamp = now.strftime("%d-%m-%Y %H:%M:%S")

        print(timestamp)

        monitor_memory(args.uid, args.pid)

        if args.key:
            # wait for a key press
            key = input()
            if key == "q" or key == "Q":
                break
        else:
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
