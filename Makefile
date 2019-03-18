IMAGE_NAME := redis-webcli

.PHONY: push
push: build
	cf push


.PHONY: build
build:
	wget https://s3.eu-central-1.amazonaws.com/redislabs-dev-public-deps/binaries/memtier_benchmark_1.2.15_xenial
	mv memtier_benchmark_1.2.15_xenial memtier_benchmark
	chmod +x memtier_benchmark


.PHONY: image
image: build
	docker build --tag $(IMAGE_NAME) .


.PHONY: run
run:
	# fail if the file does not exist
	docker run $(IMAGE_NAME)


.PHONY: docker_push
docker_push: image
	docker tag $(IMAGE_NAME):latest redislabs/$(IMAGE_NAME)
	docker push redislabs/$(IMAGE_NAME)
