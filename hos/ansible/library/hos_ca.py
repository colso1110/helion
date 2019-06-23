#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

# (c) Copyright 2016 Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
from subprocess import check_output, CalledProcessError
import os

def _ca(ca):
    create_ca =[ "/usr/bin/openssl", "req",
                 "-new",
                 "-x509",
                 "-batch",
                 "-nodes",
                 "-key", ca["key"],
                 "-out", ca["cert"],
                 "-days", ca["days"],
                 "-subj", ca["subj"],
               ]

    check_output(create_ca, stderr=subprocess.STDOUT)

def _csr(req, key, csr):
    create_csr =[ "/usr/bin/openssl", "req",
                  "-newkey", "rsa:2048",
                  "-nodes",
                  "-keyout", key,
                  "-out", csr,
                  "-extensions", "v3_req",
                  "-config", req,
                ]

    check_output(create_csr, stderr=subprocess.STDOUT)

def _sign(ca, csr, cert):
    check_output("touch index.txt".split(), stderr=subprocess.STDOUT)
    check_output("/usr/bin/openssl rand -hex -out serial 6".split(),
                    stderr=subprocess.STDOUT)

    cert_sign =[ "/usr/bin/openssl", "ca",
                 "-batch",
                 "-notext",
                 "-in", csr,
                 "-out", cert,
                 "-config", ca["conf"],
                 "-extensions", "v3_req",
                 "-cert", ca["cert"],
                 "-keyfile", ca["key"],
                ]
    check_output(cert_sign, stderr=subprocess.STDOUT)
def main():

    module = AnsibleModule(
        argument_spec = dict(
            cacert            = dict(required=True),
            cakey             = dict(required=True),
            conf              = dict(required=True),
            subj              = dict(required=True),
            cert              = dict(required=False, type='str'),
            ca_days           = dict(required=False, type='str'),
            req               = dict(required=False, type='str'),
            csr               = dict(required=False, type='str'),
            key               = dict(required=False, type='str'),
            chdir             = dict(required=False, type='str'),
            combined          = dict(required=False, type='bool'),
            generate_ca       = dict(required=False, type='bool'),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    # Initialize return values
    changed = False

    # Change to the working directory
    chdir = module.params['chdir']
    if chdir:
        chdir = os.path.abspath(os.path.expanduser(chdir))
        os.chdir(chdir)

    # Get CA credentials first
    cakey = module.params['cakey']
    if not os.path.exists(cakey) or not os.access(cakey, os.R_OK):
        module.fail_json(msg="CA key file %s not found or not readable" % (cakey))

    generate_CA = module.params['generate_ca']

    cacert = module.params['cacert']
    if not os.path.exists(cacert) or not os.access(cacert, os.R_OK):
        generate_CA = True

    ca_days = module.params['ca_days']
    if not ca_days:
        ca_days = "3650" # Ten years

    ca = {"key": cakey,
          "cert": cacert,
          "days": ca_days,
          "conf": module.params['conf'],
          "subj": module.params['subj'],
         }

    # If CA is to be generated do it now
    if generate_CA:
        try:
            _ca(ca)
            changed = True
        except CalledProcessError as err:
            module.fail_json(msg=err.output, exit_status=err.returncode)

    req = module.params['req']
    if req: # User wants a cert generated
        if not os.path.exists(req) or not os.access(req, os.R_OK):
            module.fail_json(msg="Request file %s not found or not readable" % (req))

        csr = module.params['csr']
        if not csr:
            csr = req + ".csr"
        key = module.params['key']
        if not key:
            key = req + ".key"
        cert = module.params['cert']

        # Create CSR and Sign the cert
        try:
            _csr(req, key, csr)
            _sign(ca, csr, cert)
            changed = True
        except CalledProcessError as err:
            module.fail_json(msg=err.output, exit_status=err.returncode)


        combined = module.params['combined']
        if combined:
            with open(cert, "a") as certfile, open(key, "r") as keyfile:
                    certfile.write(keyfile.read())
        changed = True

    module.exit_json(
        changed  = changed,
    )

# import module snippets
from ansible.module_utils.basic import *
main()

