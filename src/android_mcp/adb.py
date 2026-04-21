import base64
import subprocess
import tempfile
from pathlib import Path


def run(args: list[str], device: str | None = None) -> str:
    cmd = ["adb"]
    if device:
        cmd += ["-s", device]
    cmd += args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"adb {' '.join(args)} failed")
    return result.stdout.strip()


def run_bytes(args: list[str], device: str | None = None) -> bytes:
    cmd = ["adb"]
    if device:
        cmd += ["-s", device]
    cmd += args
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode().strip())
    return result.stdout


def get_devices() -> list[dict]:
    output = run(["devices", "-l"])
    devices = []
    for line in output.splitlines()[1:]:
        if not line.strip() or "offline" in line:
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            info = {"serial": parts[0]}
            for part in parts[2:]:
                if ":" in part:
                    k, v = part.split(":", 1)
                    info[k] = v
            devices.append(info)
    return devices


def screenshot(device: str | None = None) -> str:
    """Returns base64-encoded PNG."""
    png_bytes = run_bytes(["exec-out", "screencap", "-p"], device)
    return base64.b64encode(png_bytes).decode()


def ui_dump(device: str | None = None) -> str:
    """Returns raw UIAutomator XML."""
    run(["shell", "uiautomator", "dump", "/sdcard/ui.xml"], device)
    return run(["shell", "cat", "/sdcard/ui.xml"], device)


def tap(x: int, y: int, device: str | None = None) -> None:
    run(["shell", "input", "tap", str(x), str(y)], device)


def swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300, device: str | None = None) -> None:
    run(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms)], device)


def input_text(text: str, device: str | None = None) -> None:
    # Escape special shell characters
    escaped = text.replace("\\", "\\\\").replace(" ", "%s").replace("'", "\\'")
    run(["shell", "input", "text", escaped], device)


def press_keyevent(keycode: str | int, device: str | None = None) -> None:
    run(["shell", "input", "keyevent", str(keycode)], device)


def launch_app(package: str, device: str | None = None) -> None:
    run(["shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"], device)


def stop_app(package: str, device: str | None = None) -> None:
    run(["shell", "am", "force-stop", package], device)


def install_apk(apk_path: str, device: str | None = None) -> str:
    return run(["install", "-r", apk_path], device)


def get_logcat(lines: int = 100, tag: str | None = None, device: str | None = None) -> str:
    args = ["logcat", "-d", "-t", str(lines)]
    if tag:
        args += [f"{tag}:V", "*:S"]
    return run(args, device)


def get_screen_size(device: str | None = None) -> tuple[int, int]:
    output = run(["shell", "wm", "size"], device)
    size = output.split(":")[-1].strip()
    w, h = size.split("x")
    return int(w), int(h)


def get_android_version(device: str | None = None) -> str:
    return run(["shell", "getprop", "ro.build.version.release"], device)


def get_package_version(package: str, device: str | None = None) -> str:
    output = run(["shell", "dumpsys", "package", package], device)
    for line in output.splitlines():
        if "versionName=" in line:
            return line.strip().split("versionName=")[-1].split()[0]
    return "unknown"
