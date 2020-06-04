# ansible-dkim

Ansible role for configuring [Postfix](http://www.postfix.org/) with [OpenDKIM](http://opendkim.org/). Works on [Debian](https://debian.org) distributions and derived like [Ubuntu](https://ubuntu.com/).

## Description

This role confiures DKIM mail singing service in a hosts that works as an e-mail MTA. 

The role: 
* installs and configures opendkim,
* creates private and public dkim keys for the domains it has to sign, declared in the `dkim_domains` variable,
* installs postfix and configures it to pass all the messages of the configured domains to be signed by opendkim,
* shows the DNS records with the public keys that must be defined in the public DNS of the domains we sign.

## Requirements

The role requires that you configure all the rest of the mail management and you will need to have access to the DNS configuration of the domains you are requiesting to sign. At the end, the role will give you the DNS records with the public keys of the domains that you will have to publish in the global DNS system.  

## Role variable

See also comments and default values in role's file `default/main.yml`.

### Opendkim package parameters

|  Variable     |   Default value   |   Description  |
|:-------------------:|:------------------------:|:------------:|
| `dkim_default_config_file:` | /etc/default/opendkim | Opendkim Default values configuration file |
| `dkim_opendkim_config:` | /etc/opendkim | Opendkim configuration folder |
| `dkim_user:` | opendkim | linux user that runs Opendkim | 
| `dkim_group:` | opendkim | linux group that runs Opendkim | 

### Opendkim configuration parameters

|  Variable     |   Default value   |   Description  |
|:-------------------:|:------------------------:|:------------:|
| `dkim_selector:` | email | Opendkim registers' selector |
| `dkim_admin_email:` | none | e-mail address that manages opendkim. You musrt define either `dkim_admin_email` or legacy `admin_email`. |
| `dkim_domains:` | none | List of domains that opendkim must be configured to sign the mails of. A yaml list of DNS. |
| `dkim_same_key:` | true | Whether opendkim must use the same keys for all domains or a set of keys for each domain.  |
| `dkim_dns_record_pause:` | 0 | The time (seconds) the role will pause to show the DNS records with the public keys that must be configured.  |

### Postfix configuration variables 

  Variable     |   Default value   |   Description  |
|:-------------------:|:------------------------:|:------------:|
| `dkim_postfix_config_file:` | /etc/postfix/main.cf | Postfix main configuration file. |
| `dkim_postfix_config:` | see `vars/main.yml` | list of parameters to be defined in postfix configuration. Default configuration ensures opendkim is set up as a milter of post fix to sign mails. You can define additional postfix parameters using a list union. |

## Example playbook
```yaml
---
- hosts: myserver
  roles:
    - role: sunfoxcz.dkim
      # if admin_email variable is present, will be used as default for dkim_admin_email
      dkim_admin_email: my@mail.tld
      dkim_selector: mail
      dkim_domains:
       - domain1.tld
       - domain2.tld
      dkim_same_key: false
```

### License

Licensed under MIT license. See [LICENSE](LICENSE.md) for details.
