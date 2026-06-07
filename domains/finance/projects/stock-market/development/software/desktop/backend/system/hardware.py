"""Detect system hardware to flag LLM model compatibility."""
import platform
import os
import subprocess


def _ram_gb() -> tuple[float, float]:
    """Return (total_ram_gb, available_ram_gb). Multi-method fallback."""
    # 1. psutil (most accurate)
    try:
        import psutil
        m = psutil.virtual_memory()
        return round(m.total / (1024 ** 3), 1), round(m.available / (1024 ** 3), 1)
    except ImportError:
        pass

    # 2. macOS sysctl (no dependencies)
    if platform.system() == "Darwin":
        try:
            total_bytes = int(subprocess.check_output(
                ["sysctl", "-n", "hw.memsize"], text=True).strip())
            total = round(total_bytes / (1024 ** 3), 1)
            # vm_stat for available pages
            try:
                vm = subprocess.check_output(["vm_stat"], text=True)
                page_size = 16384  # default 16 KB on Apple Silicon
                for line in vm.splitlines():
                    if "page size of" in line:
                        page_size = int(line.split()[-2])
                        break
                free_pages = 0
                for line in vm.splitlines():
                    if line.startswith("Pages free:"):
                        free_pages = int(line.split()[-1].rstrip("."))
                        break
                avail = round(free_pages * page_size / (1024 ** 3), 1)
            except Exception:
                avail = 0.0
            return total, avail
        except Exception:
            pass

    # 3. Linux /proc/meminfo
    try:
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":", 1)
                info[k.strip()] = int(v.split()[0]) * 1024  # kB → bytes
        total = round(info.get("MemTotal", 0) / (1024 ** 3), 1)
        avail = round(info.get("MemAvailable", 0) / (1024 ** 3), 1)
        return total, avail
    except Exception:
        pass

    return 0.0, 0.0


def get_hardware_info() -> dict:
    total_ram_gb, available_ram_gb = _ram_gb()

    system = platform.system()
    machine = platform.machine()
    is_apple_silicon = system == "Darwin" and machine == "arm64"

    return {
        "total_ram_gb": total_ram_gb,
        "available_ram_gb": available_ram_gb,
        "cpu_count": os.cpu_count() or 1,
        "machine": machine,
        "system": system,
        "is_apple_silicon": is_apple_silicon,
        "has_metal": is_apple_silicon,  # Metal always available on Apple Silicon
    }


def model_compatibility(model_ram_gb: float, hw: dict) -> str:
    """
    compatible  — enough RAM with comfortable headroom (4 GB free after model)
    marginal    — RAM is tight but might work
    insufficient — not enough RAM; listed anyway so user can decide
    """
    total = hw["total_ram_gb"]
    if total == 0:
        return "unknown"
    if total >= model_ram_gb + 4:
        return "compatible"
    if total >= model_ram_gb + 1:
        return "marginal"
    return "insufficient"
