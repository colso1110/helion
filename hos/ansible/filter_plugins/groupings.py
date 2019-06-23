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
import itertools


def group_by_key(ungrouped, key_name):
    """Groups dictionaries into lists if they have the same value for a given
    key.

    Steps though a list of dictionaries. If the values of the given key match
    the dictionaries are placed in a list together. These lists are then stored
    in a dictionary where the keys are the value matched. This dictionary is
    then returned by the function.
    """
    def keyfn(item):
        return item[key_name]

    groupfn = itertools.groupby(sorted(ungrouped, key=keyfn), keyfn)
    grouped = {k: [i for i in g] for k, g in groupfn}
    return grouped


def sum_groups_by_key(unsummed, key_name):
    """Computes the sum of the values for a given key across multiple dicts.

    Steps through a dictionary of lists. Each list is a list of dictionaries.
    For each dictionary in a list this function computes the sum of the value
    of a given key. A dictionary with the lists replaced by the result of each
    sum calculation is returned.
    """
    def sumfn(count, item):
        return count + item.get(key_name, 0)

    summed = {k: reduce(sumfn, g, 0) for k, g in unsummed.iteritems()}
    return summed


def group_sum_by_keys(ungrouped, group_key, sum_key):
    """Groups dictionaries by a common value and then returns the sum of
    this a second value for each group."""
    grouped = group_by_key(ungrouped, group_key)
    summed = sum_groups_by_key(grouped, sum_key)
    return summed


class FilterModule(object):
    def filters(self):
        return {"sum_groups_by_key": sum_groups_by_key,
                "group_by_key": group_by_key,
                "group_sum_by_keys": group_sum_by_keys}
