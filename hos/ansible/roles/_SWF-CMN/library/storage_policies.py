#!/usr/bin/python
#
# (c) Copyright 2015,2016 Hewlett Packard Enterprise Development LP
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
import json
import shlex
import sys


def dash_to_underscore(obj):
    """
    Configuration data is not underscored
    :param obj: The object to convert
    :return:The converted object
    """
    if isinstance(obj, list):
        ret_obj = []
        for item in obj:
            ret_obj.append(dash_to_underscore(item))
    elif isinstance(obj, dict):
        ret_obj = dict()
        for key in obj.keys():
            new_key = key.replace('-', '_')
            ret_obj[new_key] = dash_to_underscore(obj[key])
    else:
        ret_obj = obj
    return ret_obj


def get_storage_policies(ring_model):
    ring_model = dash_to_underscore(ring_model)
    rings = []
    if isinstance(ring_model, dict):
        # Rings are now in configuration data
        rings = ring_model.get('rings', [])
    else:
        # Rings used to be in a top-level ring-specifications object
        # Support this mode until CP moves them to the config-data object
        # The rings were indexed by region, but this was never used, so just
        # pull off first item.
        if len(ring_model) > 0:
            rings = ring_model[0].get('rings')
    storage_policies = []

    for ring in rings:
        if ring.get('name').startswith('object-'):
            index = ring.get('name')[7:]
            name = ring.get('display_name')
            aliases = ring.get('aliases', [])
            aliases_csv = ','.join(aliases)
            if 'erasure_coding_policy' in ring:
                ec_type = ring.get('erasure_coding_policy').get('ec_type')
                ec_data = ring.get('erasure_coding_policy').get(
                    'ec_num_data_fragments')
                ec_parity = ring.get('erasure_coding_policy').get(
                    'ec_num_parity_fragments')
                ec_seg_size = ring.get('erasure_coding_policy').get(
                    'ec_object_segment_size', '1048576')
                policy = {'policy': {'index': index,
                                     'name': name,
                                     'aliases_csv': aliases_csv,
                                     'ec_type': ec_type,
                                     'ec_data': ec_data,
                                     'ec_parity': ec_parity,
                                     'ec_seg_size': ec_seg_size,
                                     'default': 'no'}}
            else:
                policy = {'policy': {'index': index,
                                     'name': name,
                                     'aliases_csv': aliases_csv,
                                     'default': 'no'}}
            if ring.get('default', False):
                policy['policy']['default'] = 'yes'

            storage_policies.append(policy)

    return storage_policies


def main():
    ringspecs = ''
    region_name = ''
    try:
        args_file = sys.argv[1]
        args_data = file(args_file).read()
        arguments = shlex.split(args_data)
    except (IndexError, IOError):
        arguments = sys.argv  # Running interactively
    for arg in arguments:
        if "=" in arg:
            (key, value) = arg.split('=')
            if key == 'ring-specifications':
                ringspecs = value

    ringspecs = ringspecs.replace("'", '"')          # fix single quotes
    ringspecs = ringspecs.replace('True', 'true')    # fix boolean
    ringspecs = ringspecs.replace('False', 'false')  # fix boolean
    storage_policies = get_storage_policies(json.loads(ringspecs))
    ret = {}
    ret['failed'] = False
    ret['rc'] = 0
    ret['ansible_facts'] = {'storage_policies': storage_policies}
    print(json.dumps(ret))


if __name__ == '__main__':
    main()
