FROM python:3.9-slim-buster
LABEL maintainer="Razvan Crainea <razvan@opensips.org>"

USER root

# Set Environment Variables
ENV DEBIAN_FRONTEND noninteractive

#install basic components
RUN apt-get -y update -qq && \
    apt-get -y install git default-libmysqlclient-dev gcc

#add keyserver, repository
RUN git clone https://github.com/OpenSIPS/opensips-cli.git /usr/src/opensips-cli && \
    cd /usr/src/opensips-cli && \
    python3 setup.py install clean --all && \
    cd / && rm -rf /usr/src/opensips-cli

RUN apt-get purge -y git gcc && \
    apt-get autoremove -y && \
    apt-get clean

ADD "run.sh" "/run.sh"

ENV PYTHONPATH /usr/lib/python3/dist-packages

ENTRYPOINT ["/run.sh", "-o", "communication_type=http"]
