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


#
# get_provided_data_values filter:
#
# Sample usage:
# Return the list of 'mechanism_drivers' parameters provided to the
# neutron-ml2-plugin (NEU-ML2) service.
#
#    {{ NEU_ML2 | get_provided_data_values('mechanism_drivers') }}
#
def get_provided_data_values(grp, option, default=[]):
    value_list = []
    try:
        for pd in grp.get('provided_data', []):
            for pdd in pd.get('data', []):
                if pdd.get('option', '') == option:
                    value_list.extend(pdd.get('values', []))
    except (jrt.UndefinedError, AttributeError):
        return default
    return value_list


def test_get_provided_data_values():
    input = {'provided_data': [{'data': [{'option': 'pet',
                                          'values': ['dog', 'cat']},
                                         {'option': 'flowers',
                                          'values': ['iris']}],
                                'provided_by': 'SVC1'},
                               {'data': [{'option': 'pet',
                                          'values': ['turtle']}],
                                'provided_by': 'SVC2'}]}

    expected = ['dog', 'cat', 'turtle']
    assert set(get_provided_data_values(input, 'pet')) == set(expected)
    assert get_provided_data_values(input, 'flowers') == ['iris']
    assert get_provided_data_values('string', 'pet') == []
    assert get_provided_data_values(
        'string', 'pet', default=['undefined']) == ['undefined']


class FilterModule(object):
    def filters(self):
        return {
            'get_provided_data_values': get_provided_data_values
        }


if __name__ == "__main__":
    test_get_provided_data_values()
