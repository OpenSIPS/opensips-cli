#!/usr/bin/env python
##
## This file is part of OpenSIPS CLI
## (see https://github.com/OpenSIPS/opensips-cli).
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/>.
##

from opensipscli.module import Module
from opensipscli.logger import logger
from socket import gethostname
from pprint import pprint
from time import gmtime, mktime
from os.path import exists, join, dirname
from os import makedirs
from opensipscli.config import cfg, OpenSIPSCLIConfig
from random import randrange

try:
    from OpenSSL import crypto, SSL
    openssl_available = True
except ImportError:
    logger.info("OpenSSL library not available!")
    openssl_available = False

class tls(Module):
    def do_rootCA(self, params):
        global cfg
        logger.info("Preparing to generate CA cert + key...")

        # TODO
        # separate cli.cfg files for TLS are fully deprecated, this if block is
        # only kept for backwards-compatibility.  Remove starting from v3.2! <3
        if cfg.exists('tls_ca_config'):
            tls_cfg = cfg.get('tls_ca_config')
            cfg = OpenSIPSCLIConfig()
            cfg.parse(tls_cfg)

        ca_dir = cfg.read_param("tls_ca_dir", "Output directory", "/etc/opensips/tls/rootCA/")
        cert_file = cfg.read_param("tls_ca_cert_file", "Output cert file", "cacert.pem")
        key_file = cfg.read_param("tls_ca_key_file", "Output key file", "private/cakey.pem")
        c_f = join(ca_dir, cert_file)
        k_f = join(ca_dir, key_file)

        if (exists(c_f) or exists(k_f)) and not cfg.read_param("tls_ca_overwrite",
                "CA certificate or key already exists, overwrite?", "yes", True):
            return

        # create a self-signed cert
        cert = crypto.X509()

        cert.get_subject().CN = cfg.read_param("tls_ca_common_name", "Website address (CN)", "opensips.org")
        cert.get_subject().C = cfg.read_param("tls_ca_country", "Country (C)", "RO")
        cert.get_subject().ST = cfg.read_param("tls_ca_state", "State (ST)", "Bucharest")
        cert.get_subject().L = cfg.read_param("tls_ca_locality", "Locality (L)", "Bucharest")
        cert.get_subject().O = cfg.read_param("tls_ca_organisation", "Organization (O)", "OpenSIPS")
        cert.get_subject().OU = cfg.read_param("tls_ca_organisational_unit", "Organisational Unit (OU)", "Project")
        cert.set_serial_number(randrange(100000))
        cert.gmtime_adj_notBefore(0)
        notafter = int(cfg.read_param("tls_ca_notafter", "Certificate validity (seconds)", 315360000))
        cert.gmtime_adj_notAfter(notafter)
        cert.set_issuer(cert.get_subject())

        # create a key pair
        key = crypto.PKey()
        key_size = int(cfg.read_param("tls_ca_key_size", "RSA key size (bits)", 4096))
        key.generate_key(crypto.TYPE_RSA, key_size)

        cert.set_pubkey(key)
        md = cfg.read_param("tls_ca_md", "Digest Algorithm", "SHA1")
        cert.sign(key, md)

        try:
            if not exists(dirname(c_f)):
                makedirs(dirname(c_f))
            open(c_f, "wt").write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('utf-8'))
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to write to %s", c_f)
            return

        try:
            if not exists(dirname(k_f)):
                makedirs(dirname(k_f))
            open(k_f, "wt").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode('utf-8'))
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to write to %s", k_f)
            return

        logger.info("CA certificate created in " + c_f)
        logger.info("CA private key created in " + k_f)

    def do_userCERT(self, params):
        global cfg
        logger.info("Preparing to generate user cert + key + CA list...")

        # TODO
        # separate cli.cfg files for TLS are fully deprecated, this if block is
        # only kept for backwards-compatibility.  Remove starting from v3.2! <3
        if cfg.exists('tls_user_config'):
            tls_cfg = cfg.get('tls_user_config')
            cfg = OpenSIPSCLIConfig()
            cfg.parse(tls_cfg)

        user_dir = cfg.read_param("tls_user_dir", "Output directory", "/etc/opensips/tls/user/")
        cert_file = cfg.read_param("tls_user_cert_file", "Output cert file", "user-cert.pem")
        key_file = cfg.read_param("tls_user_key_file", "Output key file", "user-privkey.pem")
        calist_file = cfg.read_param("tls_user_calist_file", "Output CA list file", "user-calist.pem")

        c_f = join(user_dir, cert_file)
        k_f = join(user_dir, key_file)
        ca_f = join(user_dir, calist_file)

        if (exists(c_f) or exists(k_f) or exists(ca_f)) and not cfg.read_param("tls_user_overwrite",
                "User certificate, key or CA list file already exists, overwrite?", "yes", True):
            return

        cacert = cfg.read_param("tls_user_cacert", "CA cert file", "/etc/opensips/tls/rootCA/cacert.pem")
        cakey = cfg.read_param("tls_user_cakey", "CA key file", "/etc/opensips/tls/rootCA/private/cakey.pem")

        try:
            ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, open(cacert, 'rt').read())
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to load %s", cacert)
            return

        try:
            ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM, open(cakey, 'rt').read())
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to load %s", cakey)
            return

        # create a self-signed cert
        cert = crypto.X509()

        cert.get_subject().CN = cfg.read_param("tls_user_common_name", "Website address (CN)", "www.opensips.org")
        cert.get_subject().C = cfg.read_param("tls_user_country", "Country (C)", "RO")
        cert.get_subject().ST = cfg.read_param("tls_user_state", "State (ST)", "Bucharest")
        cert.get_subject().L = cfg.read_param("tls_user_locality", "Locality (L)", "Bucharest")
        cert.get_subject().O = cfg.read_param("tls_user_organisation", "Organization (O)", "OpenSIPS")
        cert.get_subject().OU = cfg.read_param("tls_user_organisational_unit", "Organisational Unit (OU)", "Project")

        cert.set_serial_number(randrange(100000))
        cert.gmtime_adj_notBefore(0)
        notafter = int(cfg.read_param("tls_user_notafter", "Certificate validity (seconds)", 315360000))
        cert.gmtime_adj_notAfter(notafter)
        cert.set_issuer(ca_cert.get_subject())

        # create a key pair
        key = crypto.PKey()
        key_size = int(cfg.read_param("tls_user_key_size", "RSA key size (bits)", 4096))
        key.generate_key(crypto.TYPE_RSA, key_size)

        cert.set_pubkey(key)
        md = cfg.read_param("tls_user_md", "Digest Algorithm", "SHA1")
        cert.sign(ca_key, md)

        try:
            if not exists(dirname(c_f)):
                makedirs(dirname(c_f))
            open(c_f, "wt").write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('utf-8'))
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to write to %s", c_f)
            return

        try:
            if not exists(dirname(k_f)):
                makedirs(dirname(k_f))
            open(k_f, "wt").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode('utf-8'))
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to write to %s", k_f)
            return

        try:
            if not exists(dirname(ca_f)):
                makedirs(dirname(ca_f))
            open(ca_f, "wt").write(crypto.dump_certificate(crypto.FILETYPE_PEM, ca_cert).decode('utf-8'))
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to write to %s", ca_f)
            return

        logger.info("user certificate created in " + c_f)
        logger.info("user private key created in " + k_f)
        logger.info("user CA list (chain of trust) created in " + ca_f)


    def __exclude__(self):
        return not openssl_available
