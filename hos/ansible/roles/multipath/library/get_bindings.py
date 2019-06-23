#!/usr/bin/python
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

import os

def main():
    my_bindings=[]
    disks = []

    module = AnsibleModule(
        argument_spec=dict(
            hlm_host_info=dict(required=True)
        )
    )

    hlm_host_info = json.loads(module.params['hlm_host_info'])

    hlm_disk_models = hlm_host_info.get('my_disk_models', dict())
    hlm_device_groups = hlm_host_info.get('my_device_groups', dict())

    if hlm_disk_models:
        for volume_group in hlm_disk_models['volume_groups']:
            for physical_volume in volume_group['physical_volumes']:
                physical_volume = physical_volume.replace('_root', '')
                disks.append(os.path.basename(physical_volume))

    if hlm_device_groups:
        for device_group in hlm_device_groups:
            for entry in hlm_device_groups[device_group]:
                for dev in entry['devices']:
                    disks.append(os.path.basename(dev['name']))

    if not os.path.exists("/etc/multipath/bindings"):
        module.exit_json(
            bindings = my_bindings,
            rc=0,
            changed=False
        )

    try:
        with open("/etc/multipath/bindings") as f:
            bindings = f.readlines()
    except:
       module_fail_json(rc=256, msg="failed to open the binding file")

    for line in bindings:
        stripped = line.strip()
        if stripped.startswith("#") or stripped == "":
            continue
        device, wwid = line.split()
        if device in disks:
            my_bindings.append(dict(alias=device, wwid=wwid))

    module.exit_json(
        bindings = my_bindings,
        rc=0,
        changed=False
    )

from ansible.module_utils.basic import *    # NOQA

main()
