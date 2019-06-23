#!/usr/bin/env python
#
# An Ansible module to check if the disk is partitioned.
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

import os


DOCUMENTATION = '''
---
module: check_partition_exist
version_added: "1.0"
short_description: Check if the partition exists in the given disk
disk=osd-data-disk to be checked for partition(s)
data_disks=list of existing Ceph data disks on the OSD node
'''


EXAMPLES = '''
- check_partition_exist:
    disk: /dev/sde
    data_disks: ['/dev/sdc', '/dev/sdd']
'''


def check_partition_exist(disk):
    '''
    Check whether data disk is partitioned or not.
    :param disk: device to be checked if partitioned
    :return: 0 if the disk is partitioned else 1.
    '''
    command = ('partprobe -d -s %s | grep "[0-9]\|gpt"' % disk)
    rc = os.system(command)
    return rc


def main():
    module = AnsibleModule(
        argument_spec=dict(
            disk=dict(required=True),
            data_disks=dict(required=True),
        ),
        supports_check_mode=False
    )

    try:
        params = module.params
        matches = filter(lambda x: params['disk'] in x, params['data_disks'])
        retval = 0 if len(matches) > 0 else 1
        if retval == 0:
            module.exit_json(**dict(changed=False, result=retval))
        else:
            retval = check_partition_exist(params['disk'])
            if retval == 0:
                module.fail_json(msg='Abort: Device %s is ALREADY partitioned'
                                 % params['disk'])
    except Exception, e:
        module.fail_json(msg='Exception: %s' % e)
    else:
        module.exit_json(**dict(changed=True, result=retval))


# import module snippets
from ansible.module_utils.basic import *  # noqa
if __name__ == '__main__':
    main()
