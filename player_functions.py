import os
import json

DATA_FILE = os.path.join(os.getcwd(), "satisfactory_players.json")
META_FILE = os.path.join(os.getcwd(), "satisfactory_players_metadata.json")

def load_json(path):
    if not os.path.exists(path) or os.stat(path).st_size == 0:
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: JSON decoding failed for {path}, returning empty dict.")
        return {}

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def get_latest_event(event_type):
    data = load_json(DATA_FILE)
    metadata = load_json(META_FILE)

    shown_ids = metadata.get(f"shown_{event_type.lower()}", [])
    history = data.get("history", [])

    for i, event in reversed(list(enumerate(history))):
        if event["type"] == event_type and i not in shown_ids:
            shown_ids.append(i)
            metadata[f"shown_{event_type.lower()}"] = shown_ids
            save_json(META_FILE, metadata)
            return {
                "username": event["username"],
                "ip": event.get("ip"),
                "timestamp": event["timestamp"]
            }

    return None

def get_latest_join():
    return get_latest_event("JOIN")

def get_latest_leave():
    return get_latest_event("LEAVE")

def get_latest_events():
    data = load_json(DATA_FILE)
    metadata = load_json(META_FILE)

    shown_ids = metadata.get("shown_ids", [])
    history = data.get("history", [])

    new_joins = []
    new_leaves = []

    for i, event in enumerate(history):
        if i not in shown_ids:
            shown_ids.append(i)
            if event["type"] == "JOIN":
                new_joins.append([event["username"], event["timestamp"]])
            elif event["type"] == "LEAVE":
                new_leaves.append([event["username"], event["timestamp"]])

    metadata["shown_ids"] = shown_ids
    save_json(META_FILE, metadata)

    result = {}
    if new_joins:
        result["join"] = new_joins
    if new_leaves:
        result["leave"] = new_leaves

    return result if result else None

def get_currently_online():
    data = load_json(DATA_FILE)
    online = data.get("currently_online", {})
    history = data.get("history", [])
    result = {}

    for entry in reversed(history):
        if entry["type"] == "JOIN":
            ip = entry.get("ip")
            if ip in online and ip not in result:
                result[ip] = {
                    "username": entry["username"],
                    "joined_timestamp": entry["timestamp"]
                }

    return list(result.values())


# One-time return logic:
# latest_join = get_latest_join()
# if latest_join:
#     print(f"Latest join: {latest_join['username']} (IP: {latest_join['ip']})")
# else:
#     print("No new joins.")

# latest_leave = get_latest_leave()
# if latest_leave:
#     print(f"Latest leave: {latest_leave['username']} (IP: {latest_leave['ip']})")
# else:
#     print("No new leaves.")

# events = get_latest_events()

# def prettify_json(anything):
#     return json.dumps(anything, indent=4)

# if events:
#     if "join" in events:
#         # print(f"New joins: {events['join']}")
#         print("joins:")
#         print(prettify_json(events["join"]))
#     if "leave" in events:
#         # print(f"New leaves: {events['leave']}")
#         print("leaves:")
#         print(prettify_json(events["leave"]))
# else:
#     print("No new joins or leaves.")

# # Always returns full list
# online_now = get_currently_online()
# print("Currently online:")
# for player in online_now:
#     print(f"{player['username']} - joined at {player['joined_timestamp']}")