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

import jinja2.runtime as jrt

DEFAULT_VNI_RANGE = '1001:65535'

VXLAN_TAG = 'neutron.networks.vxlan'
VLAN_TAG = 'neutron.networks.vlan'
FLAT_TAG = 'neutron.networks.flat'
EXTNET_BRIDGE_TAG = 'neutron.l3_agent.external_network_bridge'

TENANT_VXLAN_ID_RANGE = 'tenant-vxlan-id-range'
TENANT_VLAN_ID_RANGE = 'tenant-vlan-id-range'
PROVIDER_PHYSNET = 'provider-physical-network'

TEST_INPUT_1 = {
    'neutron': {
        'EXTERNAL-VM': {
            EXTNET_BRIDGE_TAG: None},
        'GUEST': {
            VXLAN_TAG: {
                TENANT_VXLAN_ID_RANGE: '7000:8000,9000:10000'}},
        'MANAGEMENT': {
            VLAN_TAG: {
                PROVIDER_PHYSNET: 'physnet1',
                TENANT_VLAN_ID_RANGE: '100:200,300:400'}}},
    'vsa-storage': {
        'ISCSI': {
            'vsa.iscsi': None}},
    'foo-service': {
        'GUEST': {
            VXLAN_TAG: {
                TENANT_VXLAN_ID_RANGE: '7000:8000,9000:10000'}},
        'FOO': {
            VLAN_TAG: {
                PROVIDER_PHYSNET: 'physnet2'}}}}

TEST_INPUT_2 = {
    'neutron': {
        'EXTERNAL-VM': {
            EXTNET_BRIDGE_TAG: None},
        'GUEST': {
            VXLAN_TAG: None},
        'MANAGEMENT': {
            VLAN_TAG: {
                PROVIDER_PHYSNET: 'physnet1',
                TENANT_VLAN_ID_RANGE: '100:200,300:400'}},
        'FOO': {
            VLAN_TAG: {
                PROVIDER_PHYSNET: 'foo1',
                TENANT_VLAN_ID_RANGE: '500:600,700:800'}},
        'BAR': {
            FLAT_TAG: {
                PROVIDER_PHYSNET: 'bar1'}},
        'BAZ': {
            FLAT_TAG: {
                PROVIDER_PHYSNET: 'baz1'}}}}

TEST_INPUT_3 = {
    'neutron': {
        'GUEST': {
            VXLAN_TAG: {
                'foo': 'bar'}}}}

TEST_INPUT_4 = {
    'neutron': {
        'EXTERNAL-VM': {
            EXTNET_BRIDGE_TAG: None},
        'GUEST': {
            VXLAN_TAG: {
                TENANT_VXLAN_ID_RANGE: '7000:8000,9000:10000'}},
        'MANAGEMENT': {
            VLAN_TAG: {
                PROVIDER_PHYSNET: 'physnet1'}}}}

TEST_INPUT_5 = {
    'neutron': {
        'EXTERNAL-VM': {
            EXTNET_BRIDGE_TAG: None},
        'GUEST': {
            VXLAN_TAG: None},
        'MANAGEMENT': {
            VLAN_TAG: {
                PROVIDER_PHYSNET: 'physnet1',
                TENANT_VLAN_ID_RANGE: '100:200'}},
        'BAR': {
            FLAT_TAG: {
                PROVIDER_PHYSNET: 'bar1'}},
        'BAZ': {
            FLAT_TAG: {
                PROVIDER_PHYSNET: 'baz1'}}}}


def _iter_over_tags(network_tag_values, tag_filter=None):
    for service in network_tag_values:
        for netgroup in network_tag_values[service]:
            for tag, tag_data in network_tag_values[service][netgroup].items():
                if not tag_filter:
                    yield tag, tag_data
                elif tag_filter == tag:
                    yield tag, tag_data


#
# _get_vni_ranges filter:
#
# Sample usage:
# Return the string of vni_ranges given the dict of network_tag_values:
#
# {{ network_tag_values | _get_vni_ranges }}
#
#
# For example, when passed the following network_tag_values, this filter
# returns "7000:8000,9000:10000"
#
# network_tag_values:
#   neutron:
#     GUEST:
#       neutron.networks.vxlan:
#         tenant-vxlan-id-range: 7000:8000,9000:10000

def get_vni_ranges(network_tag_values, default=DEFAULT_VNI_RANGE):
    range_set = set()
    try:
        for tag, tag_data in _iter_over_tags(network_tag_values, VXLAN_TAG):
            if not tag_data or TENANT_VXLAN_ID_RANGE not in tag_data:
                range_set.add(default)
            else:
                range_set |= set(tag_data[TENANT_VXLAN_ID_RANGE].split(','))
        return ','.join(range_set)
    except jrt.UndefinedError:
        return default

#
# get_vlan_ranges filter:
#
# Usage:
# {{ network_tag_values | _get_vlan_ranges }}
#
# Sample usage:

# network_tag_values:
#   neutron:
#     GUEST:
#       neutron.networks.vlan:
#         provider-physical-network: physnet1
#
# returns "physnet1"
#
# network_tag_values:
#   opendaylight:
#     GUEST:
#       neutron.networks.vlan:
#         provider-physical-network: physnet1
#         tenant-vxlan-id-range: 7000:8000
#
# returns "physnet1:7000:8000"
#

def get_vlan_ranges(network_tag_values):
    range_set = set()
    try:
        for tag, tag_data in _iter_over_tags(network_tag_values, VLAN_TAG):
            if PROVIDER_PHYSNET in tag_data:
                if TENANT_VLAN_ID_RANGE in tag_data:
                    for range in tag_data[TENANT_VLAN_ID_RANGE].split(','):
                        range_set.add(tag_data[PROVIDER_PHYSNET] + ":" + range)
                else:
                    range_set.add(tag_data[PROVIDER_PHYSNET])
        return ','.join(range_set)
    except jrt.UndefinedError:
        return ''

def test_get_vni_ranges():

    # multiple services using the same vxlan tag
    actual = get_vni_ranges(TEST_INPUT_1).split(',')
    expected = ['7000:8000', '9000:10000']
    assert sorted(actual) == sorted(expected)

    # check that default isn't used when range is specified
    actual = get_vni_ranges(TEST_INPUT_1, '100:200').split(',')
    expected = ['7000:8000', '9000:10000']
    assert sorted(actual) == sorted(expected)

    # check that default is used when no range is specified
    actual = get_vni_ranges(TEST_INPUT_2)
    expected = DEFAULT_VNI_RANGE
    assert actual == expected

    # check that default is used when unrecognized key/value pair is in
    # the tag_data and no range is specified
    actual = get_vni_ranges(TEST_INPUT_3)
    expected = DEFAULT_VNI_RANGE
    assert actual == expected

def test_get_vlan_ranges():
    # no vlan tag
    actual = get_vlan_ranges(TEST_INPUT_3).split(',')
    expected = ['']
    assert actual == expected

    # vlan tag but no range
    actual = get_vlan_ranges(TEST_INPUT_4).split(',')
    expected = ['physnet1']
    assert actual == expected

    # vlan tag with a single range
    actual = get_vlan_ranges(TEST_INPUT_5).split(',')
    expected = ['physnet1:100:200']
    assert actual == expected

    # vlan tag with multiple ranges
    actual = get_vlan_ranges(TEST_INPUT_2).split(',')
    expected = ['physnet1:100:200','physnet1:300:400','foo1:500:600','foo1:700:800']
    assert sorted(actual) == sorted(expected)

    # vlan tag with multiple ranges and non-neutron service
    actual = get_vlan_ranges(TEST_INPUT_1).split(',')
    expected = ['physnet1:100:200','physnet1:300:400','physnet2']
    assert sorted(actual) == sorted(expected)


class FilterModule(object):
    def filters(self):
        return {
            '_get_vni_ranges': get_vni_ranges,
            '_get_vlan_ranges': get_vlan_ranges,
        }


def run_tests():
    test_get_vni_ranges()
    test_get_vlan_ranges()


if __name__ == "__main__":
    run_tests()
