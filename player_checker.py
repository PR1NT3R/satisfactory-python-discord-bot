import os
import re
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
USERNAME = os.getenv('USERNAME')

LOG_PATH = f"/home/{USERNAME}/SatisfactoryDedicatedServer/server.log"
JSON_OUTPUT = os.path.join(os.getcwd(), "satisfactory_players.json")

JOIN_PATTERN = re.compile(r"Join succeeded: (.+)")
ACCEPT_PATTERN = re.compile(r"NotifyAcceptingConnection accepted from: ([\d\.]+):\d+")
CLOSE_PATTERN = re.compile(r"UNetConnection::Close:.*?RemoteAddr: ([\d\.]+):\d+")

history = []
ip_to_username = {}
currently_online = {}

def load_existing_data():
    global history, ip_to_username, currently_online
    if os.path.exists(JSON_OUTPUT):
        with open(JSON_OUTPUT, "r") as f:
            data = json.load(f)
            history = data.get("history", [])
            currently_online = data.get("currently_online", {})
            ip_to_username = data.get("ip_to_username", {})

def save_data():
    data = {
        "history": history,
        "currently_online": currently_online,
        "ip_to_username": ip_to_username
    }
    with open(JSON_OUTPUT, "w") as f:
        json.dump(data, f, indent=2)

pending_username = None
last_accept_time = 0

def parse_line(line):
    global pending_username, last_accept_time
    timestamp = int(time.time())

    join_match = JOIN_PATTERN.search(line)
    if join_match:
        pending_username = join_match.group(1)
        return

    accept_match = ACCEPT_PATTERN.search(line)
    if accept_match and pending_username:
        ip = accept_match.group(1)
        if ip not in currently_online:
            ip_to_username[ip] = pending_username
            currently_online[ip] = pending_username
            history.append({
                "username": pending_username,
                "ip": ip,
                "timestamp": timestamp,
                "type": "JOIN"
            })
            print(f"[+] {pending_username} joined (IP: {ip})")
        pending_username = None
        return

    close_match = CLOSE_PATTERN.search(line)
    if close_match:
        ip = close_match.group(1)
        username = ip_to_username.get(ip)
        if username and ip in currently_online:
            currently_online.pop(ip, None)
            history.append({
                "username": username,
                "ip": ip,
                "timestamp": timestamp,
                "type": "LEAVE"
            })
            print(f"[-] {username} left (IP: {ip})")

def tail_log(log_path):
    print(f"Monitoring {log_path}")
    while not os.path.exists(log_path):
        print("Waiting for log file to be created...")
        time.sleep(2)

    with open(log_path, "r") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            parse_line(line)
            save_data()

if __name__ == "__main__":
    load_existing_data()
    tail_log(LOG_PATH)
