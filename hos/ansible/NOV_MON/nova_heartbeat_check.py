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

import socket

import keystoneclient
import keystoneclient.auth.identity.v3
import keystoneclient.session
import monasca_agent.collector.checks as checks
from novaclient import client as novacli


THIS_HOST = socket.gethostname()

OK = 0
WARN = 1
FAIL = 2
UNKNOWN = 3


def metric(message=None, state=FAIL, **kwargs):
    dims = {'observer_hostname': THIS_HOST,
            'service': 'compute'}
    dims.update(kwargs)
    metric = {
        'metric': 'nova.heartbeat',
        'dimensions': dims,
        'value': state,
    }
    if message:
        metric['value_meta'] = {'msg': message}
    return metric


class NovaHeartbeatCheck(checks.AgentCheck):
    def __init__(self, name, init_config, agent_config, instances=None):
        super(NovaHeartbeatCheck, self).__init__(
            name, init_config, agent_config, instances=instances)
        self.client = None

    def _get_client(self):
        key_args = self.init_config['keystone']
        auth = keystoneclient.auth.identity.v3.Password(**key_args)
        sess = keystoneclient.session.Session(auth=auth)
        nova_args = self.init_config['nova']
        return novacli.Client(2, session=sess, **nova_args)

    def _get_state(self, service):
        if service.state == 'up' or service.status == 'disabled':
            return OK
        return FAIL

    def _gather_metrics(self):
        if not self.client:
            self.client = self._get_client()
        services = self.client.services.list(host=THIS_HOST)
        # [{"status": "enabled",
        #   "binary": "nova-compute",
        #   "zone": "nova",
        #   "state": "down",
        #   "updated_at": "2015-10-03T02:33:38.000000",
        #   "host": "padawan-ccp-compute0001-mgmt",
        #   "disabled_reason": null,
        #   "id": 31}]
        return [metric(state=self._get_state(service),
                       hostname=service.host,
                       component=service.binary)
                for service in services]

    def check(self, instance):
        metrics = self._gather_metrics()

        self.log.debug("Collected %d heartbeat metrics", len(metrics))
        for metric in metrics:
            # apply any instance dimensions that may be configured,
            # overriding any dimension with same key that check has set.
            metric['dimensions'] = self._set_dimensions(
                metric['dimensions'], instance)
            try:
                self.gauge(**metric)
            except Exception as e:  # noqa
                self.log.error('Exception while reporting metric: %s' % e)
