from datetime import datetime, timedelta
from pyfactorybridge import API
from dotenv import load_dotenv
import pyfactorybridge
import subprocess
import requests
import psutil #type:ignore
import time
import json
import sys
import os

load_dotenv()
SATISFACTORY_SERVER_IP = os.getenv('SATISFACTORY_IP')
SATISFACTORY_SERVER_PORT = os.getenv('SATISFACTORY_PORT')
SATISFACTORY_SERVER_TOKEN = os.getenv('SATISFACTORY_TOKEN')
USERNAME = os.getenv('USERNAME')
GOTIFY_BOOL = os.getenv('GOTIFY_BOOL')
if GOTIFY_BOOL.lower() == "true":
    GOTIFY_BOOL = True
    GOTIFY_URL = os.getenv('GOTIFY_URL')
    GOTIFY_APP_TOKEN = os.getenv('GOTIFY_APP_TOKEN')
else:
    GOTIFY_BOOL = False


# [v] TODO: fix the healthckeck
# [v] TODO: discord bot integration
# [ ] TODO: implement some kind of a webpage dashboard

def gotify_message(title, content, priority, verifySSL):
    if GOTIFY_BOOL:
        url = GOTIFY_URL
        if url.endswith('/'):
            url = url[:-1]

        url = url+"/message?token="+GOTIFY_APP_TOKEN

        if priority == None:
            priority = 0

        if title == None:
            title = "Empty"

        if content == None:
            content = "Empty"

        data = {
            "title": title,
            "message": content,
            "priority": priority
        }

        response = requests.post(url, data=data, verify=verifySSL)
        print(f"gotify response status code: {response.status_code}")
        # print(f"gotify response: {response.text}")
    else:
        return


def prettify_json(anything):
    return json.dumps(anything, indent=4)

def load_healthcheck_data(filename="healthcheck_data.json"):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    else:
        return []

def save_healthcheck_data(data, filename="healthcheck_data.json"):
    with open(filename, 'w') as file:
        json.dump(data, file)

def save_metadata(data, filename="metadata.json"):
    with open(filename, 'w') as file:
        json.dump(data, file)

def check_server():
    try:
        satisfactory = API(address=f"{SATISFACTORY_SERVER_IP}:{SATISFACTORY_SERVER_PORT}", token=SATISFACTORY_SERVER_TOKEN)
        print(prettify_json(satisfactory.get_server_health()))
        # print(satisfactory.get_server_health()["health"])
        if satisfactory.get_server_health()["health"] != "healthy":
            return False
        return True
    except pyfactorybridge.exceptions.ServerError:
        # print("A")
        return False

def should_reboot(healthcheck_data):
    now = datetime.now()
    valid_timestamps = [ts for ts in healthcheck_data if now - datetime.fromtimestamp(ts) <= timedelta(seconds=3600)]
    if len(valid_timestamps) >= 5:
        return False
    valid_timestamps.append(now.timestamp())
    valid_timestamps = valid_timestamps[-6:]
    save_healthcheck_data(valid_timestamps)
    
    return True

def kill_factory_server():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if "FactoryServer-L" in proc.info['name'] or \
               any("FactoryServer-L" in cmd for cmd in proc.info['cmdline']):
                print(f"Killing FactoryServer-L process (PID: {proc.pid})")
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

def is_process_running(search_term):
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any(search_term in cmd for cmd in cmdline):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

def start_process(command):
    subprocess.Popen(command, shell=True)

def is_uptime_more_than_3_min():
    if os.name == 'posix':
        # For Linux/macOS
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
        return uptime_seconds > 180
    elif os.name == 'nt':
        # For Windows
        import ctypes
        from ctypes import wintypes, windll

        class SYSTEM_TIME(ctypes.Structure):
            _fields_ = [("wYear", wintypes.WORD),
                        ("wMonth", wintypes.WORD),
                        ("wDayOfWeek", wintypes.WORD),
                        ("wDay", wintypes.WORD),
                        ("wHour", wintypes.WORD),
                        ("wMinute", wintypes.WORD),
                        ("wSecond", wintypes.WORD),
                        ("wMilliseconds", wintypes.WORD)]

        class FILETIME(ctypes.Structure):
            _fields_ = [('dwLowDateTime', wintypes.DWORD),
                        ('dwHighDateTime', wintypes.DWORD)]

        GetTickCount64 = windll.kernel32.GetTickCount64
        GetTickCount64.restype = ctypes.c_ulonglong

        uptime_ms = GetTickCount64()
        return uptime_ms > 180 * 1000

    else:
        raise NotImplementedError("Unsupported OS")

def main():
    DEMO = False
    is_up_more_than_3_min = is_uptime_more_than_3_min()
    print(f"is more than 3 min since reboot: {is_up_more_than_3_min}")
    if not is_up_more_than_3_min:
        if DEMO:
            print("would abort the program due to the server, would abort to not break any crontabs but continuing due to demo mode")
        else:
            print("the server is not up for long enough, aborting to not break any crontabs")
            sys.exit()
            return
    result = check_server()
    print(f"Health check result: {result}")

    if result is False:
        healthcheck_data = load_healthcheck_data()
        if should_reboot(healthcheck_data):
            print("Server is unhealthy, attempting restart...")
            if os.name == "posix":
                if DEMO:
                    print("demo mode, would kill the server process and restart it")
                else:
                    gotify_message("Main server process is offline!", "Attempting to restart it", None, False)
                    time.sleep(10)
                    kill_factory_server()
                    time.sleep(30)
                    print("Starting main server process...")
                    start_process("/home/USERNAME/SatisfactoryDedicatedServer/FactoryServer.sh >> /home/USERNAME/SatisfactoryDedicatedServer/server.log 2>&1 &")
                
                # Player checker logic
                print("checking for the player checker process")
                if not is_process_running("player_checker.py"):
                    if DEMO:
                        print("demo mode, would start the player checker")
                    else:
                        time.sleep(30)
                        gotify_message("Player checker is offline!", "Attempting to restart it", None, False)
                        print("Player checker not running. Starting...")
                        start_process("cd /home/USERNAME/satisfactory_bot && /home/USERNAME/satisfactory_bot_venv_fix/venv/bin/python3 player_checker.py > /dev/null 2>&1 &")
                else:
                    print("Player checker is already running.")

                # Discord bot logic
                print("checking for discord bot process")
                if not is_process_running("discord_bot.py"):
                    if DEMO:
                        print("demo mode, would start the discord bot")
                    else:
                        gotify_message("Discord bot is offline!", "Attempting to restart it", None, False)
                        print("Discord bot not running, waiting 15s for player checker")
                        time.sleep(15)
                        print("Starting the discord bot")
                        start_process("cd /home/USERNAME/satisfactory_bot && PYTHONUNBUFFERED=1 /home/USERNAME/satisfactory_bot_venv_fix/venv/bin/python3 discord_bot.py >> /home/USERNAME/satisfactory_bot/discord_bot.log 2>&1 &")
                else:
                    print("Discord bot is already running.")
            else:
                print("Not running on Linux. Aborting restart logic.")
        else:
            print("Too many restarts recently. Skipping restart.")
    else:
        print("Server is healthy. No action needed.")

    if os.name == "posix":
        # Player checker logic
        print("checking for the player checker process")
        if not is_process_running("player_checker.py"):
            if DEMO:
                print("demo mode, would start the player checker")
            else:
                gotify_message("Player checker is offline!", "Attempting to restart it", None, False)
                print("Player checker not running. Starting...")
                start_process("cd /home/USERNAME/satisfactory_bot && /home/USERNAME/satisfactory_bot_venv_fix/venv/bin/python3 player_checker.py > /dev/null 2>&1 &")
        else:
            print("Player checker is already running.")

        # Discord bot logic
        print("checking for discord bot process")
        if not is_process_running("discord_bot.py"):
            if DEMO:
                print("demo mode, would start the discord bot")
            else:
                gotify_message("Discord bot is offline!", "Attempting to restart it", None, False)
                print("Discord bot not running, waiting 15s for player checker")
                time.sleep(15)
                print("Starting the discord bot")
                start_process("cd /home/USERNAME/satisfactory_bot && PYTHONUNBUFFERED=1 /home/USERNAME/satisfactory_bot_venv_fix/venv/bin/python3 discord_bot.py >> /home/USERNAME/satisfactory_bot/discord_bot.log 2>&1 &")
        else:
            print("Discord bot is already running.")
    else:
        print("Not running on Linux. Aborting dynamic restart logic.")

if __name__ == "__main__":
    main()
