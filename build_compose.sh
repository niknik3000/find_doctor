#!/bin/bash
set -e
sudo apt install jq yamllint -y
jq . ./find_doctor/11347.json 1>/dev/null
jq . ./find_doctor/30058.json 1>/dev/null
# python3 -m pip install --user yamllint
# yamllint ./find_doctor_compose.yaml
docker-compose -f ./find_doctor_compose.yaml down
cp ../common/common.py ./find_doctor/common.py
docker-compose -f ./find_doctor_compose.yaml build --no-cache --parallel
docker-compose -f ./find_doctor_compose.yaml up -d --force-recreate