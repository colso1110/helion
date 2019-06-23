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
from glob import glob
import imp
import json
import logging
import os

from monasca_setup import agent_config
from monasca_setup.detection import Plugin

log = logging.getLogger(__name__)


class _HLMHypervisorConfig(object):

    def __init__(self, conf_base="/etc/hlm-hypervisor"):
        self._conf_base = conf_base
        self._vm_confs = None

    @property
    def conf_base(self):
        return self._conf_base

    @property
    def vms_conf_dir(self):
        return os.path.join(self.conf_base, "vms")

    def _read_vm_confs(self):
        self._vm_confs = []

        log.info("Read HLM Hypervisor VM configs from '%s'" %
                 self.vms_conf_dir)
        if os.path.exists(self.vms_conf_dir):
            for vm_file in glob(os.path.join(self.vms_conf_dir, "*.json")):
                try:
                    log.debug("Reading VM config '%s'" % vm_file)
                    with open(vm_file) as fp:
                        hvc = json.load(fp)
                    log.debug("Found VM: %s" % hvc['hhv_vm_config'])

                    self._vm_confs.append(hvc['hhv_vm_config'])

                except IOError as e:
                    msg = ("Failed to load '%s': %s" % (vm_file, e.message))
                    log.error(msg)

    @property
    def vm_confs(self):
        if self._vm_confs is None:
            self._read_vm_confs()

        return tuple(self._vm_confs)


class _HLMHypervisorBase(Plugin):
    """Plugin base class used to monitor HLM Hypervisor node status.

    """
    def __init__(self, template_dir, overwrite=True, args=None):
        self._hhv_config = _HLMHypervisorConfig()
        super(_HLMHypervisorBase, self).__init__(template_dir, overwrite, args)

    @property
    def hhv_config(self):
        return self._hhv_config

    @property
    def hhv_vms(self):
        return self._hhv_config.vm_confs

    @property
    def hhv_domains(self):
        return [vm['domain'] for vm in self.hhv_vms]

    @staticmethod
    def _get_connection(uri='qemu:///system'):
        # This hack is done to prevent loading of libvirt.py detection plugin
        # which is in the same logical import level.
        libvirt = imp.load_source(
            'libvirt', '/usr/lib/python2.7/dist-packages/libvirt.py')
        connection = libvirt.openReadOnly(uri)
        if not connection:
            msg = 'Failed to open connection to the hypervisor'
            log.debug(msg)

        return connection

    def _detect(self):
        """Run detection.

        """
        # if no vms to monitor do nothing
        hhv_domains = set(self.hhv_domains)
        if not hhv_domains:
            return

        conn = self._get_connection()
        if conn:
            try:
                domains = set(d.name() for d in conn.listAllDomains())
            except Exception as e:
                domains = set()
                msg = 'Failed to find HLM Hypervisor VM domain: %s' % e.message
                log.debug(msg)

        # if any of the monitored vms are running, we are available
        running = domains.intersection(set(hhv_domains))
        if running:
            msg = "Running domains: %s" % ", ".join(sorted(running))
            log.debug(msg)
            self.available = True

    @property
    def hhv_monitoring_config(self):
        raise NotImplemented

    def build_config(self):
        """Build the config as a Plugins object and return.

        """
        config = agent_config.Plugins()
        config.merge(self.hhv_monitoring_config)
        return config


class HLMHypervisorSummary(_HLMHypervisorBase):
    """Detect HLM Hypervisor VMs and setup configuration to monitor
       overall state of the HLM Hypervisor node.

    """
    @property
    def hhv_monitoring_config(self):
        instances = [dict(name="hlm-hypervisor",
                          domains=[dict(domain=vm['domain'],
                                        networks=vm['networks'])
                                   for vm in self.hhv_vms],
                          dimensions=dict(service="hlm-hypervisor",
                                          component="vcp"),
                          check_type="summary")]
        config = dict(hhv=dict(init_config=None, instances=instances))

        log.info("\tMonitoring overall status of HLM Hypervisor")

        return config


class HLMHypervisorVMs(_HLMHypervisorBase):
    """Detect HLM Hypervisor VMs and setup configuration to monitor them
       and their associated networks on an individual basis.

    """
    @property
    def hhv_monitoring_config(self):
        instances = [dict(inst) for inst in self.hhv_vms]
        config = dict(hhv=dict(init_config=None, instances=instances))

        log.info("\tMonitoring these HLM Hypervisor VMs: %s" %
                 ", ".join(self.hhv_domains))

        return config
