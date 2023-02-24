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

openssl_version = None

try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    import datetime
    openssl_version = 'cryptography'
except ImportError:
    logger.info("cryptography library not available!")
    try:
        from OpenSSL import crypto, SSL
        openssl_version = 'openssl'
    except (TypeError, ImportError):
        logger.info("OpenSSL library not available!")

class tlsCert:

    def __init__(self, prefix, cfg=None):

        if not cfg:
            self.load(prefix)
            return
        self.CN = cfg.read_param("tls_"+prefix+"_common_name", "Website address (CN)", "opensips.org")
        self.C = cfg.read_param("tls_"+prefix+"_country", "Country (C)", "RO")
        self.ST = cfg.read_param("tls_"+prefix+"_state", "State (ST)", "Bucharest")
        self.L = cfg.read_param("tls_"+prefix+"_locality", "Locality (L)", "Bucharest")
        self.O = cfg.read_param("tls_"+prefix+"_organisation", "Organization (O)", "OpenSIPS")
        self.OU = cfg.read_param("tls_"+prefix+"_organisational_unit", "Organisational Unit (OU)", "Project")
        self.notafter = int(cfg.read_param("tls_"+prefix+"_notafter", "Certificate validity (seconds)", 315360000))
        self.md = cfg.read_param("tls_"+prefix+"_md", "Digest Algorithm", "SHA256")

class tlsKey:

    def __init__(self, prefix, cfg=None):

        if not cfg:
            self.load(prefix)
            return
        self.key_size = int(cfg.read_param("tls_"+prefix+"_key_size", "RSA key size (bits)", 4096))


class tlsOpenSSLCert(tlsCert):

    def __init__(self, prefix, cfg=None):
        super().__init__(prefix, cfg)
        if not cfg:
            return
        cert = crypto.X509()
        cert.set_version(2)
        cert.get_subject().CN = self.CN
        cert.get_subject().C = self.C
        cert.get_subject().ST = self.ST
        cert.get_subject().L = self.L
        cert.get_subject().O = self.O
        cert.get_subject().OU = self.OU
        cert.set_serial_number(randrange(100000))
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(self.notafter)

        extensions = [
            crypto.X509Extension(b'basicConstraints', False, b'CA:TRUE'),
            crypto.X509Extension(b'extendedKeyUsage', False, b'clientAuth,serverAuth')
        ]

        cert.add_extensions(extensions)

        self.cert = cert

    def load(self, cacert):
        self.cert = crypto.load_certificate(crypto.FILETYPE_PEM, open(cacert, 'rt').read())

    def sign(self, key):
        self.cert.set_pubkey(key)
        self.cert.sign(key.key, self.md)

    def set_issuer(self, issuer):
        self.cert.set_issuer(issuer)

    def get_subject(self):
        return self.cert.get_subject()

    def dump(self):
        return crypto.dump_certificate(crypto.FILETYPE_PEM, self.cert).decode('utf-8')

class tlsCryptographyCert(tlsCert):

    def __init__(self, prefix, cfg=None):
        super().__init__(prefix, cfg)
        if not cfg:
            return
        builder = x509.CertificateBuilder()
        builder = builder.subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, self.CN),
            x509.NameAttribute(NameOID.COUNTRY_NAME, self.C),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, self.ST),
            x509.NameAttribute(NameOID.LOCALITY_NAME, self.L),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, self.O),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, self.OU),
        ]))
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.not_valid_before(datetime.datetime.today() -
                                          datetime.timedelta(1))
        builder = builder.not_valid_after(datetime.datetime.today() +
                                          datetime.timedelta(0, self.notafter))
        builder = builder.add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=False
        )
        builder = builder.add_extension(
                x509.ExtendedKeyUsage([
                    x509.ExtendedKeyUsageOID.CLIENT_AUTH,
                    x509.ExtendedKeyUsageOID.SERVER_AUTH]),
                critical=False
        )
        self.builder = builder
        self.cert = None

    def load(self, cacert):
        self.cert = x509.load_pem_x509_certificate(open(cacert, 'rb').read())

    def sign(self, key):
        self.builder = self.builder.public_key(key.key.public_key())
        self.cert = self.builder.sign(private_key = key.key,
                                      algorithm=getattr(hashes, self.md)(),
                                      backend=default_backend())

    def set_issuer(self, issuer):
        self.builder = self.builder.issuer_name(issuer)

    def get_subject(self):
        if self.cert:
            return self.cert.subject
        return self.builder._subject_name

    def dump(self):
        return self.cert.public_bytes(encoding=serialization.Encoding.PEM).decode('utf-8')


class tlsOpenSSLKey(tlsKey):

    def __init__(self, prefix, cfg=None):
        super().__init__(prefix, cfg)
        if not cfg:
            return
        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, self.key_size)
        self.key = key

    def dump(self):
        return crypto.dump_privatekey(crypto.FILETYPE_PEM, self.key).decode('utf-8')

    def load(self, key):
        self.key = crypto.load_privatekey(crypto.FILETYPE_PEM, open(key, 'rt').read())

class tlsCryptographyKey(tlsKey):

    def __init__(self, prefix, cfg=None):
        super().__init__(prefix, cfg)
        if not cfg:
            return
        self.key = rsa.generate_private_key(
                key_size=self.key_size,
                public_exponent=65537,
                backend=default_backend()
        )

    def dump(self):
        return self.key.private_bytes(encoding=serialization.Encoding.PEM,
                                      format=serialization.PrivateFormat.TraditionalOpenSSL,
                                      encryption_algorithm=serialization.NoEncryption()
                                      ).decode('utf-8')

    def load(self, key):
        self.key = serialization.load_pem_private_key(open(key, 'rb').read(),
                                                      password=None)

class tls(Module):
    def do_rootCA(self, params, modifiers=None):
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

        if openssl_version == 'openssl':
            cert = tlsOpenSSLCert("ca", cfg)
            key = tlsOpenSSLKey("ca", cfg)
        else:
            cert = tlsCryptographyCert("ca", cfg)
            key = tlsCryptographyKey("ca", cfg)

        cert.set_issuer(cert.get_subject())
        cert.sign(key)

        try:
            if not exists(dirname(c_f)):
                makedirs(dirname(c_f))
            open(c_f, "wt").write(cert.dump())
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to write to %s", c_f)
            return

        try:
            if not exists(dirname(k_f)):
                makedirs(dirname(k_f))
            open(k_f, "wt").write(key.dump())
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to write to %s", k_f)
            return

        logger.info("CA certificate created in " + c_f)
        logger.info("CA private key created in " + k_f)

    def do_userCERT(self, params, modifiers=None):
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
            if openssl_version == 'openssl':
                ca_cert = tlsOpenSSLCert(cacert)
            else:
                ca_cert = tlsCryptographyCert(cacert)
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to load %s", cacert)
            return

        try:
            if openssl_version == 'openssl':
                ca_key = tlsOpenSSLLey(cakey)
            else:
                ca_key = tlsCryptographyKey(cakey)
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to load %s", cakey)
            return

        # create a self-signed cert
        if openssl_version == 'openssl':
            cert = tlsOpenSSLCert("user", cfg)
            key = tlsOpenSSLKey("user", cfg)
        else:
            cert = tlsCryptographyCert("user", cfg)
            key = tlsCryptographyKey("user", cfg)

        cert.set_issuer(ca_cert.get_subject())
        cert.sign(ca_key)
        try:
            if not exists(dirname(c_f)):
                makedirs(dirname(c_f))
            open(c_f, "wt").write(cert.dump())
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to write to %s", c_f)
            return

        try:
            if not exists(dirname(k_f)):
                makedirs(dirname(k_f))
            open(k_f, "wt").write(key.dump())
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to write to %s", k_f)
            return

        try:
            if not exists(dirname(ca_f)):
                makedirs(dirname(ca_f))
            open(ca_f, "wt").write(ca_cert.dump())
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to write to %s", ca_f)
            return

        logger.info("user certificate created in " + c_f)
        logger.info("user private key created in " + k_f)
        logger.info("user CA list (chain of trust) created in " + ca_f)


    def __exclude__(self):
        return (not openssl_version, None)
