#!/bin/bash
apt-get update && apt-get -y install docker-compose cron
systemctl enable cron
(crontab -l ; echo "0 * * * * `which docker-compose` -f $PWD/docker-compose.yaml start db_updater") | crontab
docker-compose up -d

