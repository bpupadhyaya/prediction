"""Detect system hardware to flag LLM model compatibility."""
import platform
import os

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


def get_hardware_info() -> dict:
    if _HAS_PSUTIL:
        mem = psutil.virtual_memory()
        total_ram_gb = round(mem.total / (1024 ** 3), 1)
        available_ram_gb = round(mem.available / (1024 ** 3), 1)
    else:
        total_ram_gb = 0.0
        available_ram_gb = 0.0

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
