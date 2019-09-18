# OpenSIPS CLI - TLS module

Using this module you can create TLS certificates and private keys.
There are two commands implemented in this module:
* `tls rootCA` - this command creates a self signed certificate for rootCA and
a private key for rootCA
* `tls userCERT` - this commnad creates a certificate which is signed by rootCA
and assigned to an user. Moreover, this command creates a private key for that
user and a ca-list(chain of trust in TSL)

## Configuration

This module can be configured from either one of the following files:
    * ~/.opensips-cli.cfg
    * /etc/opensips-cli.cfg
    * /etc/opensips/opensips-cli.cfg
or you can specify your own config files in the following variables
(located in one of the above files):
    tls_ca_config - for `tls rootCA` command 
    tls_user_config - for `tls userCERT` command

## Examples

```
opensips-cli -x tls rootCA
```

```
opensips-cli -x tls userCERT
```
