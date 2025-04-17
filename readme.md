this code uses [PyFactoryBridge](https://github.com/Jayy001/PyFactoryBridge)

---

this discord bot is actually a webhook and a python bot in one (I coudn't figure out how to send discord messages to a specific channel unprompted by user from the bot itself, so the webhook solves it), just make sure the actual bot has perms to read and write messages, and make / commands

example messages (by DISCORD_TIMESTAMP, I mean [this](https://discordtimestamp.com/)):
```
:arrow_right: player joined the server at DISCORD_TIMESTAMP
:arrow_left: player left after playing for 01:02:03, they joined at DISCORD_TIMESTAMP


:x: The server is offline after x minutes, x seconds of uptime! (downtime timestamp: DISCORD_TIMESTAMP)
:white_check_mark: The server is back online after x minutes, x seconds of downtime! (downtime timestamp: DISCORD_TIMESTAMP)

on /info (it's an embed):
Server status:

>Server Health: healthy
>Is paused due to no players: True
>Average Tick rate: 29.923
>Save name: SAVENAME
>Session time: 01:02:03 (HH:MM:SS)
>Connected players: 0/8
>Phase: 1
>Milestone: 5-3
>Nearest sheduled server reboots: DISCORD_TIMESTAMP
and DISCORD_TIMESTAMP

For more info about connected players please use /online
on /online (it's an embed too)

Players on the server:

player has been playing for 01:02:03, joined DISCORD_TIMESTAMP
player has been playing for 01:02:03, joined DISCORD_TIMESTAMP

time format for playing for is "HH:MM:SS"
```

---

there is a requirements.txt file for python pip, you probably already know what to do with it

as the user in the env file just set your linux username, the script assumes the game server is installed on "/home/{USERNAME}/SatisfactoryDedicatedServer/FactoryServer.sh"

crontab setup:

```
# HEALTHCHECK
@reboot sleep 15; cd /home/username/satisfactory_bot && /home/username/satisfactory_bot/venv/bin/python3 healthcheck.py
*/10 * * * * cd /home/username/satisfactory_bot && /home/username/satisfactory_bot/venv/bin/python3 healthcheck.py

#PLAYER JOINED/LEFT
@reboot sleep 30; cd /home/username/satisfactory_bot && /home/username/satisfactory_bot/venv/bin/python3 player_checker.py

#DISCORD BOT
@reboot sleep 45; cd /home/username/satisfactory_bot && /home/username/satisfactory_bot/venv/bin/python3 discord_bot.py
```

logs rotating:
sudo nano /etc/logrotate.d/satisfactory-server
```
/home/username/SatisfactoryDedicatedServer/server.log {
    size 100M
    rotate 5
    compress
    missingok
    notifempty
    copytruncate
}
```
force rotate log:
sudo logrotate -f /etc/logrotate.d/satisfactory-server
