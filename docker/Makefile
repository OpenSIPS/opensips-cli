NAME ?= opensips-cli
OPENSIPS_DOCKER_TAG ?= latest

all: build start

.PHONY: build start
build:
	docker build \
		--tag="opensips/opensips-cli:$(OPENSIPS_DOCKER_TAG)" \
		.

start:
	docker run -d --name $(NAME) opensips/opensips-cli:$(OPENSIPS_DOCKER_TAG)
