build:
	docker build -t telebetbot:dev .

run:
	docker run --name telebetbot -d telebetbot:dev

stop:
	docker stop telebetbot

clear:
	docker container rm telebetbot
	docker image rm telebetbot:dev

logs:
	docker logs telebetbot

start:
	docker start telebetbot

restart:
	make stop
	make clear
	make build
	make run
	make logs
