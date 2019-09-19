# OpenSIPS CLI - TLS module

Using this module you can create TLS certificates and private keys.
There are two commands implemented in this module:
* `rootCA` - this command creates a self signed certificate for rootCA and
a private key for rootCA
* `userCERT` - this commnad creates a certificate which is signed by rootCA
and assigned to an user. Moreover, this command creates a private key for that
user and a ca-list(chain of trust in TSL)

## Configuration

This module can be configured from either one of the following files:
* ~/.opensips-cli.cfg
* /etc/opensips-cli.cfg
* /etc/opensips/opensips-cli.cfg
or you can specify your own config files in the following variables
(located in one of the above files):
* tls_ca_config - for `rootCA` command 
* tls_user_config - for `userCERT` command

List of parameters for configuring CA:
* tls_ca_common_name - the common name
* tls_ca_dir - the director where rootCA will be stored
* tls_ca_cert_file - the location of ca certificate inside the ca director
* tls_ca_key_file - the location of ca private key  inside the ca director
* tls_ca_key_size - the size of the RSA key
* tls_ca_country - the initials of the country(example: 'ro') 
* tls_ca_state - the state
* tls_ca_city - the city
* tls_ca_organisation - the name organisation
* tls_ca_organisational_unit - the organisation unit
* tls_ca_md - the md used for signing
* tls_ca_notafter - the valadity period
* tls_ca_overwrite - set this to y if you want to overwrite CA, n otherwise

List of parameters for configuring user certificate:
* tls_user_common_name - the common name
* tls_user_dir - the director where user files  will be stored
* tls_user_cacert - the path to the rootCA certificate
* tls_user_cakey - the path to the rootCA private key
* tls_user_cert_file - the location of user's certificate inside the ca dir
* tls_user_key_file - the location of user's private key  inside the ca dir
* tls_user_calist_file - location of user's ca trust chain inside the ca dir
* tls_user_key_size - the size of the RSA key
* tls_user_country - the initials of the country(example: 'ro') 
* tls_user_state - the state
* tls_user_city - the city
* tls_user_organisation - the name of the organisation
* tls_user_organisational_unit - the organisation unit
* tls_user_md - the md used for signing
* tls_user_notafter - the valadity period
* tls_user_serial - the serial for the user certificate
* tls_user_overwrite - set this to y if you want to overwrite cert,n otherwise


## Examples

To create a self signed certificate and a private key for rootCA enter this snippet:
```
opensips-cli -x tls rootCA
```
Configuration file example for rootCA:
```
[default]
tls_ca_common_name: www.opensips.com
tls_ca_dir: /etc/opensips/tls/rootCA
tls_ca_cert_file: cacert.pem
tls_ca_key_file: private/cakey.pem
tls_ca_key_size: 4096
tls_ca_country: ro
tls_ca_state: Ilfov
tls_ca_city: Bucharest
tls_ca_organisation: Opensips
tls_ca_organisational_unit: Solutions
tls_ca_md: sha1
tls_ca_notafter: 315360000
tls_ca_overwrite: yes
```

To create a user certificate signed by rootCA and private key and a ca-list(chain of trust in TSL):
```
opensips-cli -x tls userCERT
```
Configuration file example for userCERT:
```
[default]
tls_user_common_name: www.open.com
tls_user_dir: /etc/opensips/tls/user
tls_user_cacert: /etc/opensips/tls/rootCA/cacert.pem
tls_user_cakey: /etc/opensips/tls/rootCA/private/cakey.pem
tls_user_cert_file: user-cert.pem
tls_user_key_file: user-privkey.pem
tls_user_calist_file: user-calist.pem
tls_user_key_size: 4096
tls_user_country: ro
tls_user_state: Braila
tls_user_city: Braila
tls_user_organisation: Opensips
tls_user_organisational_unit: Solutions
tls_user_md: sha1
tls_user_notafter: 315360000
tls_user_serial: 2
tls_user_overwrite: yes
```
