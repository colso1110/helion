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

# This file will be called by hlm_udev_run.sh to configure or remove VF's
# based on the interface removed/added/updated.

import os
import sys
import syslog
import yaml

SUCCESS = 0
FAILURE = 1
SKIPPED = 2


class udev_pci_request(object):

    def __init__(self, devpath):
        self._device_name = None
        self._device_address = None
        # Parse the devpath
        if devpath:
            path_parts = devpath.split("/")
            self._device_name = path_parts[6] \
                                if len(path_parts) >= 7 else None
            self._device_address = path_parts[4] \
                                   if len(path_parts) >= 5 else None

    @property
    def device_name(self):
        return self._device_name

    @property
    def device_address(self):
        return self._device_address


class network_pci_database(object):

    UDEV_DIR = '/etc/udev'
    DB_FILE = UDEV_DIR + '/network-pci.yml'

    def __init__(self):
        # Construct the DB map
        self._nic_device_map = {}
        # Scan db file and create device map
        self._load_devices()

    def _read_db(self, db_file):
        data = {}
        try:
            if os.path.isfile(db_file):
                with open(db_file, 'r') as _db_file:
                    data = yaml.load(_db_file)
                    if data is None:
                        data = {}
        except Exception:
            # Log message, do not fail UDEV
            syslog.syslog(syslog.LOG_ERR, '%s not found' % 'db_file')
        return data

    def _load_devices(self):
        # Read the db files and store in respective device map
        data = self._read_db(self.DB_FILE)
        # Making sure that the key 'pci_entries' exists
        # and its respective values are not empty
        if data.get('pci_entries', None):
            # Form device list from raw data
            device_list = [{item.pop('device'): item}
                           for item in data.get('pci_entries')]
            self._nic_device_map = {item.keys()[0]: item.get(item.keys()[0])
                                    for item in device_list}

    def _set_device_up(self, device_name):
        # Execute ip link show command to find out the interface is up/down
        command = "ip link show %s | awk 'NR==1{print $9; exit}'"\
                  % device_name
        output = os.popen(command).read().rstrip()
        # If interface is down, make it up
        if output == 'DOWN':
            cmd = "ip link set %s up" % device_name
            return os.system(cmd)
        else:
            # Interface is already up skip it
            return SKIPPED

    def config_VFs(self, request, device):
        # Calls the device specific script to configure VFs
        # Form the command and arguments
        command = os.path.join(self.UDEV_DIR, device['config_script'])
        args = "%s %s %s configure %s %s" \
               % (device['distro'], request.device_name,
                  str(device['vf_count']), device['bus_address'],
                  str(device['port_num']))
        # VFs on system device get configured with the value in the database
        result1 = os.system("%s %s" % (command, args))
        # Make the device up if it is down
        if result1 != FAILURE:
            result2 = self._set_device_up(request.device_name)
            if result2 != FAILURE:
                return SUCCESS
        syslog.syslog(syslog.LOG_ERR,
                      'Configuring device with address %s failed'
                      % request.device_address)
        return FAILURE

# This python script requires an command line argument which
# is the form of "/devices/pci0000:00/0000:00:02.0/0000:05:00.0/net/hed1"
# where "0000:05:00.0" represents the address and "hed1"
# represents the device name.
#
# It also has dependency on the db file named
# 'network-pci.yml' which contains the
# device details in the following yaml format
# pci_entries:
#   - 'device': 'hed1'
#     'config_script': '8086_10fb.sh'
#     'vf_count': '10'
#     'bus_address': '0000:05:00.0'
#     'port_num': '0'
#     'device_id': '10fb'
#     'distro': 'Debian'


def main():
    # A valid device create request
    request = udev_pci_request(sys.argv[1])
    pci_db = network_pci_database()
    name = request.device_name
    if name and name in pci_db._nic_device_map:
        # Configure the VF setting for this device
        return pci_db.config_VFs(request,
                                 pci_db._nic_device_map.get(name))
    syslog.syslog(syslog.LOG_ERR,
                  'Unknown device: %s, VFs not configured' % name)
    return FAILURE

main()
