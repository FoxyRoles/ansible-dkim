# ansible-dkim

Ansible role for configuring [Postfix](http://www.postfix.org/) with [OpenDKIM](http://opendkim.org/) support on [Ubuntu](https://ubuntu.com/).

### Example playbook
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
```

### License

Licensed under MIT license. See [LICENSE](LICENSE.md) for details.
