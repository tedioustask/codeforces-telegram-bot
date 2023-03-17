#!/bin/bash
apt-get update && apt-get install docker-compose cron
systemctl enable cron
(crontab -l ; echo "* * * * * cd $PWD && docker-compose start db_update") | crontab
docker-compose up -d

