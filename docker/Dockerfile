FROM python:slim-trixie
LABEL maintainer="Razvan Crainea <razvan@opensips.org>"

# Set Environment Variables
ENV DEBIAN_FRONTEND noninteractive

COPY . /usr/src/opensips-cli
RUN cd /usr/src/opensips-cli && \
    python3 -m pip install --no-cache-dir . && \
    cd / && rm -rf /usr/src/opensips-cli

ADD "docker/run.sh" "/run.sh"

ENV PYTHONPATH /usr/lib/python3/dist-packages

ENTRYPOINT [ "/run.sh", "-o", "communication_type=http" ]
