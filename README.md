# codeforces-telegram-bot

Telegram bot for codeforces.com to fetch problem set filtered by rating and tag 
After running shell script docker-compose will installed to run 3 services:
- Postgres DB
- Bot Container
- DB updater container

# Starting bot

Before running change `BOT_TOKEN` variable in *env* file for appropriated telegram API token

To run bot clone this repository and run cd to repo folder and run
```
chmod +x install.sh
sudo ./install.sh
```
Tested on Ubuntu server 22.04
