# check=skip=InvalidDefaultArgInFrom

# The test runner must supply the target distribution image.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

ENV container=docker

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3 python3-apt systemd-sysv

CMD ["/sbin/init"]
