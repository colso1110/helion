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

def main():
    module = AnsibleModule(
        argument_spec=dict(
            blacklist=dict()
        )
    )

    blacklist = json.loads(module.params['blacklist'])

    for entry in blacklist:
        if 'device' in entry.keys():
            if 'product' in entry['device'].keys() and 'vendor' in entry['device'].keys():
                if entry['device']['product'] == ".*" and entry['device']['vendor'] == ".*":
                    module.fail_json(rc=256, msg="No wildcard on blacklist allowed on redhat nodes")


    module.exit_json(
        rc=0,
        changed=False
    )


from ansible.module_utils.basic import *    # NOQA

main()
