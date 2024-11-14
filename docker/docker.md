# OpenSIPS CLI Docker Image

Docker recipe for running [OpenSIPS Command Line
Interface](https://github.com/OpenSIPS/opensips-cli).

## Building the image
You can build the docker image by running:
```
make build
```

This command will build a docker image with OpenSIPS CLI master version taken from
the git repository

## Parameters

The container receives parameters in the following format:
```
[-o KEY=VALUE]* CMD [PARAMS]*
```

Meaning of the parameters is as it follows:

* `-o KEY=VALUE` - used to tune `opensips-cli` at runtime; these parameters
will end up in opensips-cli config file, in the `default` section, as
`KEY: VALUE` lines
* `CMD` - the command used to run; if the `CMD` ends with `.sh` extension, it
will be run as a bash script, if the `CMD` ends with `.py` extension, it is
run as a python script, otherwise it is run as a `opensips-cli` command
* `PARAMS` - optional additional parameters passed to `CMD`

## Run

To run a bash script, simply pass the connector followed by the bash script:
```
docker run -d --name opensips-cli opensips/opensips-cli:latest \
		   -o url=http://8.8.8.8:8888/mi script.sh
```

Similarly, run a python script:
```
docker run -d --name opensips-cli opensips/opensips-cli:latest \
		   -o url=http://8.8.8.8:8888/mi script.py
```

To run a single MI command, use:
```
docker run -d --name opensips-cli opensips/opensips-cli:latest \
		   -o url=http://8.8.8.8:8888/mi -x mi ps
```

## DockerHub

Docker images are available on
[DockerHub](https://hub.docker.com/r/opensips/opensips-cli).
