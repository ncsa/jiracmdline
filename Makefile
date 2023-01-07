run:
	docker-compose pull
	docker-compose up

build:
	docker-compose -f build.yaml up --build

clean:
	docker-compose down
	docker-compose rm -f
	docker images | awk '/jiracmdline/{print $$3}' | xargs -r docker rmi
