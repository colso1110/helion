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
# return list of devices that are ttys

import os
import subprocess
from ansible import errors


def isatty(devices):

   ret_list=[]

   for device in devices:
       devpath = "/dev/tty" + device

       if not os.path.exists(devpath):
           return None

       try:
           output = subprocess.check_output(['/sbin/udevadm', 'info', '-x', devpath])
       except Exception as e:
           raise errors.AnsibleFilterError("Failed to open device %s, %s" % (devpath, str(e)))

       if "/devices/pnp" in output:
          ret_list.append(device)

   return ret_list

class FilterModule(object):

    def filters(self):
        return {
            'isatty': isatty,
        }
