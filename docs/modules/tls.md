# OpenSIPS CLI - TLS module

Using the `tls` module, you can generate TLS certificates and private keys.

The module has the following subcommands:
* `rootCA` - generates a CA (certification authority) self signed certificate
and private key pair.  These are to be used by a TLS server.
* `userCERT` - generates a certificate signed by a given CA, a private key and
a CA list (chain of trust) file.  These are to be used by TLS clients (users).
* `db_add` - adds a new TLS domain to the `tls_mgm` table.
* `db_update` - changes the columns of an existing TLS domain.
* `db_list` - lists the TLS domains provisioned in the `tls_mgm` table.
* `db_show` - prints the columns of a TLS domain.
* `db_delete` - removes a TLS domain from the `tls_mgm` table.

The `db_*` subcommands provision the `tls_mgm` module over the database, where
the certificate, private key and CA list are stored as BLOB values rather than
as paths to files.  A TLS domain is identified by its name and its type
(`server` or `client`), both passed as arguments:
```
opensips-cli -x tls db_delete a.example.org server
```
The domain and its type may also be given by name, in which case they can
appear anywhere among the other columns:
```
opensips-cli -x tls db_delete domain=a.example.org type=server
```
Giving one of them both ways at once is an error.  The commands addressing a
single domain ask for whatever is left out; `db_add` and `db_show` default the
type to `server`, while `db_update` and `db_delete` have no default and keep
asking until one is given, so that they cannot change a different domain than
the intended one.

`db_add` and `db_update` take the remaining `tls_mgm` columns as `column=value`
arguments, in any order and after the domain and the type:
```
opensips-cli -x tls db_add a.example.org server method=TLSv1_2 verify_cert=1
```
The settable columns are `match_ip_address`, `match_sip_domain`, `method`,
`verify_cert`, `require_cert`, `certificate`, `private_key`, `crl_check_all`,
`crl_dir`, `ca_list`, `ca_dir`, `cipher_list`, `dh_params` and `ec_curve`.  A
column that is not given is left to its default in the database schema;
`db_update` only changes the columns it is given.

The `certificate`, `private_key`, `ca_list` and `dh_params` columns hold PEM
content, so their value is the path of the file holding it, and that file is
read and stored in the table:
```
opensips-cli -x tls db_add a.example.org server \
	certificate=/etc/opensips/tls/user/user-cert.pem \
	private_key=/etc/opensips/tls/user/user-privkey.pem
```
Every other column is stored as the value it is given, paths included: for
example, `ca_list` reads the file it points to, while `ca_dir` and `crl_dir`
keep the directory as such, which is what `tls_mgm` expects of them.

After every change, the `tls_reload` MI command is issued so that a running
OpenSIPS picks up the new domains.  If OpenSIPS cannot be reached, a warning is
logged and the domains are loaded at the next restart.

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
* tls_ca_md - the digest algorithm to use for signing (e.g. SHA256)

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
* tls_user_md - the digest algorithm to use for signing (e.g. SHA256)

List of `opensips-cli.cfg` settings for the `db_*` subcommands:

* database_tls_url - URL of the database holding the `tls_mgm` table; falls
back to `database_url`
* database_tls_name - name of the database; falls back to `database_name`


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
tls_ca_md: SHA256
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
tls_user_md: SHA256
```

To provision the certificate generated above as a TLS domain in the database:
```
opensips-cli -x tls db_add a.example.org server \
	certificate=/etc/opensips/tls/user/user-cert.pem \
	private_key=/etc/opensips/tls/user/user-privkey.pem \
	ca_list=/etc/opensips/tls/user/user-calist.pem
```
Certificates issued by a public CA are provisioned the same way:
```
opensips-cli -x tls db_add a.example.org server \
	certificate=/etc/letsencrypt/live/a.example.org/fullchain.pem \
	private_key=/etc/letsencrypt/live/a.example.org/privkey.pem
```
Configuration file example for the `db_*` subcommands:
```
[default]
database_url: mysql://opensips:opensipsrw@localhost
database_name: opensips
```

To renew the certificate of a domain, or to change any of its other columns:
```
opensips-cli -x tls db_update a.example.org server \
	certificate=/etc/letsencrypt/live/a.example.org/fullchain.pem \
	private_key=/etc/letsencrypt/live/a.example.org/privkey.pem
opensips-cli -x tls db_update a.example.org server cipher_list=HIGH
```

To inspect and remove the provisioned domains:
```
opensips-cli -x tls db_list
opensips-cli -x tls db_show a.example.org server
opensips-cli -x tls db_delete a.example.org server
```
