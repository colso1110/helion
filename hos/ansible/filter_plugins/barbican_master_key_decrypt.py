#
# (c) Copyright 2015-2016 Hewlett Packard Enterprise Development LP
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

import base64
import os.path
import imp

path = os.path.dirname(os.path.realpath(__file__))

hosencrypt = imp.load_source('hosencrypt', path + '/../hosencrypt.py')

encryption_class = 'openssl'

hosencrypt_class = getattr(hosencrypt, encryption_class)

# Method to decypt the Customer defined encrypted key
# It will only decrypt the key with prefix @hos@
# Customer define this key, barbican_customer_master_key, in
# roles/barbican-common/vars/barbican_deploy_config.yml
def barbican_master_key_decrypt(value, *args, **kw):
    if not value.startswith(hosencrypt_class.prefix):
        return value
    obj = hosencrypt_class()
    return obj.decrypt(base64.urlsafe_b64decode(value.encode('ascii', 'ignore')[len(obj.prefix):]))


class FilterModule(object):
    def filters(self):
        return { 'barbican_master_key_decrypt': barbican_master_key_decrypt }
