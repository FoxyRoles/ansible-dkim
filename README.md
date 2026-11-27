# sunfoxcz.ansible-dkim

Ansible role for configuring [OpenDKIM](http://opendkim.org/) mail signing with [Postfix](http://www.postfix.org/) or Sendmail on Debian and Ubuntu.

## Description

This role configures DKIM mail signing service in a hosts that works as a Mail Transport Agent (MTA).

The role:
* installs and configures opendkim,
* creates private and public dkim keys for the domains it has to sign, declared in the `dkim_domains` variable,
* installs the selected MTA and configures OpenDKIM as a mail filter,
* shows the DNS records with the public keys and reports whether each TXT value is present.

## Requirements

The role requires `ansible-core` 2.19 or later. Use ansible-core 2.19 for
managed hosts running Python 3.8, including Ubuntu 20.04 LTS with its default
Python. The controller needs Python 3.11–3.13 to run ansible-core 2.19.
Ubuntu 26.04 LTS uses Python 3.14 by default and needs ansible-core 2.20 or
later with that interpreter.

The role requires that you configure all the rest of the mail management and you will need to have access to the DNS configuration of the domains you are requesting to sign. At the end, the role will give you the DNS records with the public keys of the domains that you will have to publish in the global DNS system.

The DNS lookup uses `dig` on the Ansible controller. If `dig` is unavailable,
the role prints a warning and reports `dns_status: lookup_failed`.
The role reports TXT records for keys referenced by the resulting `SigningTable`,
including preserved signing rules. It uses each key's domain, selector and file
path from `KeyTable`. For RSA keys without a companion `.txt` file, it derives
the public key on the managed host.

## Ansible output format

To display long DKIM TXT values on a single line, run your playbook with these
Ansible callback settings.

```sh
ANSIBLE_CALLBACK_RESULT_FORMAT=yaml ANSIBLE_CALLBACK_YAML_LINE_WIDTH=no-break \
  ansible-playbook -i inventory playbook.yml
```

With the default stdout callback, `ANSIBLE_CALLBACK_RESULT_FORMAT=yaml` formats
displayed task results throughout the run. `ANSIBLE_CALLBACK_YAML_LINE_WIDTH=no-break`
disables automatic YAML line wrapping and requires ansible-core 2.21 or later.
[Ansible stdout callback documentation](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/default_callback.html)

## Role variable

See also comments and default values in role's file [`defaults/main.yml`](defaults/main.yml).

### Opendkim package parameters

|  Variable     |   Default value   |   Description  |
|:-------------------:|:------------------------:|:------------:|
| `dkim_default_config_file:` | /etc/default/opendkim | Opendkim default values configuration file |
| `dkim_opendkim_config_dir:` | /etc/opendkim | Opendkim configuration directory |
| `dkim_user:` | opendkim | linux user that runs Opendkim |
| `dkim_group:` | opendkim | linux group that runs Opendkim |

### Opendkim configuration parameters

|  Variable     |   Default value   |   Description  |
|:-------------------:|:------------------------:|:------------:|
| `dkim_selector:` | email | DKIM Public Key DNS record's selector. The definition of a value specific to the MTA server allows to associate the same domain several DKIM Public Keys as DNS records, one for each server that manages and signs mail of the domain.  |
| `dkim_admin_email:` | none | Required OpenDKIM administrator email address. |
| `dkim_trustedhosts:` | `['127.0.0.1','localhost']` | List of trusted hosts for opendkim |
| `dkim_domains:` | none | List of domains that Opendkim must be configured to sign the mails of. A yaml list of DNS. |
| `dkim_deactivate_unknown:` | `false` | Rebuild `SigningTable` from `dkim_domains`. Existing `KeyTable` entries and keys for unlisted domains are kept. |
| `dkim_delete_unknown:` | `false` | Rebuild `SigningTable` from `dkim_domains`, remove unlisted domains from `KeyTable`, and delete their unused key files. Overrides `dkim_deactivate_unknown`. |
| `dkim_rsa_keylen:` | 2048 | RSA keylength when generating keys with `opendkim-keygen`. Other currently possible options are 1024 or 4096.  |
| `dkim_mta:` | `postfix` | Mail transport agent. Set to `postfix` or `sendmail` in the playbook or inventory. |
| `dkim_managed_comment:` | `ansible_managed` if defined, otherwise `Ansible managed` | Header comment in generated OpenDKIM configuration files. |
| `dkim_conf_override:` | empty | Additional config inserted into /etc/opendkim.conf, such as "Nameservers 127.0.0.1". |

### Postfix configuration variables

|  Variable     |   Default value   |   Description  |
|:-------------------:|:------------------------:|:------------:|
| `dkim_postfix_config_file:` | /etc/postfix/main.cf | Postfix main configuration file |
| `dkim_postfix_config:` | see [`vars/main.yml`](vars/main.yml) | List of parameters to be defined in Postfix configuration. Default configuration ensures opendkim is set up as a milter of Postfix to sign mails. You can define additional Postfix parameters using a list union. |

### Unlisted domains

By default, existing signing rules and keys for domains outside `dkim_domains`
are preserved, and legacy keys are migrated. To stop signing for those domains
while keeping their keys, set `dkim_deactivate_unknown: true`. Domains that
were deactivated stay deactivated on subsequent runs with
`dkim_deactivate_unknown: false`. To restore a removed signing rule, add its
domain to `dkim_domains` in your playbook.

The `Report unknown domains` task lists domains in the resulting `SigningTable`
or `KeyTable` that are absent from `dkim_domains`. It includes domains with
preserved signing rules and domains whose keys are kept after deactivation.

Set `dkim_delete_unknown: true` to also retire the keys. Deletion covers
generated key files and their `.txt` companions in unlisted domain directories,
as well as legacy key pairs referenced by removed entries.
The role removes files from its `keys` directory after OpenDKIM adopts the new
tables. It removes empty key directories for unlisted domains and keeps keys
still referenced by the deployed `KeyTable`. Published DNS records stay in place.

### Migrating existing keys

The role migrates all retained legacy `KeyTable` rows, including rows for
unlisted domains, regardless of `dkim_deactivate_unknown`. For each retained
row pointing directly to `keys/<selector>.private`, it copies the private key
and its `.txt` DNS record to `keys/<domain>/`, then updates the `KeyTable` path.
It removes the original pair after OpenDKIM restarts and the last reference to
it is gone. If a destination has a different private key or a source file is
missing, the migration stops and keeps the original files.


## Example playbook
```yaml
---
- hosts: myserver
  roles:
    - role: sunfoxcz.dkim
      dkim_admin_email: my@mail.tld
      dkim_selector: mail
      dkim_domains:
       - domain1.tld
       - domain2.tld
```

## Integration tests

[GitHub Actions](.github/workflows/integration.yml) runs a separate job for each
image, MTA, and Ansible version in the matrix on pushes and pull requests.
Each job applies the role inside a systemd container built from the selected
release tag using Docker and Ansible on an Ubuntu 24.04 runner.

The test runner translates the platform codenames in `galaxy_info.platforms`
to versioned Docker tags. It checks idempotence, migration for unlisted domains
in both signing modes, TXT output for preserved signing rules, and reporting
before and after deactivation and deletion.
Run it on Linux with rootful Docker Engine 28 or later, cgroups v2, and a Python
3.12 virtual environment. Each container has a private cgroup namespace with a
writable cgroup mount for systemd.

```sh
python -m pip install 'ansible-core~=2.19.0'
ansible-galaxy collection install 'community.docker:>=5.4.0,<6'
python tests/run.py postfix
python tests/run.py sendmail
```

Use `ansible-core~=2.20.0` to test Ubuntu 26.04, or `ansible-core~=2.21.0` to
test all images from the matrix except Ubuntu 20.04. Use `--image ubuntu:20.04`
to select one image. Codename aliases such as `ubuntu:focal` also work.

### License

Licensed under MIT license. See [LICENSE](LICENSE.md) for details.
