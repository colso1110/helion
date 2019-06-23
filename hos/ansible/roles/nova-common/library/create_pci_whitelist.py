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

from ansible.module_utils.basic import * # noqa

import json
import yaml

DOCUMENTATION = '''
---
module: create-pci-whitelist
short_description: Create SRIOV and PCI whitelist
description: Create SRIOV and PCI whitelist
author: Praveen Kumar SM <praveen-sm.kumar@hpe.com>
requirements: [ ]
options:
    args:
        required: true
        description:
            - A string containing arguments passed to the create sriov and
              pci whitelist
'''

EXAMPLES = '''
tasks:
    - name: Create PCI Whitelist
      create_pci_whitelist: args="{{ network_pci_pt_sriov_interfaces }}"

      The structure of network_pci_pt_sriov_interfaces is below:

          [
            {
              "bus_address": "0000:15:00",
              "device": "hed15",
              "nic_device_type": {
                "device_id": "1008",
                "family": "MT-27500",
                "name": "544M",
                "vendor_id": "15b3"
              },
              "pf_mode": "pci-passthrough",
              "tags": [
                {
                  "component": "neutron-openvswitch-agent",
                  "data_values": {
                    "provider-physical-network": "physnet5",
                    "tenant-vlan-id-range": "50:59"
                  },
                  "service": "neutron",
                  "tag": "neutron.networks.vlan"
                }
              ],
              "vf_count": "4"
            }, ...
          ]

      This will produce output (sans single-quotes) like:

          ' {"devname": "hed15", "physical_network": "physnet5"},'
          '{"physical_network": "physnet5", "address": "*:15:00"}'

      The leading space is to work around:

          https://github.com/ansible/ansible/issues/10864
'''


def main():
    module = AnsibleModule( # noqa
        argument_spec={'args': {'required': True, 'type': 'str'}},
        supports_check_mode=True)

    lines = []
    for pci_dict in yaml.load(module.params['args']):
        phys_net = ''
        for tag_dict in pci_dict.get('tags', []):
            if (tag_dict.get('tag') in ['neutron.networks.flat',
                                        'neutron.networks.vlan']):
                phys_net = (tag_dict.get('data_values', {})
                            .get('provider-physical-network', phys_net))

        pf_mode = pci_dict.get('pf_mode')
        if (pf_mode in ['normal', 'sriov-only', 'pci-passthrough']
                and pci_dict.get('vf_count', 0) > 0):
            lines.append(json.dumps({
                "devname": pci_dict.get('device'),
                "physical_network": phys_net}))
        if pf_mode in ['pci-passthrough']:
            bus_addr = pci_dict.get('bus_address')
            lines.append(json.dumps({
                "address": "*:" + bus_addr[bus_addr.index(':') + 1:],
                "physical_network": phys_net}))
    combined = ' ' + ",".join(lines)
    module.exit_json(cmd='args', stdout=combined)


if __name__ == "__main__":
    main()
