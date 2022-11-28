docker kill $(docker ps -q)
docker rm $(docker ps --filter status=created -q)
docker rm $(docker ps --filter status=exited -q)
