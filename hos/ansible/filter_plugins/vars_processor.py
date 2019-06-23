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


def extract_network_attr(networks, attribute, tag='vsa.iscsi'):
    """Extract network attribute if it is marked with
    specific tag.

    :param networks: list of networks to be searched for a tag
    :param attribute: attribute name for which value needs to be extracted
    :param tag: tag name for which enquiry need to be made
    :return: None if failed else value of attribute
    """
    for net in networks:
        for e in net['tags']:
            if e['tag'] == tag and attribute in net:
                return net[attribute]


class FilterModule(object):
    ''' Ansible filter to extract attributes from network tags '''

    def filters(self):
        return {
            # lookup tags for network attribute
            'extract_network_attr': extract_network_attr,
        }
