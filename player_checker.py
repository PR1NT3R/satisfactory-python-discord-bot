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

JOIN_PATTERN = re.compile(r"Join succeeded: ([^\s]+)")
ACCEPT_PATTERN = re.compile(r"NotifyAcceptingConnection accepted from: ([\d\.]+):\d+")
USER_ID_PATTERN = re.compile(r"userId: Epic:([^\s]+)")

history = []
id_to_username = {}
id_to_ip = {}
currently_online = {}

pending_joins = {}

def load_existing_data():
    global history, id_to_username, currently_online, id_to_ip
    if os.path.exists(JSON_OUTPUT):
        with open(JSON_OUTPUT, "r") as f:
            data = json.load(f)
            history = data.get("history", [])
            currently_online = data.get("currently_online", {})
            id_to_username = data.get("id_to_username", {})
            id_to_ip = data.get("id_to_ip", {})

def save_data():
    data = {
        "history": history,
        "currently_online": currently_online,
        "id_to_username": id_to_username,
        "id_to_ip": id_to_ip
    }
    with open(JSON_OUTPUT, "w") as f:
        json.dump(data, f, indent=2)

def parse_line(line):
    timestamp = int(time.time())

    user_id_match = USER_ID_PATTERN.search(line)
    if user_id_match:
        user_id = user_id_match.group(1)
        if user_id not in pending_joins:
            pending_joins[user_id] = {"id": user_id}
        return

    join_match = JOIN_PATTERN.search(line)
    if join_match:
        username = join_match.group(1)
        for info in pending_joins.values():
            if "username" not in info:
                info["username"] = username
        return

    accept_match = ACCEPT_PATTERN.search(line)
    if accept_match:
        ip = accept_match.group(1)
        for user_id, info in list(pending_joins.items()):
            if "username" in info:
                username = info["username"]
                if user_id not in currently_online:
                    currently_online[user_id] = username
                    id_to_username[user_id] = username
                    id_to_ip[user_id] = ip
                    history.append({
                        "id": user_id,
                        "username": username,
                        "ip": ip,
                        "timestamp": timestamp,
                        "type": "JOIN"
                    })
                    print(f"[+] {username} joined (ID: {user_id}, IP: {ip})")
                del pending_joins[user_id]
        return

    if "UNetConnection::Close:" in line and "RemoteAddr:" in line:
        close_match = re.search(r"RemoteAddr: ([\d\.]+):\d+", line)
        if close_match:
            ip = close_match.group(1)
            for user_id, stored_ip in id_to_ip.items():
                if stored_ip == ip:
                    username = id_to_username.get(user_id)
                    if user_id in currently_online:
                        currently_online.pop(user_id, None)
                        history.append({
                            "id": user_id,
                            "username": username,
                            "ip": ip,
                            "timestamp": timestamp,
                            "type": "LEAVE"
                        })
                        print(f"[-] {username} left (ID: {user_id}, IP: {ip})")
                    break

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