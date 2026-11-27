# Changelog of sunfoxcz.ansible-dkim role

## [v2.0.0](https://github.com/FoxyRoles/ansible-dkim/releases/tag/2.0.0)

### Upgrade notes

* The role now requires ansible-core 2.19 or later. Supported targets are Ubuntu 20.04, 22.04, 24.04, and 26.04, and Debian 12 and 13. Ubuntu 26.04 with its default Python requires ansible-core 2.20 or later.
* Set `dkim_admin_email` explicitly. The `admin_email` fallback was removed.
* Removed `dkim_same_key`. Missing signing keys are generated per domain. Existing shared key pairs are copied into the domain directories that reference them, preserving their DNS records.
* Removed `dkim_generate_only`. The role generates missing keys and deploys the signing configuration in the same run.

### Configuration and reporting

* Migrates retained legacy key pairs into `keys/<domain>/` and updates `KeyTable`. The role validates the OpenDKIM configuration, restores the previous signing tables if deployment fails, and removes old key pairs only after OpenDKIM has restarted and the deployed `KeyTable` has no remaining references to them.
* Keeps existing signing rules and keys for domains outside `dkim_domains` by default. Set `dkim_deactivate_unknown` to remove their signing rules and retain their keys, or set `dkim_delete_unknown` to also remove their `KeyTable` entries and unused key files.
* Reports domains missing from `dkim_domains` that still appear in the resulting `SigningTable` or `KeyTable`.
* Displays TXT records for the keys used by the resulting `SigningTable`, including preserved signing rules. It uses `dig` on the Ansible controller to report whether each record is published, missing, different, or could not be checked. The comparison joins TXT chunks and ignores spaces or tabs after semicolons. The report preserves quoted TXT chunks and can derive the public record for a file-based RSA key when its `.txt` file is missing.
* Added `dkim_conf_override` for extra OpenDKIM directives and `dkim_managed_comment` for generated file headers. OpenDKIM now uses the configured directory, user, and group in its generated configuration.
* Validates `dkim_domains` and `dkim_mta`, selects the MTA integration per host, and installs OpenSSL for key generation.

### Integration tests

* Moved integration tests from Travis CI to GitHub Actions. The Docker matrix covers Postfix and Sendmail on the supported Ubuntu and Debian versions and checks idempotence, legacy key migration, and handling of unlisted domains.

## [v1.3.0](https://github.com/FoxyRoles/ansible-dkim/releases/tag/1.3.0)

* Added `dkim_generate_only` to generate keys and display DNS records while leaving the deployed `KeyTable` and `SigningTable` in place.
* Switched OpenDKIM, Postfix, and Sendmail package installation from `apt` to the generic Ansible `package` module.
* Improved the readability of the public DKIM DNS record output.
* Replaced the deprecated `get_md5` option with `get_checksum: false` when checking whether the signing key exists.

## [v1.2.0](https://github.com/FoxyRoles/ansible-dkim/releases/tag/1.2.0)

* Added Sendmail support through `dkim_mta`. Postfix remains the default.
* Rendered `TrustedHosts` from the configurable `dkim_trustedhosts` list and restarted Postfix when its configuration changed.
* Made the RSA key length configurable through `dkim_rsa_keylen`, with a default of 2048 bits, and set the keys directory to mode `0750` and group `dkim_group`.
* Displayed public DKIM DNS records without pausing the play and read them from `dkim_opendkim_config_dir`.
* Added continuous integration tests for shared keys, per-domain keys, and Sendmail. Updated Galaxy metadata to declare Ansible 2.7 as the minimum and removed Debian Jessie from the platform list.

## [v1.1.0](https://github.com/FoxyRoles/ansible-dkim/releases/tag/1.1.0)
 * Option to sign all the domains with the same key or each domain with its own key,
 * DNS records with DKIM public keys to be configured in the public DNS for each domain we sign the mails for, are shown at the end of the playbook,
 * Parametrisation of several values in the playbook previously hard-coded.

## [v1.0.0](https://github.com/FoxyRoles/ansible-dkim/releases/tag/1.0.0)

 * First released version
 * Configuration of Opendkim to sign mails for a list of domains as a milter of postfix
 * Use of the same key for all domains
