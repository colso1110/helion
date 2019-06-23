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
# Usage 1: Find mount path for LV L2, in VG with Consumer C2, U2
#   {volume_groups:[{name:N1,
#                    logical_volumes:[{name:L1, mount:M1,
#                                      consumer:{name:C1,
#                                                usage:U1}, ...}, ...],
#                   {name:N2,
#                    logical_volumes:[{name:L2, mount:M2,
#                                      consumer:{name:C2,
#                                                usage:U2}, ...}, ...],
#                   ...]} | consumer_lv_mount(C2, U2, L2)
#     => M2
#
# Usage 2: Return provided default when no match found
#   {volume_groups:[{name:N1,
#                    logical_volumes:[{name:L1, mount:M1,
#                                      consumer:{name:C1,
#                                                usage:U1}, ...}, ...],
#                   {name:N2,
#                    logical_volumes:[{name:L2, mount:M2,
#                                      consumer:{name:C2,
#                                                usage:U2}, ...}, ...],
#                   ...]} | consumer_lv_mount(C3, U3, L3, MD)
#     => MD


class TooManyMatchingLogicalVolumes(Exception):
    pass


def consumer_lv_mount(data, lv_consumer, lv_usage, mount_default=None):
    found = []

    # iterate over the lvs for each vg
    for vg in data.get("volume_groups", []):
        for lv in vg.get("logical_volumes", []):

            # skip if doesn't have a consumer entry
            consumer = lv.get("consumer")
            if not consumer:
                continue

            # skip if consumer name or usage don't match specified
            consumer_name = consumer.get("name")
            if not consumer_name or consumer_name != lv_consumer:
                continue
            consumer_usage = consumer.get("usage")
            if not consumer_usage or consumer_usage != lv_usage:
                continue

            # found a matching logical volume
            found.append(lv)

    # fail if we found more than one matching lv
    if len(found) > 1:
        raise TooManyMatchingLogicalVolumes(
                "Found %d matching logical_volumes for (consumer=%s, "
                "usage=%s)" % (len(found), repr(lv_consumer),
                                        repr(lv_usage)))

    # return default if not match found
    if not found:
        return mount_default

    # return found mount point
    return found[0]["mount"]


class FilterModule(object):
    def filters(self):
        return {'consumer_lv_mount': consumer_lv_mount}
