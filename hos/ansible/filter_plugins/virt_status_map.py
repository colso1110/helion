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
# Jinja2 filter to extract vm status map from virt status command output
#
# { results: [ {item: {vm: N1, ...}, status: S1, ...},
#              {item: {vm: N2, ...}, status: S2, ...},
#              ... ] } | virt_status_map ==> {N1: S1, N2: S2, ...}


def virt_status_map(data):
    status_map = {}
    # expect to be provided with a result object containing a results list
    for entry in data.get('results', []):
        # only care about entries that have a status field
        if 'status' in entry:
            status_map[entry['item']['vm']] = entry['status']
    return status_map


class FilterModule(object):

    def filters(self):
        return {
            'virt_status_map': virt_status_map,
        }
