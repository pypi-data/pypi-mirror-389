import os
import platform
import socket
import subprocess
from pathlib import Path

import psutil
from stv_utils import print  # 支持 hex 颜色码的同时, 不会破坏已有的 ANSI 转义序列, 这一点比 rich 好多了

from .loader import Loader  # , _SimpleLogo # 纯测试用的


_loader = Loader()
# logo = _SimpleLogo()
logo = _loader.logo


# noinspection PyBroadException
class PyFetch:
    def __init__(self):
        self.info = {}
        self._collect_all_info()

    @staticmethod
    def _run_command(cmd):
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return ""

    @staticmethod
    def _get_os_info():
        try:
            with open("/etc/os-release", "r", encoding="utf-8") as f:
                os_release = {}
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os_release[key] = value.strip('"')

                pretty_name = os_release.get("PRETTY_NAME", "")
                name = os_release.get("NAME", platform.system())

                if pretty_name:
                    return pretty_name
                elif name:
                    return name
        except:
            pass

        return f"{platform.system()} {platform.release()}"

    @staticmethod
    def _get_kernel():
        return platform.release()

    @staticmethod
    def _get_uptime():
        try:
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.readline().split()[0])

            minutes, seconds = divmod(uptime_seconds, 60)
            hours, minutes = divmod(minutes, 60)
            days, hours = divmod(hours, 24)

            if days > 0:
                return f"{int(days)} days, {int(hours)} hours"
            elif hours > 0:
                return f"{int(hours)} hours, {int(minutes)} mins"
            else:
                return f"{int(minutes)} mins"
        except:
            return "Unknown"

    def _get_packages(self):
        packages = []

        # dpkg packages
        dpkg_result = self._run_command("dpkg-query -f '.\n' -W | wc -l")
        if dpkg_result:
            packages.append(f"{dpkg_result} (dpkg)")

        # snap packages
        snap_result = self._run_command("snap list 2>/dev/null | wc -l")
        if snap_result and snap_result != "0":
            # 减去标题行
            snap_count = int(snap_result) - 1 if snap_result.isdigit() else 0
            if snap_count > 0:
                packages.append(f"{snap_count} (snap)")

        # flatpak packages
        flatpak_result = self._run_command("flatpak list --app 2>/dev/null | wc -l")
        if flatpak_result and flatpak_result.isdigit() and int(flatpak_result) > 0:
            packages.append(f"{flatpak_result} (flatpak)")

        return ", ".join(packages) if packages else "Unknown"

    def _get_shell(self):
        shell_path = os.environ.get("SHELL", "")
        if shell_path:
            shell_name = os.path.basename(shell_path)
            # 获取shell版本
            version = self._run_command(f"{shell_path} --version | head -n1")
            return f"{shell_name} {version.split()[-1]}" if version else shell_name
        return "Unknown"

    def _get_desktop_info(self):
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
        if not desktop:
            desktop = os.environ.get("DESKTOP_SESSION", "Unknown")

        theme = "Unknown"
        icon_theme = "Unknown"

        try:
            theme_result = self._run_command("gsettings get org.gnome.desktop.interface gtk-theme 2>/dev/null")
            if theme_result and theme_result != "''":
                theme = theme_result.strip("'")

            icon_result = self._run_command("gsettings get org.gnome.desktop.interface icon-theme 2>/dev/null")
            if icon_result and icon_result != "''":
                icon_theme = icon_result.strip("'")
        except:
            pass

        return desktop, theme, icon_theme

    @staticmethod
    def _get_terminal():
        term = os.environ.get("TERM", "")
        term_program = os.environ.get("TERM_PROGRAM", "")

        if term_program:
            term_version = os.environ.get("TERM_PROGRAM_VERSION", "")
            return f"{term_program} {term_version}".strip()
        elif "TERMINAL" in os.environ:
            return os.environ["TERMINAL"]
        else:
            try:
                parent_pid = os.getppid()
                parent_name = Path(f"/proc/{parent_pid}/comm").read_text().strip()
                return parent_name
            except:
                pass

        return term if term else "Unknown"

    @staticmethod
    def _get_cpu_info():
        try:
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read()

            for line in cpuinfo.splitlines():
                if "model name" in line:
                    cpu_model = line.split(":")[1].strip()
                    break
            else:
                cpu_model = platform.processor()

            cores = psutil.cpu_count(logical=False) or 1
            logical_cores = psutil.cpu_count(logical=True) or cores

            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "cpu MHz" in line:
                            freq_mhz = float(line.split(":")[1].strip())
                            freq_ghz = freq_mhz / 1000
                            break
                    else:
                        freq_ghz = "Unknown"
            except:
                freq_ghz = "Unknown"

            if freq_ghz != "Unknown":
                return f"{cpu_model} ({logical_cores}) @ {freq_ghz:.2f}GHz"
            else:
                return f"{cpu_model} ({logical_cores})"

        except Exception as _:
            return f"{platform.processor()} (Unknown)"

    def _get_gpu_info(self):
        gpu_info = ""

        nvidia_result = self._run_command("nvidia-smi --query-gpu=gpu_name --format=csv,noheader 2>/dev/null")
        if nvidia_result:
            gpu_lines = nvidia_result.split('\n')
            gpus = []
            for line in gpu_lines[:]:
                if line.strip():
                    gpu_name = line.strip()
                    if "NVIDIA" in gpu_name:
                        gpu_name = gpu_name.replace("NVIDIA ", "")
                    gpus.append(gpu_name)
            if gpus:
                gpu_info = ", ".join(gpus)

        if not gpu_info:
            lspci_result = self._run_command("lspci | grep -i 'vga\\|3d\\|display'")
            if lspci_result:
                gpu_lines = lspci_result.split('\n')
                gpus = []
                for line in gpu_lines[:]:
                    if ':' in line:
                        gpu_name = line.split(':')[-1].strip()
                        gpu_name = gpu_name.replace(" Corporation", "")
                        gpus.append(gpu_name)
                if gpus:
                    gpu_info = ", ".join(gpus)

        if not gpu_info:
            amd_result = self._run_command("lspci | grep -i 'amd\\/ati'")
            if amd_result:
                gpu_lines = amd_result.split('\n')
                gpus = []
                for line in gpu_lines[:2]:
                    if ':' in line:
                        gpu_name = line.split(':')[-1].strip()
                        gpus.append(gpu_name)
                if gpus:
                    gpu_info = ", ".join(gpus)

        if not gpu_info:
            intel_result = self._run_command("lspci | grep -i 'intel' | grep -i 'vga'")
            if intel_result:
                gpu_lines = intel_result.split('\n')
                gpus = []
                for line in gpu_lines[:]:
                    if ':' in line:
                        gpu_name = line.split(':')[-1].strip()
                        gpus.append(gpu_name)
                if gpus:
                    gpu_info = ", ".join(gpus)

        return gpu_info if gpu_info else "Unknown"

    @staticmethod
    def _get_memory_info():
        try:
            mem = psutil.virtual_memory()
            total_gb = mem.total / (1024 ** 3)
            used_gb = mem.used / (1024 ** 3)

            return f"{used_gb:.1f}GiB / {total_gb:.1f}GiB"
        except:
            return "Unknown"

    @staticmethod
    def _get_username_hostname():
        try:
            username = os.getlogin()
        except FileNotFoundError:
            username = os.environ.get("USER", os.environ.get("USERNAME", "unknown"))
        hostname = socket.gethostname()
        return username, hostname

    def _collect_all_info(self):
        username, hostname = self._get_username_hostname()
        desktop, theme, icon_theme = self._get_desktop_info()

        self.info = {
            "username": username,
            "hostname": hostname,
            "os": self._get_os_info(),
            "kernel": self._get_kernel(),
            "uptime": self._get_uptime(),
            "packages": self._get_packages(),
            "shell": self._get_shell(),
            "desktop": desktop,
            "theme": theme,
            "icon_theme": icon_theme,
            "terminal": self._get_terminal(),
            "cpu": self._get_cpu_info(),
            "gpu": self._get_gpu_info(),
            "memory": self._get_memory_info()
        }

    def get_ascii_logo(self):
        os_name = self.info["os"].lower()
        for key in logo.keys():
            if key in os_name:
                return logo.get(key, "")
        return ""

    def display(self):
        ascii_logo = self.get_ascii_logo()

        if not ascii_logo:
            self._display_info_only()
            return

        logo_lines = ascii_logo.split('\n')
        max_logo_width = max(len(line) for line in logo_lines)

        info_lines = self._get_info_lines()

        logo_height = len(logo_lines)
        info_height = len(info_lines)
        start_pos = max(0, (logo_height - info_height) // 2)

        for i in range(max(logo_height, start_pos + info_height)):
            if i < logo_height:
                logo_line = logo_lines[i]
            else:
                logo_line = ""

            logo_padded = logo_line.ljust(max_logo_width)

            info_index = i - start_pos
            if 0 <= info_index < len(info_lines):
                info_line = info_lines[info_index]
            else:
                info_line = ""

            if logo_padded or info_line:
                print(f"{logo_padded}  {info_line}")

    def _get_info_lines(self):
        labels_and_values = [
            ("OS", self.info['os']),
            ("Kernel", self.info['kernel']),
            ("Uptime", self.info['uptime']),
            ("Packages", self.info['packages']),
            ("Shell", self.info['shell']),
            ("DE", self.info['desktop']),
            ("Theme", self.info['theme']),
            ("Icons", self.info['icon_theme']),
            ("Terminal", self.info['terminal']),
            ("CPU", self.info['cpu']),
            ("GPU", self.info['gpu']),
            ("Memory", self.info['memory'])
        ]

        max_label_length = max(len(label) for label, _ in labels_and_values)

        info_lines = [
            f"\033[1m{self.info['username']}@{self.info['hostname']}\033[0m",
            "\033[2m" + "─" * 40 + "\033[0m"
        ]

        for label, value in labels_and_values:
            padded_label = label.ljust(max_label_length)
            info_lines.append(f";00ffff;{padded_label}\033[0m: {value}")

        return info_lines

    def _display_info_only(self):
        info_lines = self._get_info_lines()
        for line in info_lines:
            print(line)


def main():
    pyfetch = PyFetch()
    pyfetch.display()


if __name__ == "__main__":
    main()
