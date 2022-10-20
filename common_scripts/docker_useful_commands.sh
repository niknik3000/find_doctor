# чистка образов с тегом <none>
docker images|grep none|awk '{print $3 }'|xargs docker rmi
# чистка остановленных конейнеров
docker ps -a | grep "Exited" | awk '{print $1 }'|xargs docker rm
# снести все контейнеры
docker rm $(docker ps -a -q)
# снести все образы
docker rmi $(docker images -a -q)