#!/usr/bin/env python
#
# An Ansible module to configure VSA cluster.
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

# import module snippets
from ansible.module_utils.basic import *  # NOQA
import subprocess

DOCUMENTATION = '''
---
module: can_resize_cluster
version_added: "1.0"
short_description: Validates VSA nodes can be added to or removed
                   from existing cluster
vsa_node_list: ips of VSA nodes in respective cluster
cluster_master_node: VSA node ip on which CLI commands will be executed
vsa_mg_user: VSA management group username
vsa_mg_password: VSA management group password
'''

EXAMPLES = '''
- can_resize_cluster:
    vsa_node_list: "192.17.17.8;192.17.17.11"
    cluster_master_node: "192.17.17.8"
    vsa_mg_user: "stack"
    vsa_mg_password: "stack"
'''


def can_resize_cluster(module, cp_node_list, cluster_master_node, mg_user,
                       mg_password, min_cluster_size=3, max_cluster_size=16):
    """
    Checks if VSA node can be added to or removed from existing cluster.
    :param cp_node_list: IP addresses of vsa nodes in input-model
    :param cluster_master_node: VSA node to run CLI commands
    :param mg_user: VSA mgmt user
    :mg_password: VSA mgmt password
    """

    cluster_node_list = []
    cp_node_list = cp_node_list.split(',')
    no_of_nodes_in_cp = len(cp_node_list)

    cl_ssh_cmd = 'sshpass -p %s ssh -o StrictHostKeyChecking=no -p 16022 -l' \
                 ' %s  %s getClusterInfo | grep ipAddress' % (
                     mg_password, mg_user, cluster_master_node)
    cmd_resp = subprocess.check_output(cl_ssh_cmd, stderr=subprocess.STDOUT,
                                       shell=True)

    no_of_nodes_in_cl = cmd_resp.count("ipAddress") - 1

    for i in xrange(no_of_nodes_in_cl):
        cluster_node_list.append(cmd_resp.split('\n')[i].split(' ')[6])

    if no_of_nodes_in_cl < no_of_nodes_in_cp:
        if no_of_nodes_in_cp <= max_cluster_size:
            module.exit_json(**dict(changed=True,
                                    msg='Validation success; '
                                        'cluster_node_list: %s,'
                                        ' cp_node_list: %s' % (
                                            cluster_node_list, cp_node_list)))
        else:
            module.fail_json(**dict(
                msg="A cluser cannot have more than %s. "
                    "Current node count is %s" % (max_cluster_size,
                                                  no_of_nodes_in_cp)))
    elif no_of_nodes_in_cl > no_of_nodes_in_cp:
        if no_of_nodes_in_cp >= min_cluster_size:
            module.exit_json(**dict(
                changed=True,
                msg='Validation success; cluster_node_list: %s '
                    'cp_node_list: %s' % (
                        cluster_node_list, cp_node_list)))
        else:
            module.fail_json(**dict(
                msg="Not allowed to remove a node from %s node cluster; "
                    "cluster_node_list: %s cp_node_list: %s"
                    % (min_cluster_size, cluster_node_list, cp_node_list)))
    else:
        node_diff = list(set(cluster_node_list) - set(cp_node_list))
        if len(node_diff) >= 1:
            module.exit_json(**dict(
                changed=True,
                msg='Validation success; cluster_node_list: %s, '
                    'cp_node_list: %s' % (
                        cluster_node_list, cp_node_list)))
        else:
            module.exit_json(**dict(changed=False,
                                    msg='No change in VSA nodes; '
                                        'cluster_node_list: %s, '
                                        'cp_node_list: %s' % (
                                            cluster_node_list, cp_node_list)))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            vsa_node_list=dict(required=True),
            cluster_master_node=dict(required=True),
            vsa_mg_user=dict(required=True),
            vsa_mg_password=dict(required=True),
        ),
        supports_check_mode=False
    )

    try:
        params = module.params
        can_resize_cluster(module,
                           params['vsa_node_list'],
                           params['cluster_master_node'],
                           params['vsa_mg_user'],
                           params['vsa_mg_password'])
    except Exception, e:
        module.fail_json(msg='Exception: %s' % e)


if __name__ == '__main__':
    main()
