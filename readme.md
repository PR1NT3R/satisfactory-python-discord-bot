this code uses [PyFactoryBridge](https://github.com/Jayy001/PyFactoryBridge)

---

ISSUES:
 - FIXED - player checker part of the discord bot stopping working after the server has crashed and restarted (I actually have no idea what is wrong with it)

---

---

DEPLOYEMENT:
 - Replace all hardcoded paths with the actual ones in the player_checker.py and healthcheck.py (I coudn't figure out how to handle paths correctly via env files, it just woudn't work correctly

---

this discord bot is actually a webhook and a python bot in one (I coudn't figure out how to send discord messages to a specific channel unprompted by user from the bot itself, so the webhook solves it), just make sure the actual bot has perms to read and write messages, and make / commands

example messages (by DISCORD_TIMESTAMP, I mean [this](https://discordtimestamp.com/)):
```
:arrow_right: player joined the server at DISCORD_TIMESTAMP
:arrow_left: player left after playing for 01:02:03, they joined at DISCORD_TIMESTAMP


:x: The server is offline after x minutes, x seconds of uptime! (downtime timestamp: DISCORD_TIMESTAMP)
:white_check_mark: The server is back online after x minutes, x seconds of downtime! (downtime timestamp: DISCORD_TIMESTAMP)
```
```
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
```

```
on /online (it's an embed too)

Players on the server:

player has been playing for 01:02:03, joined DISCORD_TIMESTAMP
player has been playing for 01:02:03, joined DISCORD_TIMESTAMP

time format for playing for is "HH:MM:SS"
```

---

making a discord bot invite (cuz discord broke it)

```
https://discord.com/oauh2/authorize?client_id=JUSTLEAVEITASITWAS&permissions=8&scope=bot
----------------------------------------------------------------^
the start of the stuff you're susposed to add to the url, change 8 to whatever you've choosen in the permissions creator
```

---

there is a requirements.txt file for python pip, you probably already know what to do with it

as the user in the env file just set your linux username, the script assumes the game server is installed on "/home/{USERNAME}/SatisfactoryDedicatedServer/FactoryServer.sh"

crontab setup:

```
# HEALTHCHECK
@reboot sleep 15; cd /home/USERNAME/satisfactory_bot && /home/USERNAME/satisfactory_bot_venv_fix/venv/bin/python3 healthcheck.py
*/5 * * * * cd /home/USERNAME/satisfactory_bot && /home/USERNAME/satisfactory_bot_venv_fix/venv/bin/python3 healthcheck.py

#BACKUP SAVES & BLUEPRINTS
50 7 * * * bash -c 'mkdir -p /home/USERNAME/satisfactory_server_BACKUPS/$(date +\%d-\%m-\%Y)'
55 7 * * * bash -c 'cp -r /home/USERNAME/.config/Epic/FactoryGame/Saved/SaveGames /home/USERNAME/satisfactory_server_BACKUPS/$(date +\%d-\%m-\%Y)/'
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
