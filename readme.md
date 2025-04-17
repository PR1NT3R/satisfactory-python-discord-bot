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
