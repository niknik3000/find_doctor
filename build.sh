#!/bin/bash
set -e
image_name="find_doctor_image"
container_name="find_doctor_container"
rm -f ./find_doctor/common.py
cp ../common/common.py ./find_doctor/common.py
cp ../private/tele.kdbx /home/tele_tok/tele.kdbx
docker stop ${container_name} && docker rm ${container_name}
docker build --rm -t ${image_name} --no-cache ./find_doctor
# неочевидная хня с entrypoint https://oprearocks.medium.com/how-to-properly-override-the-entrypoint-using-docker-run-2e081e5feb9d
docker run \
--detach \
--name ${container_name} \
--env-file ./find_doctor/env_find_doctor.env \
--restart=on-failure \
--log-opt max-size=50m \
-v /home/tele_tok/:/usr/src/app/token/ \
-v $(pwd)/find_doctor/:/usr/src/app/ \
--entrypoint python3 ${image_name} ./get_processes.py