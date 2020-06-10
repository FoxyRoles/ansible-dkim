#!/bin/bash
set -e
source /build/buildconfig
set -x

## Upgrade all packages.
apt-get update
apt-get dist-upgrade -y --no-install-recommends -o Dpkg::Options::="--force-confdef"
