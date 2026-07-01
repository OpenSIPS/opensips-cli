NAME ?= opensips-cli
OPENSIPS_DOCKER_TAG ?= latest

all: build start

.PHONY: build build-debian build-alpine start
build-debian:
	docker build -f Dockerfile \
		--tag="opensips/opensips-cli:$(OPENSIPS_DOCKER_TAG)" \
		.

build: build-debian

build-alpine:
	docker build -f Dockerfile.alpine \
		--tag="opensips/opensips-cli:alpine-$(OPENSIPS_DOCKER_TAG)" \
		.

start:
	docker run -d --name $(NAME) opensips/opensips-cli:$(OPENSIPS_DOCKER_TAG)
