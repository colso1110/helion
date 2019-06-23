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
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: keystone_federation
version_added: "1.0"
short_description: Manage federation APIs, Identity Providers, Protocols,
                   Mappings, Service Providers
description:
   - Manage federation APIs from OpenStack.
   - Authentication should be added to each call with
      token/domain scope token cred/project scope token credentials
     Examples below uses token, instead you can also specify login credentials
requirements: [ python-keystoneclient ]
author: Sam Leong
'''

EXAMPLES = '''

# Create an identity provider
- keystone_federation: action="create_identity_provider"
                       login_token=admin
                       identity_provider_id="Foo"
                       description="Foo Identity Provider"
                       endpoint=https://keystone:35357/v3

# Create a mapping
- keystone_federation: action="create_mapping"
                       login_token=admin
                       mapping_id="My_mapping"
                       rules="{mapping:...}"

# Create a protocol
- keystone_federation: action="create_protocol"
                       protocol_id="My_protocol"
                       identity_provider_id="Foo"
                       mapping_id="My_mapping"

'''

from ansible.module_utils.basic import *
from ansible.module_utils.database import *
from keystoneclient import exceptions
from keystoneclient import session
from keystoneclient.auth import token_endpoint
from keystoneclient.auth.identity import v3
from keystoneclient.v3 import client as v3client


def _get_client(auth_url=None, token=None, insecure=False, ca_cert=None):
    """Return a ks_client client object"""

    auth_plugin = token_endpoint.Token(endpoint=auth_url, token=token)
    if not insecure:
        # Caller wants cert verification
        verify = ca_cert or True

    # Client cert is not supported now.
    # Will add it later with cert=client_cert option
    auth_session = session.Session(
        auth=auth_plugin, verify=verify)
    return v3client.Client(auth_url=auth_url, session=auth_session)


def _find_identity_provider(ks_client, identity_provider_id=None):
    try:
        return ks_client.federation.identity_providers.get(
            identity_provider=identity_provider_id)
    except exceptions.NotFound:
        return None


def _find_protocol(ks_client, identity_provider_id=None, protocol_id=None):
    try:
        return ks_client.federation.protocols.get(
            identity_provider=identity_provider_id,
            protocol=protocol_id)
    except exceptions.NotFound:
        return None


def _find_mapping(ks_client, mapping_id=None):
    try:
        return ks_client.federation.mappings.get(mapping=mapping_id)
    except exceptions.NotFound:
        return None


def _find_service_provider(ks_client, service_provider_id=None):
    try:
        return ks_client.federation.service_providers.get(
            service_provider=service_provider_id)
    except exceptions.NotFound:
        return None


def find_identity_provider(ks_client, identity_provider_id=None):
    identity_provider = _find_identity_provider(
        ks_client,
        identity_provider_id=identity_provider_id)

    if identity_provider is not None:
        return True, identity_provider

    return False, None


def delete_identity_provider(ks_client, identity_provider_id=None):
    identity_provider = _find_identity_provider(
        ks_client,
        identity_provider_id=identity_provider_id)

    if identity_provider is not None:
        ks_client.federation.identity_providers.update(
            identity_provider=identity_provider_id, enabled=False)
        ks_client.federation.identity_providers.delete(
            identity_provider=identity_provider_id)
        return True, identity_provider

    # identity_provider with that Id doesn't exist
    return False, None


def create_identity_provider(ks_client, identity_provider_id=None,
                             enabled=True, description=None, remote_id=None):
    identity_provider = _find_identity_provider(
        ks_client,
        identity_provider_id=identity_provider_id)

    if identity_provider is not None:
        delete_identity_provider(
            ks_client,
            identity_provider_id=identity_provider_id)

    # identity_provider with that Id doesn't exist
    remote_ids = []
    if remote_id:
        remote_ids.append(remote_id)
    identity_provider = ks_client.federation.identity_providers.create(
        id=identity_provider_id,
        enabled=enabled,
        description=description,
        remote_ids=remote_ids)
    return True, identity_provider


def find_protocol(ks_client, identity_provider_id=None, protocol_id=None):
    protocol = _find_protocol(ks_client,
                              identity_provider_id=identity_provider_id,
                              protocol_id=protocol_id)
    if protocol is not None:
        return True, protocol

    return False, None


def delete_protocol(ks_client, identity_provider_id=None, protocol_id=None):
    protocol = _find_protocol(ks_client,
                              identity_provider_id=identity_provider_id,
                              protocol_id=protocol_id)

    if protocol is not None:
        ks_client.federation.protocols.delete(
            identity_provider=identity_provider_id,
            protocol=protocol_id)
        return True, protocol

    return False, protocol


def create_protocol(ks_client, protocol_id=None, identity_provider_id=None,
                    mapping_id=None):
    protocol = _find_protocol(ks_client,
                              identity_provider_id=identity_provider_id,
                              protocol_id=protocol_id)

    if protocol is not None:
        delete_protocol(ks_client,
                        identity_provider_id=identity_provider_id,
                        protocol_id=protocol_id)

    protocol = ks_client.federation.protocols.create(
        protocol_id=protocol_id,
        identity_provider=identity_provider_id,
        mapping=mapping_id)
    return True, protocol


def find_mapping(ks_client, mapping_id=None):
    mapping = _find_mapping(ks_client, mapping_id=mapping_id)

    if mapping is not None:
        return True, mapping

    return False, None


def delete_mapping(ks_client, mapping_id=None):
    mapping = _find_mapping(ks_client, mapping_id=mapping_id)

    if mapping is not None:
        ks_client.federation.mappings.delete(mapping=mapping_id)
        return True, mapping

    return False, mapping


def create_mapping(ks_client, mapping_id=None, rules=None):
    mapping = _find_mapping(ks_client, mapping_id=mapping_id)

    if mapping is not None:
        delete_mapping(ks_client, mapping_id=mapping_id)

    mapping = ks_client.federation.mappings.create(mapping_id=mapping_id,
                                                   rules=rules)
    return True, mapping


def find_service_provider(ks_client, service_provider_id=None):
    sp = _find_service_provider(ks_client,
                                service_provider_id=service_provider_id)

    if sp is not None:
        return True, sp

    return False, None


def delete_service_provider(ks_client, service_provider_id=None):
    sp = _find_service_provider(ks_client,
                                service_provider_id=service_provider_id)

    if sp is not None:
        ks_client.federation.service_providers.update(
            service_provider=service_provider_id, enabled=False)
        ks_client.federation.service_providers.delete(
            service_provider=service_provider_id)
        return True, sp

    return False, sp


def create_service_provider(ks_client, service_provider_id=None, auth_url=None,
                            enabled=True, description=None, sp_url=None):
    sp = _find_service_provider(ks_client,
                                service_provider_id=service_provider_id)

    if sp is not None:
        delete_service_provider(ks_client,
                                service_provider_id=service_provider_id)

    sp = ks_client.federation.service_providers.create(id=service_provider_id,
                                                       auth_url=auth_url,
                                                       enabled=enabled,
                                                       description=description,
                                                       sp_url=sp_url)
    return True, sp


dispatch_map = {
    "find_identity_provider": find_identity_provider,
    "delete_identity_provider": delete_identity_provider,
    "create_identity_provider": create_identity_provider,

    "find_protocol": find_protocol,
    "delete_protocol": delete_protocol,
    "create_protocol": create_protocol,

    "find_mapping": find_mapping,
    "delete_mapping": delete_mapping,
    "create_mapping": create_mapping,

    "find_service_provider": find_service_provider,
    "delete_service_provider": delete_service_provider,
    "create_service_provider": create_service_provider,
}


def process_params(module):
    identity_provider_id = module.params.get("identity_provider_id", None)
    description = module.params.get("description", None)
    remote_id = module.params.get("remote_id", None)
    protocol_id = module.params.get("protocol_id", None)
    mapping_id = module.params.get("mapping_id", None)
    rules = module.params.get("rules", None)
    service_provider_id = module.params.get("service_provider_id", None)
    auth_url = module.params.get("auth_url", None)
    sp_url = module.params.get("sp_url", None)

    action = module.params["action"]
    if action not in dispatch_map:
        raise RuntimeError("unknown action: {}".format(action))

    if action in ["find_identity_provider", "delete_identity_provider"]:
        return dict(identity_provider_id=identity_provider_id)
    elif action == "create_identity_provider":
        return dict(identity_provider_id=identity_provider_id,
                    description=description,
                    remote_id=remote_id)
    elif action in ["find_protocol", "delete_protocol"]:
        return dict(identity_provider_id=identity_provider_id,
                    protocol_id=protocol_id)
    elif action == "create_protocol":
        return dict(protocol_id=protocol_id,
                    identity_provider_id=identity_provider_id,
                    mapping_id=mapping_id)
    elif action in ["find_mapping", "delete_mapping"]:
        return dict(mapping_id=mapping_id)
    elif action == "create_mapping":
        return dict(mapping_id=mapping_id, rules=rules)
    elif action in ["find_service_provider", "delete_service_provider"]:
        return dict(service_provider_id=service_provider_id)
    elif action == "create_service_provider":
        return dict(service_provider_id=service_provider_id, auth_url=auth_url,
                    description=description, sp_url=sp_url)
    else:
        raise NotImplementedError(action)


def get_client(module):

    auth_url = module.params.get("endpoint")
    token = module.params.get("login_token")
    insecure = module.params.get("insecure")
    cacert = module.params.get("cacert")

    ks_client = _get_client(
        auth_url=auth_url, token=token,
        insecure=insecure, ca_cert=cacert)

    return ks_client


def process_module_action(module):

    ks_client = get_client(module)

    action = module.params["action"]
    kwargs = process_params(module)

    try:
        result = dispatch_map[action](ks_client, **kwargs)
    except Exception as e:
        module.fail_json(msg="%s, failed" % e)
    else:
        status, resource_data = result
        if hasattr(resource_data, '_info'):
            resource_data = resource_data._info
        data = dict(changed=status, result=resource_data)
        module.exit_json(**data)


def main():
    supported_actions = dispatch_map.keys()

    argument_spec = dict(
        login_token=dict(default=None, no_log=True),
        insecure=dict(default=None),
        cacert=dict(default=None),

        endpoint=dict(default=None),
        description=dict(default="Created by Ansible keystone_v3"),
        identity_provider_id=dict(default=None),
        remote_id=dict(default=None),
        protocol_id=dict(default=None),
        mapping_id=dict(default=None),
        rules=dict(default=None),
        service_provider_id=dict(default=None),
        sp_url=dict(default=None),
        auth_url=dict(default=None),

        action=dict(default=None, required=True, choices=supported_actions)
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)
    process_module_action(module)


if __name__ == '__main__':
    main()
