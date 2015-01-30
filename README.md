# ansible-dkim
Ansible role for opendkim with postfix configuration on ubuntu

### Example playbook
```yaml
---
- hosts: myserver
  user: root
  sudo: False
  roles:
    - role: sunfoxcz.dkim
      dkim_selector: mail
      dkim_domains:
       - domain1.tld
       - domain2.tld
```
