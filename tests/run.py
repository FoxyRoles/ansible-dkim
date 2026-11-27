import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from uuid import uuid4

from ansible.release import __version__ as ansible_version
import yaml


TESTS = Path(__file__).resolve().parent
ROLE = TESTS.parent

IMAGE_TAGS_BY_CODENAME = {
    'ubuntu:focal': 'ubuntu:20.04',
    'ubuntu:jammy': 'ubuntu:22.04',
    'ubuntu:noble': 'ubuntu:24.04',
    'ubuntu:resolute': 'ubuntu:26.04',
    'debian:bookworm': 'debian:12',
    'debian:trixie': 'debian:13',
}

# Focal's Python 3.8 requires Ansible 2.19. Resolute's Python 3.14 requires 2.20 or later.
ANSIBLE_CORES_BY_IMAGE = {
    'ubuntu:20.04': ('2.19',),
    'ubuntu:26.04': ('2.20', '2.21'),
}


def wait_for_systemd(container):
    for _ in range(60):
        ready = subprocess.run(
            ['docker', 'exec', container, 'systemctl', 'is-active', '--quiet', 'multi-user.target'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if ready.returncode == 0:
            return
        time.sleep(1)
    subprocess.run(['docker', 'logs', container], check=False)
    raise RuntimeError(f'systemd did not reach multi-user.target in {container}')


def test_image(image, playbook, workspace, environment):
    print(f'Testing {playbook.stem} on {image} with ansible-core {ansible_version}', flush=True)
    tag = f'sunfoxcz-dkim-test:{image.replace(":", "-")}'
    subprocess.run(
        ['docker', 'build', '--pull', '--build-arg', f'BASE_IMAGE={image}',
         '--tag', tag, str(TESTS)],
        check=True,
    )

    container = f'dkim-test-{uuid4().hex}'
    try:
        subprocess.run(
            ['docker', 'run', '--detach', '--name', container, '--hostname', 'dkim.example.test',
             '--cgroupns=private', '--security-opt', 'writable-cgroups=true',
             '--tmpfs', '/run', '--tmpfs', '/run/lock', tag],
            check=True,
        )
        wait_for_systemd(container)

        host = {
            'ansible_connection': 'community.docker.docker',
            'ansible_host': container,
            'ansible_python_interpreter': '/usr/bin/python3',
        }
        inventory = workspace / 'inventory.yml'
        inventory.write_text(yaml.safe_dump({'all': {'hosts': {'dkim_test': host}}}))
        command = [sys.executable, '-m', 'ansible.cli.playbook', '-i', str(inventory), str(playbook)]
        subprocess.run([*command, '--syntax-check'], env=environment, check=True)
        subprocess.run(command, env=environment, check=True)

        second_run = subprocess.run(command, env=environment, text=True, stdout=subprocess.PIPE)
        print(second_run.stdout, end='', flush=True)
        second_run.check_returncode()
        if not re.search(r'^dkim_test\s*:.*\bchanged=0\b', second_run.stdout, re.MULTILINE):
            raise RuntimeError(f'{playbook.stem} was not idempotent on {image}')
    finally:
        subprocess.run(['docker', 'rm', '--force', container], stdout=subprocess.DEVNULL, check=False)


def main():
    metadata = yaml.safe_load((ROLE / 'meta' / 'main.yml').read_text())['galaxy_info']
    codenames = (
        f'{platform["name"].lower()}:{version}'
        for platform in metadata['platforms']
        for version in platform['versions']
    )
    images = {codename: IMAGE_TAGS_BY_CODENAME.get(codename, codename) for codename in codenames}
    default_cores = (metadata['min_ansible_version'], '2.21')

    parser = argparse.ArgumentParser(description='Run the DKIM role in systemd containers.')
    parser.add_argument('mta', choices=('postfix', 'sendmail'))
    parser.add_argument(
        '--image', choices=sorted(images.keys() | images.values()),
        help='Test just this image with the installed Ansible.',
    )
    args = parser.parse_args()

    core_series = '.'.join(ansible_version.split('.')[:2])
    selected = [images.get(args.image, args.image)] if args.image else [
        image for image in images.values()
        if core_series in ANSIBLE_CORES_BY_IMAGE.get(image, default_cores)
    ]
    if not selected:
        parser.error(f'no images assigned to ansible-core {core_series}; choose a test version or --image')

    cgroup_version = subprocess.check_output(
        ['docker', 'info', '--format', '{{.CgroupVersion}}'], text=True,
    ).strip()
    if cgroup_version != '2':
        parser.error('the Docker daemon must use cgroups v2')

    with TemporaryDirectory(prefix='dkim-test-') as directory:
        workspace = Path(directory)
        (workspace / 'dkim').symlink_to(ROLE, target_is_directory=True)
        config = workspace / 'ansible.cfg'
        config.write_text('[defaults]\n')
        environment = dict(
            os.environ, ANSIBLE_CONFIG=str(config), ANSIBLE_ROLES_PATH=directory,
            ANSIBLE_LOCAL_TEMP=directory, ANSIBLE_NOCOLOR='true', ANSIBLE_STDOUT_CALLBACK='default',
        )
        playbook = TESTS / f'{args.mta}.yml'
        for image in selected:
            test_image(image, playbook, workspace, environment)


if __name__ == '__main__':
    main()
