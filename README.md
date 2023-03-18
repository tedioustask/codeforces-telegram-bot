# Codeforces-telegram-bot

Telegram bot for codeforces.com to fetch problem set filtered by rating and tag.
It parse all problems fetched with API endpoint `/api/problemset.problems` and store them to database.
Whole problem set splits to contests by tag and rating after that.

After running shell script docker-compose and cron will installed to run 3 services:
- PostgreSQL DB container
- Telegram Bot container
- DB updater container

Updater container starts by cron job every hour

# Starting bot

Before running change `BOT_TOKEN` variable in *env* file for appropriate telegram API token

To run bot clone this repository and run cd to repo folder and run
```
chmod +x install.sh
sudo ./install.sh
```
To stop bot just run in repo folder
```
sudo docker-compose down
```
Tested on Ubuntu server 22.04

