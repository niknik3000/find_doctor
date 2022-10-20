docker-compose -f ./find_doctor_compose.yaml down
cp ../common/common.py ./find_doctor/common.py
docker-compose -f ./find_doctor_compose.yaml --no-cache build
docker-compose -f ./find_doctor_compose.yaml up -d --force-recreate