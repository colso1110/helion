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
# Create variable value validation filter


def is_str_set(my_var, do_define_check=True):
    """Returns True if variable is set to a non-blank value.

    Input value is stripped on both end to make sure it has value.
    """
    if do_define_check:
        try:
            my_var
        except NameError:
            my_var = None
    if my_var is None:
        return False
    elif isinstance(my_var, (int, long)):
        return my_var  # return natural number as-is
    else:
        return my_var and my_var.strip() != ''


def is_bool_true(my_var, do_define_check=True):
    """Check variable value can be converted to boolean True

    Case-insensitive input value of True, yes or 1 is treated as boolean True.
    """
    if do_define_check:
        try:
            my_var
        except NameError:
            my_var = None
    if my_var and type(my_var) == type(True):
        return my_var
    else:
        return my_var and my_var.strip().lower() in ['yes', 'true', '1', 'on']


class FilterModule(object):

    def filters(self):
        return {'is_str_set': is_str_set,
                'is_bool_true': is_bool_true,
                }
