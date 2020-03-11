Opendkim Ansible role
============================

This role, Opendkim, installs and configures opendkim and postfix on Debian .

It works on Debian Stretch. It should work on Ubuntu or other Debian-based systems.

Description
------------

This role creates a dkim key for each host hosted on the server.
- install and configure opendkim,
- create the keys of the domains declared in the dkim_domains variable
- install and configure postfix

Requirements
------------

This role does not require prior installation, it only has a Debian or Ubuntu system

Note
----

This role is based on [FoxyRoles/ansible-dkim](https://github.com/FoxyRoles/ansible-dkim) role

Role Variables
--------------

### Client vars

Each client configuration overrides global configuration. Thew following variables can be defined:

- `dkim_create`: true or false (default: true). If true, configures the opendkin and create or replace keys present, else install opendkim and configure postfix.
`dkim_selector`: use that will be given to the key (default: email)
`dkim_admin_email`: administrator email (default: example@domain.com)
`dkim_domains`:  Domains for which keys must be created
  - domain1.tld
  - domain2.tld
  - domain3.tld

Example Playbook
----------------

### Quick and dirty

You should look at [defaults/main.yml](defaults/main.yml).

License
-------

GPLv3

Author Information
------------------

Original role [Tomáš Jacík](https://github.com/foxycode) enhanced by [Víctor Torterola](https://github.com/UdelaRInterior)