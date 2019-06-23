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

from random import SystemRandom
import libvirt


# Need to add in some try except logic to handle errors here and
# retun an error via module error logic
def get_vm_list():
    conn = libvirt.openReadOnly("qemu:///system")
    vm_list = list(vm.name() for vm in conn.listAllDomains())
    conn.close()
    return vm_list


def extract_bus_info(bus_address):
    domain, bus, slot_func = bus_address.split(':')
    slot, function = slot_func.split('.')
    return dict(domain=domain, bus=bus, slot=slot, function=function)


def generate_mac_address():
    # generate a /dev/urandom based random number to use when
    # constructing a MAC address.  since we are using the MAC
    # address pattern 52:54:00:XX:YY:ZZ we can safely use all
    # 24 bits in the XX:YY:ZZ part of the address.
    xx_yy_zz = str(hex(SystemRandom().randint(0, 0xffffff))[2:]).zfill(6)
    xx, yy, zz = (xx_yy_zz[0:2], xx_yy_zz[2:4], xx_yy_zz[4:6])

    return ":".join(("52", "54", "00", xx, yy, zz))


def add_mac_addresses(host_info, vm):
    for nbi in vm.get('net_bridge_info', []):
        if 'mac_address' not in nbi:
            nbi['mac_address'] = generate_mac_address()


def process_pci_bus_addresses(vm):
    for nbi in vm.get('net_bridge_info', []):
        if 'bus_address' in nbi:
            bus_info = extract_bus_info(nbi['bus_address'])
            nbi['_bus_info'] = bus_info


def process_vm_entry(host_info, vm):
    process_pci_bus_addresses(vm)
    add_mac_addresses(host_info, vm)
    return vm


def main():
    module = AnsibleModule(  # noqa
        argument_spec=dict(
           host_info=dict(required=True, type="dict")
    ))
    host_info = module.params['host_info']
    vms_info = host_info["my_vms"]
    vms_exist = get_vm_list()
    returned_vms = list(process_vm_entry(host_info, vm)
                        for vm in vms_info
                        if vm['vm'] not in vms_exist)
    module.exit_json(returned_vms=returned_vms, rc=0, changed=0)


from ansible.module_utils.basic import *  # noqa
main()
