.PHONY: push
push: memtier_benchmark
	cf push

# Legacy target - no longer needed as memtier_benchmark is installed via APT in Dockerfile
memtier_benchmark:
	@echo "memtier_benchmark is now installed via APT package in the Docker image"
	@echo "This target is kept for backward compatibility only"

# Docker multi-platform build targets
.PHONY: docker-build docker-buildx-setup docker-push

# Docker image configuration
# Usage: make docker-push TAG=v1.2.3
# To override image name: make docker-push IMAGE_NAME=myregistry/myimage TAG=v1.2.3
# To override memtier version: make docker-push TAG=v1.2.3 MEMTIER_VERSION=2.1.4
# WARNING: TAG is required for push commands to prevent accidental overwrites
IMAGE_NAME ?= redislabs/redis-webcli
TAG ?=
MEMTIER_VERSION ?= 2.1.1

# Setup buildx for multi-platform builds (run once)
docker-buildx-setup:
	docker buildx create --name multiarch --use || docker buildx use multiarch
	docker buildx inspect --bootstrap

# Build multi-platform image (AMD64 + ARM64)
docker-build:
	docker buildx build --platform linux/amd64,linux/arm64 \
		--build-arg MEMTIER_VERSION=$(MEMTIER_VERSION) \
		-t $(IMAGE_NAME):$(TAG) .

# Build and push multi-platform image (requires TAG to be set)
docker-push:
	@if [ -z "$(TAG)" ]; then \
		echo "Error: TAG is required. Usage: make docker-push TAG=v1.2.3"; \
		exit 1; \
	fi
	docker buildx build --platform linux/amd64,linux/arm64 \
		--build-arg MEMTIER_VERSION=$(MEMTIER_VERSION) \
		-t $(IMAGE_NAME):$(TAG) --push .


