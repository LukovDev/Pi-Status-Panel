#
# server.py - Основной файл программы. Поднимает и серверную часть, и сайт.
#
# Запустить:
# python3 -m uvicorn server:app --host 0.0.0.0 --port 8888 --reload
#
# Подключиться:
# http://rpi5.local:8888/
#
# <!> ГДЕ НАПИСАНО "rpi5.local" ЗАМЕНИТЕ НА АЙПИ ИЛИ ИМЯ ВАШЕГО ХОСТА <!>
#


# Импортируем:
from utils import *
from threading import Thread
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse


app = FastAPI()


# Разрешаем CORS:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Подключаем папки как статику:
app.mount("/styles", StaticFiles(directory="styles"), name="styles")
app.mount("/js", StaticFiles(directory="js"), name="js")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


# Запускаем отдельный поток для отслеживания трафика сети:
Thread(target=NetVars.thread_network_traffic_check, args=(), daemon=True).start()


# Запускаем отдельный поток для отслеживания нагрузки на ядра процессора:
Thread(target=CPUCores.thread_cpu_cores_check, args=(), daemon=True).start()


# Запускаем отдельный поток для отслеживания нагрузки на диск:
Thread(target=Disk.thread_disk_check, args=(), daemon=True).start()

# Название сетей для отслеживания:
NetVars.net_lan_name        = "eth0"   # Проводная сеть.
NetVars.net_wifi_name       = "wlan0"  # WiFi сеть.
NetVars.net_counter_timeout = 10.0     # Каждые 10 секунд сбрасывать пик.


# Можете перевести на свой язык:
USE_LANG = True  # Если установить False то будет использоваться English.
INTERFACE_LANG = {
    "classes": {
        "ghz":           "ГГц",
        "mem-free":      "Свободно:",
        "mem-used":      "Использовано:",
        "mem-total":     "Всего:",
    },
    "ids": {
        # Основное:
        "main":          "Основное",
        "hostname":      "Имя хоста:",
        "ipv4":          "IPv4:",
        "username":      "Имя пользователя:",
        "platform":      "Платформа:",
        "osname":        "Система:",
        "h264-freq":     "Частота H264:",
        "isp-freq":      "Частота ISP:",
        "uart-freq":     "Частота UART:",

        # Процессор:
        "cpu":           "Процессор",
        "arch":          "Архитектура:",
        "cpu-bits":      "Разрядность:",
        "cpu-temp":      "Температура:",
        "cpu-freq":      "Частота:",
        "cpu-min-freq":  "Минимальная частота:",
        "cpu-max-freq":  "Максимальная частота:",
        "cpu-all-freq":  "Все частоты:",
        "cpu-usage":     "Загруженность ЦП:",
        "cpu-cores":     "Нагрузка на ядра:",

        # Графика:
        "gpu":           "Графический процессор",
        "gpu-freq":      "Частота:",
        "gpu-min-freq":  "Минимальная частота:",

        # Память:
        "memory":        "Память",
        "ram":           "ОЗУ",
        "storage":       "Хранилище",

        # Использование диска:
        "disk-usage":    "Использование диска",
        "disk-read-bs":  "Чтение:",
        "disk-write-bs": "Запись:",

        # Интернет:
        "network":              "Сеть",
        "net-properties":       "Свойства:",
        "net-receive-bs":       "Получено:",
        "net-transmit-bs":      "Отправка:",
        "net-receive-total-b":  "Получено всего:",
        "net-transmit-total-b": "Отправлено всего:",
        "net-receive-max-b":    "Получено в пике:",
        "net-transmit-max-b":   "Отправлено в пике:",

        "system-uptime":        "Время работы:",
        "timestamp":            "Последнее время обновления информации:",
    },
    "other": {
        # ...
    },
}


# Получить страницу:
@app.get("/")
async def index(request: Request) -> Response:
    page = ""
    with open("pages/index.html", "r+", encoding="utf-8") as f:
        page = f.read()
    return HTMLResponse(page, 200)


@app.post("/api/status")
async def index(request: Request) -> Response:
    data = await request.json()
    # print("Получены данные:", data)

    # Статус системы:
    status = {
        "classes": {
            # ...
        },
        "ids": {
            "hostname-val":           get_hostname(),
            "ipv4-val":               get_ipv4(),
            "username-val":           get_username(),
            "platform-val":           get_platform(),
            "osname-val":             get_osname(),
            "h264-freq-val":          get_h264_freq(),
            "isp-freq-val":           get_isp_freq(),
            "uart-freq-val":          get_uart_freq(),

            "arch-val":               get_arch(),
            "cpu-bits-val":           get_cpu_bits(),
            "cpu-temp-val":           get_cpu_temp(),
            "cpu-freq-val":           get_cpu_freq(),
            "cpu-min-freq-val":       get_cpu_min_freq(),
            "cpu-max-freq-val":       get_cpu_max_freq(),
            "cpu-all-freq-val":       get_cpu_all_freq(),

            "gpu-freq-val":           get_gpu_freq(),
            "gpu-min-freq-val":       get_gpu_min_freq(),

            "ram-free-size-val":      format_memory_size(get_ram_free_size()),
            "ram-used-size-val":      format_memory_size(get_ram_used_size()),
            "ram-total-size-val":     format_memory_size(get_ram_total_size()),

            "storage-free-size-val":  format_memory_size(get_storage_free_size()),
            "storage-used-size-val":  format_memory_size(get_storage_used_size()),
            "storage-total-size-val": format_memory_size(get_storage_total_size()),

            "disk-read-bs-val":       format_memory_size(get_disk_read_bs()),
            "disk-write-bs-val":      format_memory_size(get_disk_write_bs()),

            "lan-rx-bs-val":          format_memory_size(get_lan_rx_bs()),
            "lan-tx-bs-val":          format_memory_size(get_lan_tx_bs()),
            "wifi-rx-bs-val":         format_memory_size(get_wifi_rx_bs()),
            "wifi-tx-bs-val":         format_memory_size(get_wifi_tx_bs()),

            "lan-rx-b-val":           format_memory_size(get_lan_rx_b()),
            "lan-tx-b-val":           format_memory_size(get_lan_tx_b()),
            "wifi-rx-b-val":          format_memory_size(get_wifi_rx_b()),
            "wifi-tx-b-val":          format_memory_size(get_wifi_tx_b()),

            "lan-rx-max-b-val":       format_memory_size(get_lan_max_rx_bs()),
            "lan-tx-max-b-val":       format_memory_size(get_lan_max_tx_bs()),
            "wifi-rx-max-b-val":      format_memory_size(get_wifi_max_rx_bs()),
            "wifi-tx-max-b-val":      format_memory_size(get_wifi_max_tx_bs()),

            "system-uptime-val":      format_uptime(),
            "timestamp-val":          datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        },
        "other": {
            "cpu-usage-val":          str(get_cpu_usage()),
            "cpu-cores-val":          get_cpu_cores(),
            "ram-used-percent":       str(round(get_ram_used_size()/get_ram_total_size()*100, 2)),
            "storage-used-percent":   str(round(get_storage_used_size()/get_storage_total_size()*100, 2)),
        },
    }

    # Отправляем данные:
    data = status
    if USE_LANG:
        data = {
            "classes": INTERFACE_LANG["classes"] | status["classes"],
            "ids": INTERFACE_LANG["ids"] | status["ids"],
            "other": INTERFACE_LANG["other"] | status["other"],
        }
    return JSONResponse(data, 200)


"""
    < PiStatusPanel >
    By LukovDev (@mr_lukov).
    License: MIT
    lakuworx@gmail.com

    Thank you for Using!
"""
