#!/bin/bash
set -e
source /build/buildconfig
set -x

$minimal_apt_get_install init software-properties-common

if [[ "$(lsb_release -cs)" != "focal" ]]; then
	apt-add-repository -y ppa:ansible/ansible
	apt update
fi

$minimal_apt_get_install ansible

echo -e "all:\n  hosts:\n    localhost:\n      ansible_connection: local" > /etc/ansible/hosts
