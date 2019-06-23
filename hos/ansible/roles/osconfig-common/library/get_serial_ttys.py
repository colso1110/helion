#!/usr/bin/python
#
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

import os
import subprocess

def main():
   module = AnsibleModule(
       argument_spec=dict(
           dev_ins=dict(required=True)
       )
   )

   devices = module.params['dev_ins']

   ret_list=[]

   for device in devices:
       devpath = "/dev/tty" + device

       if not os.path.exists(devpath):
           return None

       try:
           fd = os.open(devpath, os.O_RDONLY)
       except Exception as e:
           module.fail_json(msg = "Failed to open device %s, %s" % (devpath, str(e)))

       if os.isatty(fd):
          ret_list.append(device)

   module.exit_json(
       dev_outs=ret_list,
       changed=True
   )

from ansible.module_utils.basic import *    # NOQA

main()
