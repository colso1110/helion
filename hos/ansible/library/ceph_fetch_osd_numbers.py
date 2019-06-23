#!/usr/bin/env python
#
# An Ansible module to fetch osd numbers.
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

import os
import json
import signal
import subprocess
from threading import Timer


DOCUMENTATION = '''
---
module: ceph_fetch_osd_numbers
version_added: "1.0"
short_description: Fetch the OSD numbers on the given host
hostname=osd-host-name
cluster_name=ceph
timeout=timeout the module operation after specified number of seconds
    required: false
    default: 30
'''


EXAMPLES = '''
- ceph_fetch_osd_numbers:
    hostname: osd-1
    cluster_name: ceph
    timeout: 30
'''


def kill_procgroup(proc):
    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)


def get_osd_numbers(module, hostname, cluster_name, timeout):
    '''
    Returns list of osd number.
    :param module: current module instance
    :param hostname: host on which module is being run on
    :param cluster_name: name of the Ceph cluster
    :param timeout: timeout the operation after specified number of seconds
    :return: list of osd numbers
    '''
    cmd = ('ceph --cluster %s osd tree -f json' % (cluster_name))
    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                         preexec_fn=os.setsid)
    t = Timer(timeout, kill_procgroup, [p])
    t.start()
    output, err = p.communicate()
    if t.is_alive():
        t.cancel()
    else:
        error_msg = "Timeout on cmd %s output %s" % (cmd, output)
        module.fail_json(msg=error_msg)

    if p.returncode != 0:
        error_msg = "Failed to run %s" % (cmd)
        module.fail_json(msg=error_msg)

    output = json.loads(output)
    osd_numbers = []
    if output and 'nodes' in output:
        for entity in output['nodes']:
            if entity['type'] == 'host' and entity['name'] == hostname:
                osd_numbers = entity['children'][:]
    return osd_numbers


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(required=True),
            cluster_name=dict(required=True),
            timeout=dict(required=False, type='int', default=30)
        ),
        supports_check_mode=False
    )

    try:
        params = module.params
        retval = get_osd_numbers(module,
                                 params['hostname'],
                                 params['cluster_name'],
                                 params['timeout'])
    except Exception, e:
        module.fail_json(msg='Exception: %s' % e)
    else:
        module.exit_json(**dict(changed=True, result=retval))


# import module snippets
from ansible.module_utils.basic import *  # noqa
if __name__ == '__main__':
    main()
