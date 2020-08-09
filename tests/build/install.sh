#!/bin/bash
set -e
source /build/buildconfig
set -x

$minimal_apt_get_install init software-properties-common

#!/bin/sh
if [ "$(lsb_release -is)" = "Ubuntu" ] && [ "$(lsb_release -cs)" != "focal" ]; then

	apt-add-repository -y ppa:ansible/ansible
	apt update
elif [ "$(lsb_release -is)" = "Debian" ] && [ "$(lsb_release -cs)" = "stretch" ]; then
	echo "deb http://deb.debian.org/debian stretch-backports main" > /etc/apt/sources.list.d/backports.list
	apt update
	apt install -y ansible -t stretch-backports
elif [ "$(lsb_release -is)" = "Debian" ] && [ "$(lsb_release -cs)" = "buster" ]; then
	apt update
	apt install -y python
fi

$minimal_apt_get_install ansible

echo -e "all:\n  hosts:\n    localhost:\n      ansible_connection: local" > /etc/ansible/hosts
