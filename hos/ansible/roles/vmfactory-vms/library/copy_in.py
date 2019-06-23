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
import guestfs
import libvirt

# TODO: Do we need VIR_DOMAIN_SHUTDOWN since we don't use it below?
from libvirt import VIR_DOMAIN_SHUTDOWN, VIR_DOMAIN_SHUTOFF


# Need to add in some try except logic to handle errors here and
# retun an error via module error logic
def copy_in(image, inlist, outlist):
    g = guestfs.GuestFS(python_return_dict=True)
    g.add_drive_opts(image)
    g.launch()
    g.mount("/dev/hlm-vg/root", "/")
    for infile, outfile in zip(inlist, outlist):
        g.upload(infile, outfile)
    g.sync()
    g.umount_all()
    return True


def check_poweredoff_state(vmname):
    conn = libvirt.open("qemu:///system")
    vm = conn.lookupByName(vmname)
    state = vm.state()[0]
    conn.close()
    if state == VIR_DOMAIN_SHUTOFF:
        return True
    else:
        return False


def same_type(t, *args):
    return ((len(set(type(a) for a in args))) == 1)


def all_are_type(t, *args):
    return all(isinstance(a, t) for a in args)


def all_are_strs(*args):
    return all_are_type(str, *args)


def all_are_lists(*args):
    return all_are_type(list, *args)


def lists_same_length(*args):
    return (all_are_lists(*args) and
            (len(set(len(a) for a in args)) == 1))


def main():
    module = AnsibleModule(
        argument_spec=dict(
           vmname=dict(required=True),
           infile=dict(required=True),
           outfile=dict(required=True),
           image=dict(required=True)
        )
    )
    vmname = module.params['vmname']
    inlist = module.params['infile']
    outlist = module.params['outfile']
    image = module.params['image']

    # check that both infile and outfile are the same type
    if not same_type(inlist, outlist):
        module.fail_json(msg="infile & outfile must but be of the same type.")

    # if both infile and outfile are lists, check they are list of strings
    # and that the lists are the same length
    if all_are_lists(inlist, outlist):
        if not (lists_same_length(inlist, outlist) and
                all_are_strs(*inlist) and
                all_are_strs(*outlist)):
            module.fail_json(msg="infile & outfile can be lists of paths "
                                 "but both lists must be the same length.")

    # if both infile and outfile are strings, convert to lists
    if all_are_strs(inlist, outlist):
        inlist = [inlist]
        outlist = [outlist]

    if check_poweredoff_state(vmname):
        # Only change if node is powered off
        changed = copy_in(image, inlist, outlist)
    else:
        changed = 0
    result = dict(changed=changed, rc=0)
    module.exit_json(**result)


from ansible.module_utils.basic import *  # noqa
main()
