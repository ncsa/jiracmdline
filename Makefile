run:
	docker-compose pull
	docker-compose up

build:
	docker-compose -f build.yaml up --build

gunicorn:
	docker-compose -f build.yaml build
	docker-compose -f build.yaml run  gunicorn_project bash

clean:
	docker-compose down
	docker-compose rm -f
	docker container prune -f
	docker images | awk '/andylytical|jiracmdline|gunicorn/ {print $$3}' | xargs -r docker rmi
