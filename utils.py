#
# utils.py - Модуль содержащий все необходимые функции для получения информации из системы.
#


# Импортируем:
import os
import time
import socket
import psutil


# Получить вывод команды:
def get_cmd_result(cmd: str) -> str:
    try:
        with os.popen(cmd) as f:
            value = str(f.read().strip())
        return value
    except Exception:
        return "n/a"


# Прочитать информацию об оперативной памяти:
def _read_meminfo_() -> dict:
    info = {}
    with open("/proc/meminfo") as f:
        for L in f:
            key, val = L.split(":", 1)
            info[key] = int(val.split()[0])
    return info


# Округлить размер памяти:
def format_memory_size(bytes_size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(bytes_size)
    for unit in units:
        if size < 1024:
            return f"{round(size, 2)} {unit}"
        size /= 1024
    return f"{bytes_size} B"


# Получить сколько времени прошло с момента запуска системы:
def format_uptime() -> str:
    with open("/proc/uptime", "r") as f:
        uptime_seconds = float(f.readline().split()[0])
    minutes, seconds = divmod(int(uptime_seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{days:02}:{hours:02}:{minutes:02}:{seconds:02}"


# Глобальные переменные сети:
class NetVars:
    # Название сетей для отслеживания:
    net_lan_name: str = "eth0"
    net_wifi_name: str = "wlan0"

    # Сохранённые прошлые значения всего трафика:
    net_lan_rx_total: int = 0  # Получено в байтах.
    net_lan_tx_total: int = 0  # Отправлено в байтах.
    net_wifi_rx_total: int = 0  # Получено в байтах.
    net_wifi_tx_total: int = 0  # Отправлено в байтах.

    # Сколько трафика передаётся (B/s):
    net_lan_rx_bs: float = 0.0
    net_lan_tx_bs: float = 0.0
    net_wifi_rx_bs: float = 0.0
    net_wifi_tx_bs: float = 0.0

    # Пиковые скорости (B/s):
    net_max_lan_rx_bs: int = 0
    net_max_lan_tx_bs: int = 0
    net_max_wifi_rx_bs: int = 0
    net_max_wifi_tx_bs: int = 0

    # Время последнего сброса пиков:
    _last_reset_ = time.time()
    net_counter_timeout: float = 5.0  # Обновлять каждые 5 секунд.

    # Функция отдельного потока для отслеживания изменения трафика интернета:
    @staticmethod
    def thread_network_traffic_check() -> None:
        while True:
            now = time.time()
            # Получаем старый трафик:
            lan_rx_old = NetVars.net_lan_rx_total
            lan_tx_old = NetVars.net_lan_tx_total
            wifi_rx_old = NetVars.net_wifi_rx_total
            wifi_tx_old = NetVars.net_wifi_tx_total

            try:
                # Получаем трафик по LAN:
                lan_rx = int(get_cmd_result(f"cat /sys/class/net/{NetVars.net_lan_name}/statistics/rx_bytes"))
                lan_tx = int(get_cmd_result(f"cat /sys/class/net/{NetVars.net_lan_name}/statistics/tx_bytes"))

                # Получаем трафик по WiFi:
                wifi_rx = int(get_cmd_result(f"cat /sys/class/net/{NetVars.net_wifi_name}/statistics/rx_bytes"))
                wifi_tx = int(get_cmd_result(f"cat /sys/class/net/{NetVars.net_wifi_name}/statistics/tx_bytes"))
            except Exception:
                lan_rx = lan_rx_old
                lan_tx = lan_tx_old
                wifi_rx = wifi_rx_old
                wifi_tx = wifi_tx_old

            # Вычисляем дельту передачи данных в б/c:
            NetVars.net_lan_rx_bs = lan_rx-lan_rx_old
            NetVars.net_lan_tx_bs = lan_tx-lan_tx_old
            NetVars.net_wifi_rx_bs = wifi_rx-wifi_rx_old
            NetVars.net_wifi_tx_bs = wifi_tx-wifi_tx_old

            # Обновляем данные всего трафика:
            NetVars.net_lan_rx_total = lan_rx
            NetVars.net_lan_tx_total = lan_tx
            NetVars.net_wifi_rx_total = wifi_rx
            NetVars.net_wifi_tx_total = wifi_tx

            # Если пора сбрасывать пики:
            if now - NetVars._last_reset_ >= NetVars.net_counter_timeout:
                NetVars.net_max_lan_rx_bs = 0.0
                NetVars.net_max_lan_tx_bs = 0.0
                NetVars.net_max_wifi_rx_bs = 0.0
                NetVars.net_max_wifi_tx_bs = 0.0
                NetVars._last_reset_ = now

            # Обновить пики:
            NetVars.net_max_lan_rx_bs = max(NetVars.net_max_lan_rx_bs, NetVars.net_lan_rx_bs)
            NetVars.net_max_lan_tx_bs = max(NetVars.net_max_lan_tx_bs, NetVars.net_lan_tx_bs)
            NetVars.net_max_wifi_rx_bs = max(NetVars.net_max_wifi_rx_bs, NetVars.net_wifi_rx_bs)
            NetVars.net_max_wifi_tx_bs = max(NetVars.net_max_wifi_tx_bs, NetVars.net_wifi_tx_bs)

            time.sleep(1.0)  # Обновляем данные каждую секунду.


# Глобальные переменные процессора:
class CPUCores:
    check_interval: float = 1.0  # Раз в 1 секунду проверяем загруженность ядер.
    cpu_cores: list = [["Core 0", "0.0"], ["Core 1", "0.0"], ["Core 2", "0.0"], ["Core 3", "0.0"]]
    cpu_usage: float = 0.0

    # Функция отдельного потока для отслеживания загрузки ядер процессора:
    @staticmethod
    def thread_cpu_cores_check() -> None:
        while True:
            CPUCores.cpu_cores = [
                (f"Core {i}", str(pct))
                for i, pct in enumerate(psutil.cpu_percent(interval=CPUCores.check_interval, percpu=True))]
            CPUCores.cpu_usage = round(sum([float(b) for a, b in CPUCores.cpu_cores])/len(CPUCores.cpu_cores), 1)


# Глобальные переменные диска
class Disk:
    # Скорость чтения/записи на диск (B/s):
    disk_read_bs:  int = 0
    disk_write_bs: int = 0

    # Функция отдельного потока для отслеживания нагрузки на диск:
    @staticmethod
    def thread_disk_check() -> None:
        interval = 1.0
        while True:
            disk1 = psutil.disk_io_counters()
            time.sleep(interval)
            disk2 = psutil.disk_io_counters()
            Disk.disk_read_bs  = (disk2.read_bytes-disk1.read_bytes)   / interval
            Disk.disk_write_bs = (disk2.write_bytes-disk1.write_bytes) / interval


# Получить имя хоста:
def get_hostname() -> str:
    return get_cmd_result("hostname")


# Получить IPv4 адрес (первый внешний адрес):
def get_ipv4() -> str:
    try:
        # Соединяемся со внешним адресом, чтобы узнать свой исходящий IP:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "n/a"


# Получить имя пользователя:
def get_username() -> str:
    return get_cmd_result("echo $USER")


# Получить платформу:
def get_platform() -> str:
    return get_cmd_result("uname -s")


# Получить имя системы:
def get_osname() -> str:
    try:
        with os.popen("cat /etc/issue") as f:
            value = " ".join(w for w in f.read().strip().split() if w not in ["\\n", "\\l"])
        return str(value)
    except Exception:
        return "n/a"


# Получить частоту h264 (в ГГц):
def get_h264_freq() -> str:
    try:
        value = get_cmd_result("vcgencmd measure_clock h264")
        return str(round(int(value.split("=")[1])/1000/1000/1000, 2))
    except Exception:
        return "n/a"


# Получить частоту isp (в ГГц):
def get_isp_freq() -> str:
    try:
        value = get_cmd_result("vcgencmd measure_clock isp")
        return str(round(int(value.split("=")[1])/1000/1000/1000, 2))
    except Exception:
        return "n/a"


# Получить частоту uart (в ГГц):
def get_uart_freq() -> str:
    try:
        value = get_cmd_result("vcgencmd measure_clock uart")
        return str(round(int(value.split("=")[1])/1000/1000/1000, 2))
    except Exception:
        return "n/a"


# Получить архитектуру процессора:
def get_arch() -> str:
    return get_cmd_result("uname -m")


# Получить разрядность процессора:
def get_cpu_bits() -> str:
    return get_cmd_result("getconf LONG_BIT")


# Получить температуру процессора:
def get_cpu_temp() -> str:
    values = []
    try:
        for i in range(5):  # 5 раз запрашиваем температуру чтобы узнать среднее значение:
            values.append(int(get_cmd_result("cat /sys/class/thermal/thermal_zone0/temp"))/1000)
        return str(round(sum(values)/len(values), 2))
    except Exception:
        return "n/a"


# Получить текущую частоту процессора (в ГГц):
def get_cpu_freq() -> str:
    try:
        value = get_cmd_result("vcgencmd measure_clock arm")
        return str(round(int(value.split("=")[1])/1000/1000/1000, 2))
    except Exception:
        return "n/a"


# Получить минимальную частоту процессора (в ГГц):
def get_cpu_min_freq() -> str:
    try:
        return str(round(int(get_cmd_result("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq"))/1000/1000, 2))
    except Exception:
        return "n/a"


# Получить максимальную частоту процессора (в ГГц):
def get_cpu_max_freq() -> str:
    try:
        return str(round(int(get_cmd_result("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq"))/1000/1000, 2))
    except Exception:
        return "n/a"


# Получить все частоты процессора процессора (в ГГц):
def get_cpu_all_freq() -> str:
    value = get_cmd_result("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_frequencies")
    return ", ".join(str(round(int(v)/1000/1000, 2)) for v in value.split())


# Получить общую загруженность процессора:
def get_cpu_usage() -> float:
    return CPUCores.cpu_usage


# Получить загруженность каждого ядра процессора в процентах:
def get_cpu_cores() -> list:
    return CPUCores.cpu_cores


# Получить текущую частоту графического процессора (в ГГц):
def get_gpu_freq() -> str:
    try:
        value = get_cmd_result("vcgencmd measure_clock v3d")
        return str(round(int(value.split("=")[1])/1000/1000/1000, 2))
    except Exception:
            return "n/a"


# Получить минимальную частоту графического процессора (в ГГц):
def get_gpu_min_freq() -> str:
    try:
        value = get_cmd_result("vcgencmd get_config gpu_freq_min")
        return str(round(int(value.split("=")[1])/1000, 2))
    except Exception:
        return "n/a"


# Получить сколько свободно пространства в оперативной памяти в байтах:
def get_ram_free_size() -> int:
    return int(_read_meminfo_().get("MemAvailable", 0)*1024)


# Получить сколько занято пространства в оперативной памяти в байтах:
def get_ram_used_size() -> int:
    info = _read_meminfo_()
    return int((info.get("MemTotal", 0)-info.get("MemAvailable", 0))*1024)


# Получить сколько всего пространства в оперативной памяти в байтах:
def get_ram_total_size() -> int:
    return int(_read_meminfo_().get("MemTotal", 0)*1024)


# Получить сколько свободного пространства в хранилище в байтах:
def get_storage_free_size() -> int|str:
    return psutil.disk_usage("/").free


# Получить сколько занято пространства в хранилище в байтах:
def get_storage_used_size() -> int|str:
    return psutil.disk_usage("/").used


# Получить сколько всего пространства в хранилище в байтах:
def get_storage_total_size() -> int|str:
    return psutil.disk_usage("/").total


# Чтение с диска (B/s)
def get_disk_read_bs() -> int:
    return int(Disk.disk_read_bs)


# Запись на диск (B/s)
def get_disk_write_bs() -> int:
    return int(Disk.disk_write_bs)


# Получить сколько байт в секунду получаем по LAN:
def get_lan_rx_bs() -> int:
    return int(NetVars.net_lan_rx_bs)


# Получить сколько байт в секунду отправляем по LAN:
def get_lan_tx_bs() -> int:
    return int(NetVars.net_lan_tx_bs)


# Получить сколько байт в секунду получаем по WiFi:
def get_wifi_rx_bs() -> int:
    return int(NetVars.net_wifi_rx_bs)


# Получить сколько байт в секунду отправляем по WiFi:
def get_wifi_tx_bs() -> int:
    return int(NetVars.net_wifi_tx_bs)


# Получить всего сколько трафика было загружено в байтах по LAN:
def get_lan_rx_b() -> int:
    return int(NetVars.net_lan_rx_total)


# Получить всего сколько трафика было выгружено в байтах по LAN:
def get_lan_tx_b() -> int:
    return int(NetVars.net_lan_tx_total)


# Получить всего сколько трафика было загружено в байтах по WiFi:
def get_wifi_rx_b() -> int:
    return int(NetVars.net_wifi_rx_total)


# Получить всего сколько трафика было выгружено в байтах по WiFi:
def get_wifi_tx_b() -> int:
    return int(NetVars.net_wifi_tx_total)


# Получить сколько байт было получено в пике по LAN:
def get_lan_max_rx_bs() -> int:
    return int(NetVars.net_max_lan_rx_bs)


# Получить сколько байт было отправлено в пике по LAN:
def get_lan_max_tx_bs() -> int:
    return int(NetVars.net_max_lan_tx_bs)


# Получить сколько байт было получено в пике по WiFi:
def get_wifi_max_rx_bs() -> int:
    return int(NetVars.net_max_wifi_rx_bs)


# Получить сколько байт было отправлено в пике по WiFi:
def get_wifi_max_tx_bs() -> int:
    return int(NetVars.net_max_wifi_tx_bs)


"""
    < Pi-Status-Panel >
    By LukovDev (@mr_lukov).
    License: MIT
    lakuworx@gmail.com

    Thank you for Using!
"""
