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

import json
import re


def journal_disk_validate(ip_journal_disks, blk_device_info, journal_disk_size,
                          existing_journal_disks):
    existing_journal_disks = json.loads(existing_journal_disks)
    unique_disks = set(ip_journal_disks)
    unique_disks.discard(None)

    # create a dict of format (where are sizes are in bytes):
    # disk : {'size' = total disk size, 'part_size' = existing partitions' size
    # 'part_count': # of existing disk partitions
    # 'ceph_part_count': # of existing ceph partition on disk
    # 'exp_ceph_part_count': # of expected ceph partitions on disk
    journal_stats = dict((disk, {'size': 0, 'part_size': 0, 'part_count': 0,
                                 'ceph_part_count': 0, 'exp_ceph_part_count':
                                 ip_journal_disks.count(disk)})
                         for disk in unique_disks)

    blk_regex = 'NAME=\"(.*)\" SIZE=\"(.*)\" TYPE=\"(.*)\"'
    re_c = re.compile(blk_regex)
    for device_info in blk_device_info:
        result = re_c.search(device_info)
        if result:
            device_name = None
            name, size, type = result.groups()
            if type == 'disk':
                device_name = name
            elif type == 'part':
                # name can be: sdc1 or sdc10, ignore the partition number
                part_regex = re.search('(\d+)', name)
                if part_regex:
                    index = len(part_regex.groups()[0])
                    device_name = name if type == 'disk' else name[:-index]
            if not device_name:
                # only consider disks or partition type block devices.
                continue

            # check if block device is specified as OSD journal disk
            # full_name will be like: /dev/sdc
            full_name = filter(lambda x: device_name in x,
                               journal_stats.keys())
            if full_name:
                full_name = full_name[0]
                if type == 'disk':
                    journal_stats[full_name]['size'] = int(size)
                else:
                    journal_stats[full_name]['part_size'] += int(size)
                    journal_stats[full_name]['part_count'] += 1
                    matches = filter(lambda x: name in x,
                                     existing_journal_disks)
                    if len(matches) > 0:
                        journal_stats[full_name]['ceph_part_count'] += 1

    unit_gb = 1024 * 1024 * 1024

    for disk, info in journal_stats.iteritems():
        # determine how many new journal partitions are to be created.
        new_partitions = info['exp_ceph_part_count'] - info['ceph_part_count']

        # calculate required_size = no. of new partitions * current journal
        # size.
        required_free_size_gb = new_partitions * journal_disk_size/float(1024)
        available_free_size = float(info['size'] - info['part_size'])
        available_free_size_gb = round(available_free_size/unit_gb, 2)
        if required_free_size_gb > available_free_size_gb:
            return ("Journal disk %s does not have the capacity to support "
                    "requested OSDs (minimum expected free size %s GiB, "
                    "actual free size %s GiB)." %
                    (disk, round(required_free_size_gb, 2),
                     available_free_size_gb))
    return True


class FilterModule(object):
    def filters(self):
        return {'journal_disk_validate': journal_disk_validate}
