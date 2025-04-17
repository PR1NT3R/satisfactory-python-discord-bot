from datetime import datetime, timedelta
from pyfactorybridge import API
from dotenv import load_dotenv
import pyfactorybridge
import subprocess
import requests
import time
import json
import os

load_dotenv()
SATISFACTORY_SERVER_IP = os.getenv('SATISFACTORY_IP')
SATISFACTORY_SERVER_PORT = os.getenv('SATISFACTORY_PORT')
SATISFACTORY_SERVER_TOKEN = os.getenv('SATISFACTORY_TOKEN')
USERNAME = os.getenv('USERNAME')


# [v] TODO: fix the healthckeck
# [v] TODO: discord bot integration
# [ ] TODO: implement some kind of a webpage dashboard


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

def main():
    DEMO = False
    result = check_server()
    print(f"Health check result: {result}")

    if result == False:
        healthcheck_data = load_healthcheck_data()
        if should_reboot(healthcheck_data):
            if os.name == "posix":
                print("Restarting the server process...")
                if DEMO == False:
                    time.sleep(10)
                    # COMMAND HERE
                    subprocess.Popen(f"/home/{USERNAME}/SatisfactoryDedicatedServer/FactoryServer.sh > /home/{USERNAME}/SatisfactoryDedicatedServer/server.log 2>&1 &", shell=True)
                else:
                    print("DEMO mode active, doing nothing (but with demo mode off would restart the process)")
            else:
                print("Not linux, doing nothing (but on linux would restart the process)")
        else:
            print("Too many health checks in the last hour, NOT restarting the process")

if __name__ == "__main__":
    main()