import argparse
import json
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


def verify_domains(container, unknown_signing, unknown_keys):
    for table, unknown_present in [('SigningTable', unknown_signing), ('KeyTable', unknown_keys)]:
        content = subprocess.check_output(
            ['docker', 'exec', container, 'cat', f'/etc/opendkim/{table}'], text=True,
        )
        if 'first.example.test' not in content or ('second.example.test' in content) != unknown_present:
            raise RuntimeError(f'Unexpected contents of {table}:\n{content}')
        if table == 'KeyTable' and unknown_keys and '/keys/second.example.test/email.private' not in content:
            raise RuntimeError(f'Unexpected key path in {table}:\n{content}')

    for domain, expected in [('first.example.test', True), ('second.example.test', unknown_keys)]:
        directory = f'/etc/opendkim/keys/{domain}'
        result = subprocess.run(['docker', 'exec', container, 'test', '-d', directory])
        if result.returncode != (0 if expected else 1):
            raise RuntimeError(f'Unexpected key directory state: {directory}')
        verify_key_pair(container, f'{directory}/email', expected)


def verify_key_pair(container, key_path, expected):
    for extension in ('private', 'txt'):
        path = f'{key_path}.{extension}'
        result = subprocess.run(['docker', 'exec', container, 'test', '-f', path])
        if result.returncode != (0 if expected else 1):
            raise RuntimeError(f'Unexpected key file state: {path}')


def restore_legacy_key_layout(container):
    subprocess.run(
        ['docker', 'exec', container, 'sh', '-ec', r'''
            cd /etc/opendkim
            mv keys/second.example.test/email.private keys/email.private
            mv keys/second.example.test/email.txt keys/email.txt
            rmdir keys/second.example.test
            sed -i 's|/keys/second\.example\.test/email\.private|/keys/email.private|' KeyTable
        '''],
        check=True,
    )


def verify_idempotence(command, environment):
    repeated_run = subprocess.run(command, env=environment, text=True, stdout=subprocess.PIPE)
    print(repeated_run.stdout, end='', flush=True)
    repeated_run.check_returncode()
    if not re.search(r'^dkim_test\s*:.*\bchanged=0\b', repeated_run.stdout, re.MULTILINE):
        raise RuntimeError('The role changed on a repeated run')


def verify_domain_report(command, environment, expected):
    result = subprocess.run(command, env=environment, check=True, text=True, stdout=subprocess.PIPE)
    print(result.stdout, end='', flush=True)
    report = result.stdout.partition('TASK [dkim : Report deactivated domains to append to dkim_domains]')[2]
    report = re.split(r'\n(?:TASK \[|RUNNING HANDLER \[|PLAY RECAP)', report, maxsplit=1)[0]
    payload = report.partition('ok: [dkim_test] =>')[2].strip()
    domains = yaml.safe_load(payload)['msg']['dkim_domains'] if payload else []
    if domains != expected:
        raise RuntimeError(f'Expected deactivated domains {expected}, got {domains}')


def test_unknown_domains(container, command, environment):
    selected = {'dkim_domains': ['first.example.test']}
    for deactivate in (False, True):
        restore_legacy_key_layout(container)
        if deactivate:
            selected['dkim_deactivate_unknown'] = True
        verify_domain_report(
            [*command, '--extra-vars', json.dumps(selected)], environment,
            ['second.example.test'] if deactivate else [],
        )
        verify_domains(container, unknown_signing=not deactivate, unknown_keys=True)
        verify_key_pair(container, '/etc/opendkim/keys/email', expected=False)

    preserve = dict(selected, dkim_deactivate_unknown=False)
    verify_domain_report(
        [*command, '--extra-vars', json.dumps(preserve)], environment, ['second.example.test'],
    )
    verify_domains(container, unknown_signing=False, unknown_keys=True)

    verify_domain_report(command, environment, [])
    marker = '/etc/opendkim/keys/third.example.test/.keep'
    subprocess.run(['docker', 'exec', container, 'install', '-D', '/dev/null', marker], check=True)
    selected['dkim_delete_unknown'] = True
    delete_command = [*command, '--extra-vars', json.dumps(selected)]
    verify_domain_report([*delete_command, '--check'], environment, [])
    verify_domains(container, unknown_signing=True, unknown_keys=True)
    verify_domain_report(delete_command, environment, [])
    verify_domains(container, unknown_signing=False, unknown_keys=False)
    subprocess.run(['docker', 'exec', container, 'test', '-f', marker], check=True)
    verify_idempotence(delete_command, environment)


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
        verify_idempotence(command, environment)
        test_unknown_domains(container, command, environment)
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
