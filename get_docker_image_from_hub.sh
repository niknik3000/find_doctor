image_name="find_doctor_image"
container_name="find_doctor_cont"
hub_name="niknik9000/find_doctor:latest"
rm -f ./find_doctor/common.py
cp ../common/common.py ./find_doctor/common.py
cp ../private/tele.kdbx /home/tele_tok/tele.kdbx
docker pull ${hub_name}
docker stop ${container_name} && docker rm ${container_name}
docker run \
--detach \
--name ${container_name} \
--env-file ./find_doctor/env_find_doctor.env \
--restart=always \
-v /home/tele_tok/:/usr/src/app/token/ \
-v $(pwd)/find_doctor/:/usr/src/app/ \
--entrypoint python3 ${hub_name} ./get_processes.py