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

DOCUMENTATION = '''
---
module: update_mlx4_udev_rules
short_description: Updates the udev rules for mellanox cards on HLM upgrade
description:
    - Reads the existing rules
    - Generates a new file in correct format if its a mellanox card
options:
  in_file:
    description:
      - The input file, the existing rules.
    required: True
  out_file:
    description:
      - The output file containing the new generated rules.
    required: True
'''

EXAMPLES = '''
- update_mlx4_udev_rules:
     inFile: "/etc/udev/rules.d/70-persistent-net.rules"
     outFile: "/etc/udev/rules.d/80-hos-preserve_eth_names.rules"
'''
import json
import os


def update_udev_rules(module,in_file, out_file):

    in_lines = read_udev_file(module, in_file)
    if not ("(mlx4_core)" in ''.join(in_lines)):
        module.exit_json(**dict(changed=False, rc=0))

    first_line = in_lines[0]
    in_warning_line = "# HELION-MANAGED - mlx4_core rules will be in 80-hos-preserve_eth_names.rules\n"

    if in_warning_line not in ''.join(in_lines):
        in_lines[0] = in_warning_line + first_line
        write_udev_file(module, in_file, in_lines)
    else:
        pass

    out_lines = ""
    out_warning_line = "# HELION-MANAGED - Managed by Helion - Do not edit\n\n"
    out_lines += out_warning_line

    for i, line in enumerate(in_lines):
        if "(mlx4_core)" in line:
            out_lines += ''.join(line)
            temp_line = in_lines[i+1]
            temp_line = temp_line.replace('dev_id', 'dev_port')
            temp_line = temp_line.split(',')

            for j, item in enumerate(temp_line):
                if "ATTR{dev_port}" in item:
                    temp = temp_line[j].split('==')
                    temp[1] = int(temp[1].strip('"'), 16)
                    temp[1] = '"%s"' % temp[1]
                    string = "==".join(temp)
                    temp_line[j] = string
                    in_lines[i+1] =  ','.join(temp_line)
                    out_lines += in_lines[i+1]+'\n'
                else:
                    continue

    write_udev_file(module, out_file, out_lines)

def read_udev_file(module, filename):

    file_contents = ""
    try:
        with open(filename, 'r') as pfile:
            file_contents = pfile.readlines()
    except:
        error_msg = 'Error: Cannot open %s' % (filename)
        module.fail_json(msg=error_msg)

    return file_contents

def write_udev_file(module, filename, content):

    lines = ''.join(content)
    try:
        with open(filename, "w") as pfile:
            pfile.write(lines)
    except:
        error_msg = 'Error: Cannot open %s' % (filename)
        module.fail_json(msg=error_msg)

def main():
    module = AnsibleModule(
        argument_spec = dict(
           inFile=dict(required=True),
           outFile=dict(required=True)
    ))
    in_file = module.params['inFile']
    out_file = module.params['outFile']
    update_udev_rules(module, in_file, out_file)
    changed = (os.path.exists(out_file))
    result = dict(changed=changed, rc=0)
    module.exit_json(**result)

from ansible.module_utils.basic import *
main()
