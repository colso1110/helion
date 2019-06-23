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
import imp
import logging
import json

from monasca_setup import agent_config
from monasca_setup.detection import Plugin

log = logging.getLogger(__name__)


class Vsa(Plugin):
    """Detect Vsa VMs and setup configuration to monitor them.

    """

    def __init__(self, template_dir, overwrite=True, args=None):
        vsa_specs = self._read_vsa_specs()
        self.vsa_network = vsa_specs.get("vsa_network")
        self.vsa_domain = vsa_specs.get("vsa_domain")
        super(Vsa, self).__init__(template_dir, overwrite, args)

    def _detect(self):
        """Run detection.

        """
        # This hack is done to prevent loading of libvirt.py detection plugin
        # which is in the same logical import level.
        libvirt = imp.load_source(
            'libvirt', '/usr/lib/python2.7/dist-packages/libvirt.py')
        conn = libvirt.openReadOnly('qemu:///system')
        if not conn:
            msg = 'Failed to open connection to the hypervisor'
            log.debug(msg)
        else:
            try:
                conn.lookupByName(self.vsa_domain)
                self.available = True
            except Exception as e:
                msg = 'Failed to find VSA VM domain: %s' % e.message
                log.debug(msg)

    def _watch_vsa_domain(self):
        config = dict()
        parameters = {
            'name': 'vsa',
            'domain': self.vsa_domain,
            'network': self.vsa_network,
            'dimensions': {
                'service': 'vsa',
                'component': 'vsa'
            }
        }
        config['vsa'] = {
            'init_config': None,
            'instances': [parameters]
        }
        return config

    def build_config(self):
        """Build the config as a Plugins object and return.

        """
        config = agent_config.Plugins()
        log.info("\tMonitoring the VSA VM domain: %s" % self.vsa_domain)
        config.merge(self._watch_vsa_domain())
        return config

    def _read_vsa_specs(self, config_file="/etc/vsa/vsa_config.json"):
        log.info("Read VSA config from %s" % config_file)
        try:
            with open(config_file) as file_desc:
                config_data = json.load(file_desc)
                vsa_specs = {}
                vsa_specs["vsa_network"] = config_data["vsa_config"][
                    "network_name"]
                vsa_specs["vsa_domain"] = config_data["vsa_config"]["hostname"]
                log.debug("Config data: %s" % config_data)
                return vsa_specs
        except IOError as e:
            msg = ("Failed to load %s %s" % (config_file, e.message))
            log.error(msg)
