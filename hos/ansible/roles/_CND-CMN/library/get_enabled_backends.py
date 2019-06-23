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
module: get_enabled_backends
short_description: constructs a list of enabled backends.
description:
     - The module accepts a cinder config structure and returns a string
     comprising a list of enabled backends.
options:
  cinder_config:
    description:
      - Cinder config data
    required: true
    default: null
author:
'''

EXAMPLES = '''
# Example from Ansible Playbooks.
- get_enabled_backends: cinder_config = '{{ config_data.CND | to_json }}'

# Returns string comprising a list of the enabled backends.

# NOTE: Please use single quotes for host info converted to JSON as
# double quotes will cause argument errors
'''

from subprocess import PIPE, Popen


class openssl:
    # Lifted from hosencrypt.py
    prefix = '@hos@'

    def __init__(self, key=None):
        self._decrypt_key = key

    def delegate(self, cmd, value):
        argv = ('/usr/bin/openssl', 'aes-256-cbc', '-a', cmd,
                '-pass', 'pass:%s' % self._decrypt_key)
        p = Popen(argv, close_fds=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        result = p.communicate(input=value)
        if p.returncode != 0:
            errmsg = result[1].strip()
            if errmsg.startswith('bad decrypt'):
                errmsg = 'incorrect encryption key'
            elif (errmsg.startswith('error reading input file') or
                  errmsg.startswith('bad magic number')):
                errmsg = 'bad input data'
            raise OSError('openssl: %s' % errmsg)
        return result[0].strip()

    def decrypt(self, cooked):
        if cooked.startswith(openssl.prefix):
            cooked = cooked[len(openssl.prefix):]
        # openssl expects a newline at the end of the string.
        if cooked[-1] != '\n':
            cooked += '\n'
        return self.delegate('-d', cooked)


def get_enabled_backends(cp_hosts, backends, fz_confs,
                         fz_hosts, cinder_config):
    # Return a dictionary of lists, the keys in the dictionary are the
    # controller host names, and the values are lists of backends that
    # will be enabled for that host. The list can be empty.

    enabled_backends = {h: [] for h in cp_hosts}
    for be in backends:
        host = select_controller(enabled_backends, fz_confs, fz_hosts,
                                 be, cinder_config[be])
        enabled_backends[host].append(be)

    return enabled_backends


def select_controller(cp_hosts, fz_confs, fz_hosts, backend, config):
    # Select the controller node to manage the backend.
    candidate_fzs = None
    if 'failure-zone' in config:
        candidate_fzs = [fz for fz in fz_confs if backend in fz_confs[fz]]
    # If it's not in any failure-zone, then choose from all the controllers
    if candidate_fzs is None:
        selected_host = cp_hosts.keys()[0]
        for h in sorted(cp_hosts):
            if len(cp_hosts[h]) < len(cp_hosts[selected_host]):
                selected_host = h
        return selected_host

    # Now find the least used host in that list of AZs
    selected_host = fz_hosts[candidate_fzs[0]][0]
    for fz in sorted(candidate_fzs):
        for h in sorted(fz_hosts[fz]):
            if len(cp_hosts[h]) < len(cp_hosts[selected_host]):
                selected_host = h
    return selected_host


def get_failure_zone_lists(cinder_config, cp_hosts, groups):
    # Returns two dictionaries fc_confs and fc_hosts, the keys are the failure
    # zones that are referenced. The values in fz_confs are lists of the cinder
    # configs that reference that failure-zone. The values in fc_hosts are lists
    # of controller nodes that are in that failure-zone.
    fz_confs = {}
    for conf_name, conf in cinder_config.iteritems():
        if 'failure-zone' in conf:
            for fz in conf['failure-zone']:
                if fz in fz_confs:
                    fz_confs[fz].append(conf_name)
                else:
                    fz_confs[fz] = [conf_name]

    # TODO Get the list of failure-zones required for each resource group
    # referencing a cinder-config section. These will be added to the lists in
    # fc_confs.

    # Now get the list of nodes in each failure-zone
    fz_hosts = {}
    for fz in fz_confs:
        if fz in groups:
            fz_hosts[fz] = [h for h in cp_hosts if h in groups[fz]]
        else:
            fz_hosts[fz] = []
    return fz_confs, fz_hosts

def validate_user_assignment(user_assigned_host, backend, enabled_backends):
    # Returns True if the user assigned host and backend both exist in enabled_backends

    if user_assigned_host in enabled_backends:
        for key in enabled_backends.keys():
            if backend in enabled_backends[key]:
                return True
    return False

def get_user_specified_assignment(enabled_backends, user_assignment):

    for backend, user_assigned_host in user_assignment.iteritems():
        if validate_user_assignment(user_assigned_host, backend, enabled_backends):
            for host in enabled_backends.keys():
                # If the user has associated a backend with a host then if needed
                # make the same association in enabled_backends
                if user_assigned_host == host:
                    if backend not in enabled_backends[host]:
                        enabled_backends[host].append(backend)
                # If the backend association differs with whats in enabled_backends
                # remove it from enabled_backends
                else:
                    if backend in enabled_backends[host]:
                        enabled_backends[host].remove(backend)
    return enabled_backends

def get_vsa_provided_data(section, service_data, provided_data, host_data):
    """Include VSA specific configuration logic

    The VSA configuration requires a URL that is configured from the vip,
    protocol and suffix provided by the service configuration.

    We also set a default value for the VSA management username and the
    VSA cluster name.
    """
    if not 'backend-config' in section:
        section['backend-config'] = {}
    backend_configuration = section['backend-config']
    backend_configuration['hpelefthand_api_url'] = (
        '%s://%s:%s%s' % (service_data['protocol'],
                          provided_data['service_vip']['vip'],
                          service_data['port'],
                          service_data['url_suffix']))
    backend_configuration['hpelefthand_clustername'] = (
        'cluster-%s' % provided_data['cluster'])
    backend_configuration['hpelefthand_username'] = (
        'mg-%s' % provided_data['cluster'])

def get_ceph_provided_data(section, service_data, provided_data, host_data):
    """At this point there is no ceph specific configuration logic"""
    pass

def get_cinder_config(section, service_data, provided_data):
    if not 'backend-config' in section:
        section['backend-config'] = {}
    backend_configuration = section['backend-config']
    for key in service_data['backend-config']:
        backend_configuration[key] = service_data['backend-config'][key]
    for key in provided_data:
        if key == 'volume-types':
            continue
        backend_configuration[key] = provided_data[key]

known_services = {
    'VSA-BLK': get_vsa_provided_data,
    'CEP-BLK': get_ceph_provided_data,
    }

def decrypt_value(key, value, decryptor):
    """Decrypt configuration values

    Users can enter encrypted values for configuration variables like this:

        backend-config:
          unencrypted_variable: cleartext
          encrypted_variable:
              value: "ciphertext"
              encrypted: true

    If a variable has a dictionary as a value then this method will return the
    cleartext value.
    """
    if decryptor is None:
        raise Exception("The configuration variable %s may be encrypted, but "
                        "HOS_USER_PASSWORD_ENCRYPT_KEY has not been set." %
                        key)
    if not 'value' in value:
        raise Exception("The dictionary for the variable %s must have the key"
                        " 'value': %s" % (key, value))
    if not 'encrypted' in value:
        raise Exception("The dictionary for the variable %s must have the key"
                        " 'encrypted': %s" % (key, value))
    if value['encrypted'] is True:
        return decryptor.decrypt(value['value'])
    else:
        return value['value']

def get_provided_data(host_data, cinder_config, cinder_data, decrypt_key):
    """Link the provided_by reference in cinder_config.yml to service data

    The provided_by stanza for a backend in cinder_config.yml must provide a
    key/value pair that exists in the provided_by section of the provided_data
    section of the CND_VOL dictionary. This is generated from the service
    config input model, eg vsa/vsa_config.yml.

    This method takes the backend-config data from the service config model
    and generates data used to generate the backend configuration in
    cinder.conf.
    """
    provided_data = None
    if 'provided_data' in cinder_data:
        provided_data = cinder_data['provided_data']
    for section in cinder_config:
        if 'provided_by' in cinder_config[section]:
            provided_by = cinder_config[section]['provided_by']
            provided_key = provided_by.keys()[0]
            provided_value = provided_by[provided_key]
            p_data = None
            for pd in provided_data:
                if pd['provided_by'][provided_key] == provided_value:
                    p_data = pd['provided_by']
                    service_data = pd['data']
                    if p_data['name'] in known_services:
                        known_services[p_data['name']](cinder_config[section],
                                                       service_data,
                                                       p_data,
                                                       host_data)
                    backend_data = {}
                    if 'config_data' in p_data and ('backend-config' in
                                                    p_data['config_data']):
                        backend_data = p_data['config_data']['backend-config']
                    get_cinder_config(cinder_config[section],
                                      service_data,
                                      backend_data)

            if p_data is None:
                raise Exception("No config data for provided_by %s: %s" %
                                (provided_key, provided_value))

        # Check for encrypted config variables in this section.
        decryptor = None
        if decrypt_key and decrypt_key != "":
            decryptor = openssl(decrypt_key)
        cnf = cinder_config[section]['backend-config']
        for v in cnf:
            if isinstance(cnf[v], dict):
                cnf[v] = decrypt_value(v, cnf[v], decryptor)

def main():
    """Generates cinder.conf from input model data

    The parameters required are:
        host_data: The data for the host being configured.
        cinder_config_data: The input model data from cinder_config.yml
        groups: The groups variable from the input model
        vol_group_name: The string to use to find the group of cinder-volume
                        hosts in groups.
        cinder_data: The data from the provided_by section of cinder
        user_assignment_data: The list of backends that have been assigned to
                              a specific cinder-volume host.
    """
    module = AnsibleModule(
        argument_spec=dict(
            host_data=dict(type='dict'),
            cinder_config_data=dict(type='dict'),
            groups=dict(type='dict'),
            vol_group_name=dict(type='str'),
            cinder_data=dict(type='dict'),
            decryption_key=dict(type='str'),
            user_assignment_data=dict(type='dict')
        )
    )
    host_data = module.params['host_data']
    cinder_config = module.params['cinder_config_data']
    groups = module.params['groups']
    cp_hosts = module.params['groups'][module.params['vol_group_name']]
    cinder_data = module.params['cinder_data']
    decrypt_key = module.params['decryption_key']
    user_assignment = module.params['user_assignment_data']

    if not cinder_config:
        module.fail_json(rc=256, msg="No cinder config info specified")

    get_provided_data(host_data['my_dimensions'], cinder_config, cinder_data, decrypt_key)

    # If we can assume that the lists presented to this method on every
    # controller host will be in the same order, then the next two operations
    # are not required
    sorted_hosts = sorted(cp_hosts)
    sorted_backends = sorted(cinder_config.keys())

    fz_confs, fz_hosts = get_failure_zone_lists(cinder_config,
                                                cp_hosts, groups)

    enabled_backends = get_enabled_backends(sorted_hosts,
                                            sorted_backends,
                                            fz_confs,
                                            fz_hosts,
                                            cinder_config)

    if user_assignment:
        enabled_backends = get_user_specified_assignment(enabled_backends, user_assignment)

    backend_configs = []
    for be in cinder_config:
        section = {'name': be}
        section['config'] = cinder_config[be]['backend-config']
        backend_configs.append(section)

    module.exit_json(
        control_plane_hosts=cp_hosts,
        cinder_enabled_backends=enabled_backends,
        cinder_backend_configs=backend_configs,
        stderr='',
        rc=0,
        changed=True
    )


from ansible.module_utils.basic import *    # NOQA

main()
