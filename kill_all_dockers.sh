stop_and_kill () {
	docker kill $(docker ps -q)
	docker rm $(docker ps --filter status=created -q)
	docker rm $(docker ps --filter status=exited -q)
}

read -p "Do you wish to stop and delete ALL containers? y/N " answer
case $answer in
		[Yy]* ) stop_and_kill; break;;
		[Nn]* ) exit;;
		* ) exit;;
esac

