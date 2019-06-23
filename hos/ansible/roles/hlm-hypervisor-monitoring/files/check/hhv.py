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
import imp
import logging

from monasca_agent.collector.checks import AgentCheck

log = logging.getLogger(__name__)


class _HHVLibvirtHelper(object):

    _import = {
        'name': 'libvirt',
        'path': '/usr/lib/python2.7/dist-packages/libvirt.py'
    }

    def __init__(self, uri='qemu:///system'):
        self._uri = uri
        self._libvirt = None
        self._domain_states = None
        self._conn = None
        self._all_vms = None
        self._all_vnets = None

    @property
    def uri(self):
        return self._uri

    @property
    def libvirt(self):
        if self._libvirt is None:
            # This hack is done to prevent loading of libvirt.py detection
            # plugin which is in the same logical import level.
            self._libvirt = imp.load_source(self._import['name'],
                                            self._import['path'])

        return self._libvirt

    def _load_domain_states(self):
        l = self.libvirt
        self._domain_states = {
            l.VIR_DOMAIN_NOSTATE: 'VM has no state',
            l.VIR_DOMAIN_RUNNING: 'VM is running',
            l.VIR_DOMAIN_BLOCKED: 'VM is blocked on a resource',
            l.VIR_DOMAIN_PAUSED: 'VM is paused',
            l.VIR_DOMAIN_SHUTDOWN: 'VM is being shutdown',
            l.VIR_DOMAIN_SHUTOFF: 'VM is being shutoff',
            l.VIR_DOMAIN_CRASHED: 'VM is crashed',
            l.VIR_DOMAIN_PMSUSPENDED: ('VM is suspended by guest power '
                                       'management')
        }

        # Warn if HHV's libvirt supports additional domain states
        if ((l.VIR_DOMAIN_PMSUSPENDED + 1) < l.VIR_DOMAIN_LAST):
            log.warning("HHV Libvirt supports additional domain states")

    @property
    def domain_states(self):
        if self._domain_states is None:
            self._load_domain_states()

        return dict(self._domain_states)

    def _get_connection(self, uri='qemu:///system'):
        connection = self.libvirt.openReadOnly(uri)
        if not connection:
            msg = 'Failed to open connection to the hypervisor'
            log.debug(msg)
            return None

        return connection

    @property
    def conn(self):
        if self._conn is None:
            self._conn = self._get_connection(self.uri)

        return self._conn

    @property
    def all_vms(self):
        if self._all_vms is None:
            self._all_vms = self.conn.listAllDomains()

        return self._all_vms

    @property
    def all_vm_names(self):
        return [v.name() for v in self.all_vms]

    @property
    def active_vm_names(self):
        return [v.name() for v in self.all_vms if v.isActive()]

    @property
    def all_vnets(self):
        if self._all_vnets is None:
            self._all_vnets = self.conn.listAllNetworks()

        return self._all_vnets

    @property
    def all_vnet_names(self):
        return [n.name() for n in self.all_vnets]

    @property
    def active_vnet_names(self):
        return [n.name() for n in self.all_vnets if n.isActive()]


class _HLMHypervisorBase(AgentCheck):

    @staticmethod
    def _hhv_vm_state(hlh, vm):
        if vm not in hlh.all_vm_names:
            return "missing"

        if vm not in hlh.active_vm_names:
            return "down"

        return "up"

    def hhv_vm_state(self, hlh, vm):
        return ("VM", vm, self._hhv_vm_state(hlh, vm))

    @staticmethod
    def _hhv_vnet_state(hlh, vnet):
        if vnet not in hlh.all_vnet_names:
            return "missing"

        if vnet not in hlh.active_vnet_names:
            return "down"

        return "up"

    def hhv_vnet_state(self, hlh, vnet):
        return ("VNET", vnet, self._hhv_vnet_state(hlh, vnet))

    def hhv_vm_info(self, hlh, vm_entry):
        states = [self.hhv_vm_state(hlh, vm_entry['domain'])]
        states.extend([self.hhv_vnet_state(hlh, vnet)
                       for vnet in vm_entry['networks']])

        not_healthy = [s for s in states if s[2] != "up"]
        if not_healthy:
            message = "VM %s is not healthy" % vm_entry['domain']
            detail = "\n".join(["%s %s is %s" % e for e in not_healthy])
        else:
            message = "VM %s is healthy" % vm_entry['domain']
            detail = "No problems detected"

        result = dict(metric=("hlm-hypervisor.vcp_vm.%s" %
                              vm_entry['domain']),
                      value=int(bool(len(not_healthy))),  # 0 or 1
                      value_meta=dict(message=message, detail=detail))

        return result

    def _build_metrics(self, hlh, inst, dims):
        raise NotImplemented

    def check(self, instance):
        dimensions = self._set_dimensions(None, instance)
        hlh = _HHVLibvirtHelper('qemu:///system')

        try:
            metrics = self._build_metrics(hlh, instance, dimensions)
            for metric in metrics:
                self.gauge(**metric)

        except Exception as e:
            log.error('Error in performing check - %s' % e.message)

    def dependencies_installed(self):
        return True


class HLMHypervisorSummary(_HLMHypervisorBase):

    def _build_summary_metrics(self, hlh, inst, dims):
        vm_infos = [self.hhv_vm_info(hlh, vm)
                    for vm in inst.get("domains", [])]
        not_healthy = [vmi for vmi in vm_infos if vmi['value'] != 0]

        if not_healthy:
            message = "VCP VMs are not healthy"
            detail = "\n".join([e['value_meta']['detail']
                                for e in not_healthy])
        else:
            message = "VCP VMs are healthy"
            detail = "No problems detected"

        result = dict(metric="hlm-hypervisor.vcp_vms",
                      value=int(bool(len(not_healthy))),  # 0 or 1
                      value_meta=dict(message=message, detail=detail),
                      dimensions=dims)

        return [result]

    def _build_vm_metrics(self, hlh, inst, dims):
        result = self.hhv_vm_info(hlh, inst)
        result['dimensions'] = dims

        return [result]

    def _build_metrics(self, hlh, inst, dims):
        metrics = []

        check_type = inst.get('check_type')
        if check_type == "vm":
            metrics = self._build_vm_metrics(hlh, inst, dims)
        elif check_type == "summary":
            metrics = self._build_summary_metrics(hlh, inst, dims)
        elif check_type is None:
            log.warn("Skipping invalid instance; no check_type found")
        else:
            log.warn("Skipping invalid instance; check_type not valid")

        return metrics
