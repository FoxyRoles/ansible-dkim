# Changelog of ansible-dkim role

##  [v1.1.0](https://github.com/FoxyRoles/ansible-dkim/releases/tag/v1.1.0) by [@ulvida](https://github.com/ulvida)
 * Option to sign all the domains with the same key or each domain with its own key,
 * DNS records with DKIM public keys to be configured in the public DNS for each domain we sign the mails for, are shown at the end of the playbook,
 * Parametrisation of several values in the playbook previously hard-coded.

##  [v1.0.0](https://github.com/FoxyRoles/ansible-dkim/releases/tag/v1.0.0) by [@foxycode](https://github.com/foxycode)

 * First released version
 * Configuration of Opendkim to sign mails for a list of domains as a milter of postfix
 * Use of the same key for all domains
