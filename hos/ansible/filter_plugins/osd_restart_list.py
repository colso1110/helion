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


def osd_restart_list(osd_start_result, osd_configure_result=None):
    if not osd_configure_result:
        return osd_start_result

    osd_configure_changed = [int(item['result']['osd_number']) for item in
                             osd_configure_result['results'] if 'result'
                             in item and item['result']]
    if not osd_configure_changed:
        return osd_start_result

    for item in osd_start_result:
        if item['item'] in osd_configure_changed:
            item.update(({"changed": True}))
    return osd_start_result


class FilterModule(object):
    def filters(self):
        return {'osd_restart_list': osd_restart_list}
