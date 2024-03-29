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
DOCUMENTATION = '''
---
module: monasca_alarm_definition
short_description: crud operations on Monasca alarm definitions
description:
    - Performs crud operations (create/update/delete) on monasca alarm definitions
    - Monasca project homepage - https://wiki.openstack.org/wiki/Monasca
    - When relevant the alarm_definition_id is in the output and can be used with the register action
author: Tim Kuhlman <tim@backgroundprocess.com>
requirements: [ python-monascaclient ]
options:
    alarm_actions:
        required: false
        description:
            -  Array of notification method IDs that are invoked for the transition to the ALARM state. Will not overwrite for existing definitions
    api_version:
        required: false
        default: '2_0'
        description:
            - The monasca api version.
    description:
        required: false
        description:
            - The description associated with the alarm definition
    expression:
        required: false
        description:
            - The alarm definition expression, required for create/update operations.
    keystone_password:
        required: false
        description:
            - Keystone password to use for authentication, required unless a keystone_token is specified.
    keystone_url:
        required: false
        description:
            - Keystone url to authenticate against, required unless keystone_token is defined.
              Example http://192.168.10.5:5000/v3
    keystone_token:
        required: false
        description:
            - Keystone token to use with the monasca api. If this is specified the monasca_api_url is required but
              the keystone_user and keystone_password aren't.
    keystone_user:
        required: false
        description:
            - Keystone user to log in as, required unless a keystone_token is specified.
    keystone_project:
        required: false
        description:
            - Keystone project name to obtain a token for, defaults to the user's default project
    match_by:
        required: false
        default: "[hostname]"
        description:
            - Alarm definition match by, see the monasca api documentation for more detail.
    monasca_api_url:
        required: false
        description:
            - If unset the service endpoint registered with keystone will be used.
    name:
        required: true
        description:
            - The alarm definition name
    ok_actions:
        required: false
        description:
            -  Array of notification method IDs that are invoked for the transition to the OK state. Will not overwrite for existing definitions
    severity:
        required: false
        default: "LOW"
        description:
            - The severity set for the alarm definition must be LOW, MEDIUM, HIGH or CRITICAL
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the alarm definition should exist.  When C(absent), removes the alarm definition. The name
              is used to determine the alarm definition to remove
    undetermined_actions:
        required: false
        description:
            -  Array of notification method IDs that are invoked for the transition to the UNDETERMINED state. Will not overwrite for existing definitions
'''

EXAMPLES = '''
- name: Host Alive Alarm
  monasca_alarm_definition:
    name: "Host Alive Alarm"
    expression: "host_alive_status > 0"
    keystone_url: "{{monasca_keystone_url}}"
    keystone_user: "{{monasca_keystone_user}}"
    keystone_password: "{{monasca_keystone_password}}"
  tags:
    - alarms
    - system_alarms
  register: out
- name: Create System Alarm Definitions
  monasca_alarm_definition:
    name: "{{item.name}}"
    expression: "{{item.expression}}"
    keystone_token: "{{out.keystone_token}}"
    monasca_api_url: "{{out.monasca_api_url}}"
  with_items:
    - { name: "High CPU usage", expression: "avg(cpu.idle_perc) < 10 times 3" }
    - { name: "Disk Inode Usage", expression: "disk.inode_used_perc > 90" }
'''

from ansible.module_utils.basic import *
import os

try:
    from monascaclient import client
    from monascaclient import ksclient
except ImportError:
    paths = ["/opt/stack/service/monascaclient/venv", "/opt/monasca"]
    for path in paths:
        activate_this = os.path.realpath(path + '/bin/activate_this.py')
        if not os.path.exists(activate_this):
            continue
        try:
            execfile(activate_this, dict(__file__=activate_this))
            from monascaclient import client
            from monascaclient import ksclient
        except ImportError:
            monascaclient_found = False
        else:
            monascaclient_found = True
            break
else:
    monascaclient_found = True


# With Ansible modules including other files presents difficulties otherwise this would be in its own module
class MonascaAnsible(object):
    """ A base class used to build Monasca Client based Ansible Modules
        As input an ansible.module_utils.basic.AnsibleModule object is expected. It should have at least
        these params defined:
        - api_version
        - keystone_token and monasca_api_url or keystone_url, keystone_user and keystone_password and optionally
          monasca_api_url
    """
    def __init__(self, module):
        self.module = module
        self._keystone_auth()
        self.exit_data = {'keystone_token': self.token, 'monasca_api_url': self.api_url}
        self.monasca = client.Client(self.module.params['api_version'], self.api_url, token=self.token)

    def _exit_json(self, **kwargs):
        """ Exit with supplied kwargs combined with the self.exit_data
        """
        kwargs.update(self.exit_data)
        self.module.exit_json(**kwargs)

    def _keystone_auth(self):
        """ Authenticate to Keystone and set self.token and self.api_url
        """
        if self.module.params['keystone_token'] is None:
            try:
                ks = ksclient.KSClient(auth_url=self.module.params['keystone_url'],
                                       username=self.module.params['keystone_user'],
                                       password=self.module.params['keystone_password'],
                                       project_name=self.module.params['keystone_project'])
            except Exception, e:
                self.module.fail_json(msg='Keystone KSClient Exception: %s' % e)

            self.token = ks.token
            if self.module.params['monasca_api_url'] is None:
                self.api_url = ks.monasca_url
            else:
                self.api_url = self.module.params['monasca_api_url']
        else:
            if self.module.params['monasca_api_url'] is None:
                self.module.fail_json(msg='Error: When specifying keystone_token, monasca_api_url is required')
            self.token = self.module.params['keystone_token']
            self.api_url = self.module.params['monasca_api_url']


class MonascaDefinition(MonascaAnsible):
    def run(self):
        name = self.module.params['name']
        expression = self.module.params['expression']

        # Find existing definitions
        definitions = {definition['name']: definition for definition in self.monasca.alarm_definitions.list()}

        if self.module.params['state'] == 'absent':
            if name not in definitions.keys():
                self._exit_json(changed=False)

            if self.module.check_mode:
                self._exit_json(changed=True)
            resp = self.monasca.alarm_definitions.delete(alarm_id=definitions[name]['id'])
            if resp.status_code == 204:
                self._exit_json(changed=True)
            else:
                self.module.fail_json(msg=str(resp.status_code) + resp.text)
        else:  # Only other option is state=present
            def_kwargs = {"name": name, "description": self.module.params['description'], "expression": expression,
                          "match_by": self.module.params['match_by'], "severity": self.module.params['severity'],
                          "alarm_actions": self.module.params['alarm_actions'],
                          "ok_actions": self.module.params['ok_actions'],
                          "undetermined_actions": self.module.params['undetermined_actions']}

            if name in definitions.keys():
                if definitions[name]['expression'] == expression and \
                   definitions[name]['severity'] == def_kwargs['severity']:
                    self._exit_json(changed=False, alarm_definition_id=definitions[name]['id'])
                def_kwargs['alarm_id'] = definitions[name]['id']
                del def_kwargs['alarm_actions']
                del def_kwargs['ok_actions']
                del def_kwargs['undetermined_actions']

                if self.module.check_mode:
                    self._exit_json(changed=True, alarm_definition_id=definitions[name]['id'])
                body = self.monasca.alarm_definitions.patch(**def_kwargs)
            else:
                if self.module.check_mode:
                    self._exit_json(changed=True)
                body = self.monasca.alarm_definitions.create(**def_kwargs)

            if 'id' in body:
                self._exit_json(changed=True, alarm_definition_id=body['id'])
            else:
                self.module.fail_json(msg=body)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            alarm_actions=dict(required=False, default=[], type='list'),
            api_version=dict(required=False, default='2_0', type='str'),
            description=dict(required=False, type='str'),
            expression=dict(required=False, type='str'),
            keystone_password=dict(required=False, type='str'),
            keystone_token=dict(required=False, type='str'),
            keystone_url=dict(required=False, type='str'),
            keystone_user=dict(required=False, type='str'),
            keystone_project=dict(required=False, type='str'),
            match_by=dict(default=['hostname'], type='list'),
            monasca_api_url=dict(required=False, type='str'),
            name=dict(required=True, type='str'),
            ok_actions=dict(required=False, default=[], type='list'),
            severity=dict(default='LOW', type='str'),
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            undetermined_actions=dict(required=False, default=[], type='list')
        ),
        supports_check_mode=True,
        no_log=True
    )

    if not monascaclient_found:
        module.fail_json(msg="python-monascaclient >= 1.0.9 is required")

    definition = MonascaDefinition(module)
    try:
        definition.run()
    except Exception, e:
        definition.module.fail_json(msg='Monascaclient Exception: %s' % e)

if __name__ == "__main__":
    main()
