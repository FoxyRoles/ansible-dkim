# ansible-dkim

Ansible role for configuring [Postfix](http://www.postfix.org/) with [OpenDKIM](http://opendkim.org/), an implementation for Linux of [DKIM mail signing](http://dkim.org/). Works on [Debian](https://debian.org) distributions and derived like [Ubuntu](https://ubuntu.com/).

## Description

This role configures DKIM mail signing service in a hosts that works as a Mail Transport Agent (MTA).

The role:
* installs and configures opendkim,
* creates private and public dkim keys for the domains it has to sign, declared in the `dkim_domains` variable,
* installs postfix and configures it to pass all the messages of the configured domains to be signed by opendkim,
* shows the DNS records with the public keys and reports whether each TXT value is present.

## Requirements

The role requires that you configure all the rest of the mail management and you will need to have access to the DNS configuration of the domains you are requesting to sign. At the end, the role will give you the DNS records with the public keys of the domains that you will have to publish in the global DNS system.

The DNS lookup uses `dig` on the Ansible controller. If `dig` is unavailable,
the role prints a warning and reports `dns_status: lookup_failed`.

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

See also comments and default values in role's file [`default/main.yml`](default/main.yml).

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
| `dkim_rsa_keylen:` | 2048 | RSA keylength when generating keys with `opendkim-keygen`. Other currently possible options are 1024 or 4096.  |
| `dkim_conf_override:` | empty | Additional config inserted into /etc/opendkim.conf, such as "Nameservers 127.0.0.1". |

### Postfix configuration variables

|  Variable     |   Default value   |   Description  |
|:-------------------:|:------------------------:|:------------:|
| `dkim_postfix_config_file:` | /etc/postfix/main.cf | Postfix main configuration file |
| `dkim_postfix_config:` | see [`vars/main.yml`](vars/main.yml) | List of parameters to be defined in Postfix configuration. Default configuration ensures opendkim is set up as a milter of Postfix to sign mails. You can define additional Postfix parameters using a list union. |

### Migrating existing keys

The role reads the existing `KeyTable` before configuring OpenDKIM. For every
row pointing directly to `keys/<selector>.private`, it copies the private key
and its `.txt` DNS record to `keys/<domain>/`, using the domain and selector
from that row. Each domain gets its own copy of a shared legacy key. The role
updates the `KeyTable` paths and removes the original pair after OpenDKIM
restarts successfully. If a destination has a different private key or a
source file is missing, the migration stops and keeps the original files.


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

### License

Licensed under MIT license. See [LICENSE](LICENSE.md) for details.
