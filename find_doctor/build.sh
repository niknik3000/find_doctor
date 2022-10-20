image_name="find_doctor_image"
container_name="find_doctor_cont"
cp ../../common/common.py ./common.py
docker stop ${container_name} && docker rm ${container_name}
docker build --rm -t ${image_name} --no-cache .
# неочевидная хня с entrypoint https://oprearocks.medium.com/how-to-properly-override-the-entrypoint-using-docker-run-2e081e5feb9d
docker run --name ${container_name} --env-file env_find_doctor.env --restart=always -v /home/tele_tok/:/usr/src/app/token/ --entrypoint python3 ${image_name} ./get_processes.py