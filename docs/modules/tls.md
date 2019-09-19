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
    tls_ca_config - for `rootCA` command 
    tls_user_config - for `userCERT` command

List of parameters for configuring CA:
    tls_ca_common_name - the common name
    tls_ca_dir - the director where rootCA will be stored
    tls_ca_cert_file - the location of ca certificate inside the ca director
    tls_ca_key_file - the location of ca private key  inside the ca director
    tls_ca_key_size - the size of the RSA key
    tls_ca_country - the initials of the country(example: 'ro') 
    tls_ca_state - the state
    tls_ca_city - the city
    tls_ca_organisation - the name organisation
    tls_ca_organisational_unit - the organisation unit
    tls_ca_md - the md used for signing
    tls_ca_notafter - the valadity period
    tls_ca_overwrite - set this to y if you want to overwrite CA, n otherwise

List of parameters for configuring user certificate:
    tls_user_common_name - the common name
    tls_user_dir - the director where user files  will be stored
    tls_user_cacert - the path to the rootCA certificate
    tls_user_cakey - the path to the rootCA private key
    tls_user_cert_file - the location of user's certificate inside the ca dir
    tls_user_key_file - the location of user's private key  inside the ca dir
    tls_user_calist_file - location of user's ca trust chain inside the ca dir
    tls_user_key_size - the size of the RSA key
    tls_user_country - the initials of the country(example: 'ro') 
    tls_user_state - the state
    tls_user_city - the city
    tls_user_organisation - the name of the organisation
    tls_user_organisational_unit - the organisation unit
    tls_user_md - the md used for signing
    tls_user_notafter - the valadity period
    tls_user_serial - the serial for the user certificate
    tls_user_overwrite - set this to y if you want to overwrite cert,n otherwise


## Examples

```
opensips-cli -x tls rootCA
```

```
opensips-cli -x tls userCERT
```
