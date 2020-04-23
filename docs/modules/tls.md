# OpenSIPS CLI - TLS module

Using the `tls` module, you can generate TLS certificates and private keys.

The module has two subcommands:
* `rootCA` - generates a CA (certification authority) self signed certificate
and private key pair.  These are to be used by a TLS server.
* `userCERT` - generates a certificate signed by a given CA, a private key and
a CA list (chain of trust) file.  These are to be used by TLS clients (users).

## Configuration

Certificates and private keys can be customized using the following settings:

List of `opensips-cli.cfg` settings for configuring self-signed CA certificates:

* tls_ca_dir - output directory where the cert and key will be written to
* tls_ca_cert_file - output certificate file path, within `tls_ca_dir`
* tls_ca_key_file - output private key file path, within `tls_ca_dir`
* tls_ca_overwrite - set this to "y" in order to overwrite existing files
* tls_ca_common_name - the address of the website (e.g. "opensips.org")
* tls_ca_country - the initials of the country (e.g. "RO")
* tls_ca_state - the state (e.g. "Bucharest")
* tls_ca_locality - the city (e.g. "Bucharest")
* tls_ca_organisation - the name of the organisation (e.g. "OpenSIPS")
* tls_ca_organisational_unit - the organisational unit (e.g. "Project")
* tls_ca_notafter - the validity period, in seconds (e.g. 315360000)
* tls_ca_key_size - the size of the RSA key, in bits (e.g. 4096)
* tls_ca_md - the digest algorithm to use for signing (e.g. SHA1)

List of `opensips-cli.cfg` settings for configuring user certificates:

* tls_user_dir - output directory where the cert and key will be written to
* tls_user_cert_file - output certificate file path, within `tls_user_dir`
* tls_user_key_file - output private key file path, within `tls_user_dir`
* tls_user_calist_file - output CA list file path, within `tls_user_dir`
* tls_user_overwrite - set this to "y" in order to overwrite existing files
* tls_user_cacert - path to the input CA certificate
* tls_user_cakey - path to the input CA private key
* tls_user_common_name - the address of the website (e.g. "www.opensips.org")
* tls_user_country - the initials of the country (e.g. "RO")
* tls_user_state - the state (e.g. "Bucharest")
* tls_user_locality - the city (e.g. "Bucharest")
* tls_user_organisation - the name of the organisation (e.g. "OpenSIPS")
* tls_user_organisational_unit - the organisational unit (e.g. "Project")
* tls_user_notafter - the validity period, in seconds (e.g. 315360000)
* tls_user_key_size - the size of the RSA key, in bits (e.g. 4096)
* tls_user_md - the digest algorithm to use for signing (e.g. SHA1)


## Examples

To create a self-signed certificate and a private key for rootCA, enter this snippet:
```
opensips-cli -x tls rootCA
```
Configuration file example for rootCA:
```
[default]
tls_ca_dir: /etc/opensips/tls/rootCA
tls_ca_cert_file: cacert.pem
tls_ca_key_file: private/cakey.pem
tls_ca_overwrite: yes
tls_ca_common_name: opensips.org
tls_ca_country: RO
tls_ca_state: Bucharest
tls_ca_locality: Bucharest
tls_ca_organisation: OpenSIPS
tls_ca_organisational_unit: Project
tls_ca_notafter: 315360000
tls_ca_key_size: 4096
tls_ca_md: SHA1
```

To create a user certificate signed by the above rootCA, along with a private
key and a CA list (chain of trust) file:
```
opensips-cli -x tls userCERT
```
Configuration file example for userCERT:
```
[default]
tls_user_dir: /etc/opensips/tls/user
tls_user_cert_file: user-cert.pem
tls_user_key_file: user-privkey.pem
tls_user_calist_file: user-calist.pem
tls_user_overwrite: yes
tls_user_cacert: /etc/opensips/tls/rootCA/cacert.pem
tls_user_cakey: /etc/opensips/tls/rootCA/private/cakey.pem
tls_user_common_name: www.opensips.org
tls_user_country: RO
tls_user_state: Bucharest
tls_user_locality: Bucharest
tls_user_organisation: OpenSIPS
tls_user_organisational_unit: Project
tls_user_notafter: 315360000
tls_user_key_size: 4096
tls_user_md: SHA1
```
