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
# return kernel boot arguments for given fcoe interface

from ansible.errors import AnsibleFilterError


def fcoe_boot_args(host_info, iface):
    ret = ""

    iface_entry = 'ansible_%s' % iface

    iface_info = host_info.get(iface_entry)
    if iface_info is None:
        raise AnsibleFilterError("Interface not found: '%s'" % iface)

    iface_mac = iface_info.get('macaddress')
    if iface_mac is None:
        raise AnsibleFilterError("No MAC address available for interface: "
                                 "'%s'" % iface)

    return "fcoe=%s:nodcb iface=%s:%s" % (iface, iface, iface_mac)

class FilterModule(object):

    def filters(self):
        return {
            'fcoe_boot_args': fcoe_boot_args,
        }
