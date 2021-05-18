#!/bin/env bash
#
# Configures Chia and Plotman, then launches Machinaris web server
#

echo 'Configuring Chia...'
#sed -i 's/log_stdout: false/log_stdout: true/g' /root/.chia/mainnet/config/config.yaml
sed -i 's/log_level: WARNING/log_level: INFO/g' /root/.chia/mainnet/config/config.yaml

echo 'Configuring Plotman...'
mkdir -p /root/.chia/plotman/logs
cp -n /machinaris/config/plotman.sample.yaml /root/.chia/plotman/plotman.yaml

echo 'Starting Machinaris...'
mkdir -p /root/.chia/machinaris/logs
cd /machinaris
if [ $FLASK_ENV == "development" ];
then
    /chia-blockchain/venv/bin/gunicorn --reload --bind 0.0.0.0:8926 app:app > /root/.chia/machinaris/logs/webui.log 2>&1 &
else
    /chia-blockchain/venv/bin/gunicorn --bind 0.0.0.0:8926 app:app > /root/.chia/machinaris/logs/webui.log 2>&1 &
fi
echo 'Completed startup.  Browse to port 8926.'
