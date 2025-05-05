import os
import re
import json
import time
from datetime import datetime
from dotenv import load_dotenv

LOG_PATH = f"/home/USERNAME/SatisfactoryDedicatedServer/server.log"
JSON_OUTPUT = os.path.join(os.getcwd(), "satisfactory_players.json")

JOIN_PATTERN = re.compile(r"Login request:.*\?Name=([^\s?]+)")
REPDATA_PATTERN = re.compile(r"RepData=\[([0-9A-F]+)\]")
IP_PATTERN = re.compile(r"RemoteAddr: ([\d\.]+):\d+")
LEAVE_PATTERN = re.compile(r"UNetConnection::Close:.*?UniqueId:.*?RepData=\[([0-9A-F]+)\]")

history = []
repdata_to_username = {}
ip_to_repdata = {}
currently_online = {}

def load_existing_data():
    global history, repdata_to_username, ip_to_repdata, currently_online
    if os.path.exists(JSON_OUTPUT):
        with open(JSON_OUTPUT, "r") as f:
            data = json.load(f)
            history = data.get("history", [])
            currently_online = data.get("currently_online", {})
            repdata_to_username = data.get("repdata_to_username", {})
            ip_to_repdata = data.get("ip_to_repdata", {})

def save_data():
    data = {
        "history": history,
        "currently_online": currently_online,
        "repdata_to_username": repdata_to_username,
        "ip_to_repdata": ip_to_repdata
    }
    with open(JSON_OUTPUT, "w") as f:
        json.dump(data, f, indent=2)

def parse_line(line):
    timestamp = int(time.time())

    if "Login request:" in line:
        join_match = JOIN_PATTERN.search(line)
        repdata_match = REPDATA_PATTERN.search(line)
        
        if join_match and repdata_match:
            username = join_match.group(1)
            repdata = repdata_match.group(1)
            
            repdata_to_username[repdata] = username
            

            if repdata not in currently_online:
                currently_online[repdata] = username
                history.append({
                    "username": username,
                    "repdata": repdata,
                    "timestamp": timestamp,
                    "type": "JOIN"
                })
                print(f"[+] {username} joined (RepData: {repdata[:8]}...)")
            return

    ip_match = IP_PATTERN.search(line)
    if ip_match and "Client netspeed is" in line:
        ip = ip_match.group(1)
        
        for event in reversed(history):
            if event["type"] == "JOIN" and "ip" not in event and "repdata" in event:
                repdata = event["repdata"]
                ip_to_repdata[ip] = repdata
                event["ip"] = ip
                print(f"    Associated IP {ip} with player {event['username']}")
                break
    
    if "UNetConnection::Close:" in line:
        leave_match = REPDATA_PATTERN.search(line)
        ip_match = IP_PATTERN.search(line)
        
        if leave_match:
            repdata = leave_match.group(1)
            username = repdata_to_username.get(repdata)
            
            if username and repdata in currently_online:
                currently_online.pop(repdata, None)
                history.append({
                    "username": username,
                    "repdata": repdata,
                    "timestamp": timestamp,
                    "type": "LEAVE"
                })
                print(f"[-] {username} left (RepData: {repdata[:8]}...)")
                return

        if ip_match:
            ip = ip_match.group(1)

            repdata = ip_to_repdata.get(ip)
            if repdata:
                username = repdata_to_username.get(repdata)
                if username and repdata in currently_online:
                    currently_online.pop(repdata, None)
                    history.append({
                        "username": username,
                        "repdata": repdata,
                        "ip": ip,
                        "timestamp": timestamp,
                        "type": "LEAVE"
                    })
                    print(f"[-] {username} left (RepData: {repdata[:8]}...)")
                    return

            if ip in currently_online:
                username = currently_online[ip]
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
