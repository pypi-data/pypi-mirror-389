# brainframe-sys-tools

Python CLI tools for monitoring and debugging BrainFrame system deployment.

## Installation

```bash
pip install brainframe-sys-tools
```

## Usage

```bash
brainframe-sys-tools <command> [options]
```

### Commands

- `perf_monitor` - Monitor CPU, GPU, memory, storage, and temperatures
- `fps_monitor` - Monitor BrainFrame stream FPS and throughput
- `service_monitor` - Monitor BrainFrame service health
- `sys_info` - Display system information
- `ssh_tunnel` - Create SSH tunnels

### Example

```bash
brainframe-sys-tools perf_monitor
brainframe-sys-tools fps_monitor --server-url http://localhost
```

## Help

```bash
brainframe-sys-tools <command> --help
```
