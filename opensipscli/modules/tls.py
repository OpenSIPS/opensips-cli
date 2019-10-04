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
from OpenSSL import crypto, SSL
from socket import gethostname
from pprint import pprint
from time import gmtime, mktime
from os.path import exists, join, dirname
from os import makedirs
from opensipscli.config import cfg, OpenSIPSCLIConfig

class tls(Module):
    def do_rootCA(self, params):
        tlscfg = cfg
        ca_cfg = cfg.get("tls_ca_config")
        if ca_cfg:
            tlscfg = OpenSIPSCLIConfig()
            tlscfg.parse(ca_cfg)

        cn = tlscfg.read_param("tls_ca_common_name", "input the hostname of the website the certificate is for", "www.opensips.com")
        ca_dir = tlscfg.read_param("tls_ca_dir", "ca director", "/etc/opensips/tls/rootCA/")
        cert_file = tlscfg.read_param("tls_ca_cert_file","cert_file", "cacert.pem")
        key_file = tlscfg.read_param("tls_ca_key_file","key_file", "private/cakey.pem")
        c_f = join(ca_dir, cert_file)
        k_f = join(ca_dir, key_file)
        create_cert = False
        if not exists(c_f) or not exists(k_f):
            create_cert = True
        else:
            if tlscfg.read_param("tls_ca_overwrite", "rootCA already exists, do you want to overwrite it?", "yes", True):
                create_cert = True
        if create_cert:
             # create a key pair
            key = crypto.PKey()
            key_size = int(tlscfg.read_param("tls_ca_key_size","key_size", 4096))
            key.generate_key(crypto.TYPE_RSA, key_size)        

            # create a self-signed cert
            cert = crypto.X509() 

            cert.get_subject().C = tlscfg.read_param("tls_ca_country", "country")
            cert.get_subject().ST = tlscfg.read_param("tls_ca_state", "state", "Ilfov")
            cert.get_subject().L = tlscfg.read_param("tls_ca_city", "city", "Bucharest")
            cert.get_subject().O = tlscfg.read_param("tls_ca_organisation", "organization", "opensips")
            cert.get_subject().OU = tlscfg.read_param("tls_ca_organisational_unit", "organisational unit", "project")
            cert.get_subject().CN = cn 
            cert.set_serial_number(1)
            cert.gmtime_adj_notBefore(0)
            notafter = int(tlscfg.read_param("tls_ca_notafter", "duration", 315360000))
            cert.gmtime_adj_notAfter(notafter)
            cert.set_issuer(cert.get_subject())
            cert.set_pubkey(key)
            md = tlscfg.read_param("tls_ca_md", "md", "sha1")
            cert.sign(key, md)

            if not exists(dirname(c_f)):
                makedirs(dirname(c_f))
            try:
                open(c_f, "wt").write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('utf-8'))
            except Exception as e:
                logger.error(e)

            if not exists(dirname(k_f)):
                makedirs(dirname(k_f))
            try:
                open(k_f, "wt").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode('utf-8'))
            except Exception as e:
                logger.error(e)   
            logger.info("CA certificate created in " + c_f)
            logger.info("CA private key created in " + k_f)

    def do_userCERT(self, params):
        tlscfg = cfg
        user_cfg = cfg.get("tls_user_config")
        if user_cfg:
            tlscfg = OpenSIPSCLIConfig()
            tlscfg.parse(user_cfg)

        cn = tlscfg.read_param("tls_user_common_name", "input the hostname of the website the certificate is for", "www.open.ro")
        user_dir = tlscfg.read_param("tls_user_dir", "user director", "/etc/opensips/tls/user/")
        cert_file = tlscfg.read_param("tls_user_cert_file","cert_file", "user-cert.pem")
        key_file = tlscfg.read_param("tls_user_key_file","key_file", "user-privkey.pem")
        calist_file = tlscfg.read_param("tls_user_calist_file","cert_file", "user-calist.pem")
        c_f = join(user_dir, cert_file)
        k_f = join(user_dir, key_file)
        ca_f = join(user_dir, calist_file)
        
        create_cert = False
        if not exists(c_f) or not exists(k_f):
            create_cert = True
        else:
            if tlscfg.read_param("tls_user_overwrite", "user certificate already exists, do you want to overwrite it?", "yes", True):
                create_cert = True
        if create_cert:
            cacert = tlscfg.read_param("tls_user_cacert","cert_file", "/etc/opensips/tls/rootCA/cacert.pem")
            cakey = tlscfg.read_param("tls_user_cakey","key_file", "/etc/opensips/tls/rootCA/private/cakey.pem")
            ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, open(cacert, 'rt').read())
            ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM, open(cakey, 'rt').read())
            
            # create a key pair
            key = crypto.PKey()
            key_size = int(tlscfg.read_param("tls_user_key_size","key_size", 4096))
            key.generate_key(crypto.TYPE_RSA, key_size)
            
            # create a self-signed cert
            cert = crypto.X509()

            cert.get_subject().C = tlscfg.read_param("tls_user_country", "country", "ro")
            cert.get_subject().ST = tlscfg.read_param("tls_user_state", "state", "Braila")
            cert.get_subject().L = tlscfg.read_param("tls_user_city", "city", "Braila")
            cert.get_subject().O = tlscfg.read_param("tls_user_organisation", "organization", "opensips")
            cert.get_subject().OU = tlscfg.read_param("tls_user_organisational_unit", "organisational unit", "project")
            cert.get_subject().CN = cn 
            serial = int(tlscfg.read_param("tls_user_serial", "serial", 2))
            cert.set_serial_number(serial)
            cert.gmtime_adj_notBefore(0)
            notafter = int(tlscfg.read_param("tls_user_notafter", "duration", 315360000))
            cert.gmtime_adj_notAfter(notafter)
            cert.set_issuer(ca_cert.get_subject())
            cert.set_pubkey(key)
            md = tlscfg.read_param("tls_user_md", "md", "sha1")
            cert.sign(ca_key, md)

            if not exists(dirname(c_f)):
                makedirs(dirname(c_f))
            try:
                open(c_f, "wt").write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('utf-8'))
            except Exception as e:
                logger.error(e)   

            if not exists(dirname(k_f)):
                makedirs(dirname(k_f))
            try:
                open(k_f, "wt").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode('utf-8'))
            except Exception as e:
                logger.error(e)   
            
            if not exists(dirname(ca_f)):
                makedirs(dirname(ca_f))
            try:
                open(ca_f, "wt").write(crypto.dump_certificate(crypto.FILETYPE_PEM, ca_cert).decode('utf-8'))
            except Exception as e:
                logger.error(e)   
            logger.info("user certificate created in " + c_f)
            logger.info("user private key created in " + k_f)
            logger.info("user calist(ca chain of trust) created in " + ca_f)
