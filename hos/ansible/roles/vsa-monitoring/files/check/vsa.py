#!/usr/bin/python
#
# (c) Copyright 2015 Hewlett Packard Enterprise Development LP
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

import monasca_agent.collector.checks as checks

log = logging.getLogger(__name__)


class Vsa(checks.AgentCheck):

    @staticmethod
    def _get_connection():
        # This hack is done to prevent loading of libvirt.py detection plugin
        # which is in the same logical import level.
        libvirt = imp.load_source(
            'libvirt', '/usr/lib/python2.7/dist-packages/libvirt.py')
        connection = libvirt.openReadOnly('qemu:///system')
        if not connection:
            msg = 'Failed to open connection to the hypervisor'
            log.debug(msg)
            return None
        return connection

    @staticmethod
    def _check_domain_is_active(connection, domain):
        try:
            dom = connection.lookupByName(domain)
            dom_status = dom.info()[0]             # First attibute is vm state
            if dom_status == 1:                    # '1' represents 'running'
                return 0                           # Return '0' if active
        except Exception as e:
            msg = 'Failed to find VSA VM domain: %s' % e.message
            log.debug(msg)
        return 1                                   # Return '1' if inactive

    @staticmethod
    def _check_network_is_active(connection, network):
        try:
            net = connection.networkLookupByName(network)
            if net.isActive():
                return 0                           # Return '0' if active
        except Exception as e:
            msg = 'Failed to find VSA VM network: %s' % e.message
            log.debug(msg)
        return 1                                   # Return '1' if inactive

    @staticmethod
    def _build_msg(entity, status):
        msg = "The %s is down" % entity
        if not status:
            msg = "The %s is active" % entity
        return msg

    def _build_metrics(self, instance):
        connection = self._get_connection()
        vsa_metrics = [
            {
                "name": "vsa_vm_status",
                "entity": instance.get('domain', None),
                "status": self._check_domain_is_active(
                    connection, instance.get('domain', None)),
            },
            {
                "name": "vsa_vm_net_status",
                "entity": "VM Network",
                "status": self._check_network_is_active(
                    connection, instance.get('network', None)),
            }
        ]
        for metric in vsa_metrics:
            metric['message'] = self._build_msg(metric['entity'],
                                                metric['status'])

        return vsa_metrics

    def check(self, instance):
        dimensions = self._set_dimensions(None, instance)
        try:
            metrics = self._build_metrics(instance)
            for metric in metrics:
                self.gauge(metric['name'],
                           metric['status'],
                           dimensions=dimensions,
                           value_meta={'message': metric['message']})

        except Exception as e:
            log.error('Error in performing check - %s' % e.message)
