from discord import Intents, Client, Message, app_commands# type:ignore
from responses import get_response # type:ignore
from dotenv import load_dotenv
from typing import Final
from pyfactorybridge import API
from player_functions import get_latest_events, get_currently_online # type:ignore
import pyfactorybridge
import requests
import discord # type:ignore
import asyncio
import random
import json
import time
import os

load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
GUILD_ID: Final[int] = os.getenv('GUILD_ID')
SATISFACTORY_TOKEN: Final[str] = os.getenv('SATISFACTORY_TOKEN')
WEBHOOK_URL: Final[str] = os.getenv('WEBHOOK_URL')
SATISFACTORY_SERVER_IP: Final[str] = os.getenv('SATISFACTORY_IP')
SATISFACTORY_SERVER_PORT: Final[str] = os.getenv('SATISFACTORY_PORT')
IMAGE_URL: Final[str] = os.getenv('IMAGE_URL')
# print(TOKEN)

intents: Intents = Intents.default()
intents.message_content = True #NOQA
client: Client = Client(intents=intents)
tree = app_commands.CommandTree(client)

session = requests.Session()
webhook = discord.webhook.SyncWebhook.from_url(WEBHOOK_URL, session=session)

async def send_message(message: Message, user_message: str) -> None:
    if not user_message:
        print("message was empty, intents are disabled")
        return
    
    
    if is_private := user_message[0] == '?':
        user_message = user_message[1:]

    try:
        response: str = get_response(user_message)
        if response:
            await (message.author.send(response) if is_private else message.channel.send(response))
    except Exception as e:
        print(e)

@client.event
async def on_ready() -> None:
    print(f'{client.user} is up!')
    await tree.sync(guild=discord.Object(id=GUILD_ID))

    # await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Looking for keywords..."))
    # await random_status()
    client.loop.create_task(random_status())
    client.loop.create_task(watch_players())
    client.loop.create_task(watch_server())

async def random_status():
    async def random_status1():
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Looking for keywords..."))
    async def random_status2():
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Watching lizard doggos"))
    async def random_status3():
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Listening to the sea"))
    async def random_status4():
        await client.change_presence(activity=discord.Streaming(name="Streaming a speedrun", url="https://example.com"))
    async def random_status5():
        await client.change_presence(activity=discord.Game(name="Satisfactory"))
    
    
    statuses = [random_status1, random_status2, random_status3, random_status4, random_status5]

    while not client.is_closed():
        status = random.choice(statuses)
        await status()
        await asyncio.sleep(10)

METADATA_FILE = os.path.join(os.getcwd(), "discord_bot_metadata.json")

def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

async def watch_server():
    while not client.is_closed():
        current_state = "DOWN"
        timestamp = int(time.time())

        try:
            satisfactory = API(address=f"{SATISFACTORY_SERVER_IP}:{SATISFACTORY_SERVER_PORT}", token=SATISFACTORY_TOKEN)
            if satisfactory.get_server_health()["health"] == "healthy":
                current_state = "UP"
        except pyfactorybridge.exceptions.ServerError:
            pass  # stay DOWN

        history = load_json(METADATA_FILE)

        if history and history[-1][0] == current_state:
            i = 0 # basically do nothing
            # print("No change in server health state, not adding a new entry.")
        else:
            history.append([current_state, timestamp])
            save_json(METADATA_FILE, history)
            # print(f"Server state changed to {current_state} at {timestamp}")

            message = ""
            if len(history) > 1:
                prev_state, prev_timestamp = history[-2]
                time_diff = timestamp - prev_timestamp
                hours = int(time_diff // 3600)
                minutes = int((time_diff % 3600) // 60)
                seconds = int(time_diff % 60)
                time_parts = []
                if hours > 0:
                    time_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
                if minutes > 0:
                    time_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
                if seconds > 0 or not time_parts:
                    time_parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
                formatted_time = ', '.join(time_parts)

                if current_state == "UP":
                    message = f":white_check_mark: The server is back online after {formatted_time} of downtime! (downtime timestamp: <t:{prev_timestamp}:R>)"
                else:
                    message = f":x: The server is offline after {formatted_time} of uptime! (downtime timestamp: <t:{prev_timestamp}:R>)"

                if len(message)>10:
                    webhook.send(message)

        await asyncio.sleep(10)

async def watch_players():
    while not client.is_closed():
        message = ""
        events = get_latest_events()
        events2 = []
        if events:
            if "join" in events:
                events["join"] = sorted(events["join"], key=lambda x: x[1])
                for event in events["join"]:
                    events2.append([event, "join"])
            if "leave" in events:
                events["leave"] = sorted(events["leave"], key=lambda x: x[1])
                for event in events["leave"]:
                    events2.append([event, "leave"])
            events2 = sorted(events2, key=lambda x: x[0][1])
            current_time = time.time()
            for entry in events2:
                if entry[1] == "join":
                    time_difference = current_time - entry[0][1]
                    relative_time = f"{int(time_difference // 3600):02}:{int((time_difference % 3600) // 60):02}:{int(time_difference % 60):02}"
                    message += f":arrow_right: {entry[0][0]} joined the server at <t:{entry[0][1]}:R>\n"
                if entry[1] == "leave":
                    leave_time = entry[0][1]
                    join_time = entry[0][2]
                    if join_time:
                        session_length = leave_time - join_time
                        session_str = f"{int(session_length // 3600):02}:{int((session_length % 3600) // 60):02}:{int(session_length % 60):02}"
                        message +=  f":arrow_left: {entry[0][0]} left after playing for {session_str}, they joined at <t:{join_time}:R>\n"
                    else:
                        message += f":arrow_left: {entry[0][0]} left (join time unknown)\n"
                message += "\n"

        if len(message) >= 10:
            webhook.send(message)
        await asyncio.sleep(10)

    
# @tree.command(name="test", description="Just a testing command", guild=discord.Object(id=GUILD_ID))
# async def first_command(interaction):
#     await interaction.response.send_message("Hello from a command!")

# @tree.command(name="test2", description="Just a testing command, responds in private", guild=discord.Object(id=GUILD_ID))
# async def first_command(interaction):
#     await interaction.response.send_message("Hello from a command!", ephemeral=True)

# @tree.command(name="test3", description="Just a testing command, responds in dm", guild=discord.Object(id=GUILD_ID))
# async def first_command(interaction):
#     try:
#         await interaction.user.send("Hello from a command!")
#         await interaction.response.send_message("sent dm!")
#     except discord.Forbidden:
#         await interaction.response.send_message("cannot send dm", ephemeral=True)

# @tree.command(name="test4", description="Just a testing command, responds in dm, private response", guild=discord.Object(id=GUILD_ID))
# async def first_command(interaction):
#     try:
#         await interaction.user.send("Hello from a command!")
#         await interaction.response.send_message("sent dm!", ephemeral=True)
#     except discord.Forbidden:
#         await interaction.response.send_message("cannot send dm", ephemeral=True)

# @tree.command(name="test5", description="Just a testing command, responds with a test embed", guild=discord.Object(id=GUILD_ID))
# async def first_command(interaction):
#     embed = discord.Embed(
#         title="Server status:",
#         description="test\ntest below",
#         # color=discord.Colour.dark_red()
#         color=discord.Colour(0xfb8500)
#     )
#     embed.set_footer(text="footer")
#     embed.set_thumbnail(url=IMAGE_URL)
#     await interaction.response.send_message(embed=embed)

@tree.command(name="online", description="Shows who is online on the server", guild=discord.Object(id=GUILD_ID))
async def first_command(interaction):
    message_content = ""
    players_online = get_currently_online()
    current_time = time.time()
    for player in players_online:
        time_difference = current_time-player['joined_timestamp']
        # relative_time = f"{int(time_difference // 3600)} hours, {int((time_difference % 3600) // 60)} minutes and {int(time_difference % 60)} seconds" if time_difference >= 3600 else f"{int(time_difference // 60)} minutes and {int(time_difference % 60)} seconds" if time_difference >= 60 else f"{int(time_difference)} seconds"
        relative_time = f"{int(time_difference // 3600):02}:{int((time_difference % 3600) // 60):02}:{int(time_difference % 60):02}"
        message_content += f">{player['username']} has been playing for {relative_time}, joined <t:{player['joined_timestamp']}:R>\n"
    embed = discord.Embed(
        title="Players on the server:",
        description=message_content,
        # color=discord.Colour.dark_red()
        color=discord.Colour(0xfb8500)
    )
    embed.set_footer(text='time format for "playing for" is "HH:MM:SS"')
    embed.set_thumbnail(url=IMAGE_URL)
    await interaction.response.send_message(embed=embed)

@tree.command(name="info", description="Shows the session info", guild=discord.Object(id=GUILD_ID))
async def first_command(interaction):
    satisfactory = API(address=f"{SATISFACTORY_SERVER_IP}:{SATISFACTORY_SERVER_PORT}", token=SATISFACTORY_TOKEN)
    server_health = satisfactory.get_server_health()
    server_game_state = satisfactory.query_server_state()["serverGameState"]
    time_difference = server_game_state["totalGameDuration"]
    # relative_time = f"{int(time_difference // 3600)} hours, {int((time_difference % 3600) // 60)} minutes and {int(time_difference % 60)} seconds" if time_difference >= 3600 else f"{int(time_difference // 60)} minutes and {int(time_difference % 60)} seconds" if time_difference >= 60 else f"{int(time_difference)} seconds"
    relative_time = f"{int(time_difference // 3600):02}:{int((time_difference % 3600) // 60):02}:{int(time_difference % 60):02}"
    description = f"""
    >Server Health: {server_health["health"]}
    >Is paused due to no players: {server_game_state["isGamePaused"]}
    >Average Tick rate: {round(server_game_state["averageTickRate"], 3)}
    >Save name: {server_game_state["activeSessionName"]}
    >Session time: {relative_time} (HH:MM:SS)
    >Connected players: {server_game_state["numConnectedPlayers"]}/{server_game_state["playerLimit"]}
    >Phase: {server_game_state["gamePhase"]
        .split("_")[-1]
        .split("'")[0]}
    >Milestone: {server_game_state["activeSchematic"]
        .split("/")[-1]
        .split("_")[-2]}
    >Nearest sheduled server reboots: <t:{str(time.mktime(
        time.strptime(time.strftime('%Y-%m-%d 01:00:00',
        time.localtime(time.time())), '%Y-%m-%d %H:%M:%S')) +
         (86400 if time.localtime(time.time()).tm_hour > 0 else 0))[:-2]}:R>
     and <t:{str(time.mktime(
         time.strptime(time.strftime('%Y-%m-%d 04:00:00',
        time.localtime(time.time())), '%Y-%m-%d %H:%M:%S')) +
         (86400 * ((6 - time.localtime(time.time()).tm_wday) % 7)))[:-2]}:R>
    """
    embed = discord.Embed(
        title="Server status:",
        description=description,
        # color=discord.Colour.dark_red()
        color=discord.Colour(0xfb8500)
    )
    embed.set_footer(text="For more info about connected players please use /online")
    embed.set_thumbnail(url=IMAGE_URL)
    await interaction.response.send_message(embed=embed)

@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user:
        return
    username: str = str(message.author)
    user_message: str = str(message.content)
    channel: str = str(message.channel)
    # guild_id: int = int(message.guild.id)

    print(f'[{channel}] {username}: "{user_message}"')
    # print(f'[{guild_id}-{channel}] {username}: "{user_message}"')
    await send_message(message, user_message)

def main() -> None:
    client.run(token=TOKEN)

if __name__ == '__main__':
    main()
