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
# This plugin provides the following filters.
# pci_changed: This is to determine whether any configuration for a
#              PCI interface changed or not.
# pci_deleted: This is to determine whether the existing interface is
#              moved from PCI device to non-PCI device.
# pci_config_script_list: This is to get a list of config scripts
#              for PCI interfaces which are newly added, or changed,
#              or deleted.
# pci_add_update_delete_list: This is to get a list of PCI interfaces
#              which are newly added, or changed, or deleted.
# pci_packages: This is to get a list of packages to be installed
#               on a host based on the drivers specified
# pci_modules: This is to get a list of modules to be installed on
#              a host based on the drivers specified.
# pci_validate_multi_port_interfaces: This is to validate that vf_count
#              is not configured for more than one port of multi-port
#              interfaces.
#

def pci_changed(new_list, old_list):
    """Returns True or False based on the two lists are same or not."""
    for new_entry in new_list:
        match_found = False
        for old_entry in old_list:
            if (new_entry['device'] == old_entry['device'] and
                new_entry.get('config_script', None) == old_entry['config_script'] and
                new_entry['vf_count'] == old_entry['vf_count'] and
                new_entry['nic_device_type']['device_id'] == old_entry['device_id']):
                # A match is found. No change for that entry.
                match_found = True
                break
        if not match_found:
           # This means that the entry is changed in the new list.
           # As there is at least one change detected, we can declare
           # that two lists are not the same.
           return True
    # Nothing got changed. Return False.
    return False

def pci_deleted(new_list, old_list):
    """Returns list of elements in old_list which are not present in new list."""
    delete_list = []
    for entry in old_list:
        # Check whether bus addresses and interface names match in the two lists for
        # each entry.
        bus_addr_matches = [x for x in new_list if x['bus_address'] == entry['bus_address'] and
                            x.get('config_script', None)]
        device_matches = [x for x in new_list if x['device'] == entry['device'] and
                          x.get('config_script', None)]
        if not (bus_addr_matches and device_matches):
            delete_list.append(entry)
    return delete_list

def pci_config_script_list(new_list, old_list):
    """Returns a list of config scripts.

    Returns a list of config scripts from the list of added, modified and deleted
    interfaces so that post_configure operation can be performed.
    """
    config_script_list = []
    for new_entry in new_list:
        match_found = False
        for old_entry in old_list:
            if (new_entry['device'] == old_entry['device'] and
                new_entry.get('config_script', None) == old_entry['config_script'] and
                new_entry['vf_count'] == old_entry['vf_count'] and
                new_entry['nic_device_type']['device_id'] == old_entry['device_id']):
                # A match is found. No change for that entry.
                match_found = True
                break
        if not match_found:
           # This means that the entry is changed in the new list.
           # Or, the entry is totally new one.
           # Add the config_script to the list.
           config_script_list.append(new_entry['config_script'])

    # Check for deleted interfaces. Post-configure operation is
    # required for deleted interfaces as well.
    delete_list = pci_deleted(new_list, old_list)
    for entry in delete_list:
        config_script_list.append(entry['config_script'])
    # Return the final list with unique elements
    return config_script_list

def pci_add_update_delete_list(new_list, old_list):
    """Returns a list of PCI interfaces which are added/modified/deleted."""
    add_modify_list = []
    for new_entry in new_list:
        match_found = False
        for old_entry in old_list:
            if (new_entry['device'] == old_entry['device'] and
                new_entry.get('config_script', None) == old_entry['config_script'] and
                new_entry['vf_count'] == old_entry['vf_count'] and
                new_entry['nic_device_type']['device_id'] == old_entry['device_id']):
                # A match is found. No change for that entry.
                match_found = True
                break
        if not match_found:
           # This means that the entry is changed in the new list.
           # Or, the entry is totally new one.
           # Add the config_script to the list.
           add_modify_list.append(new_entry)

    # Check for deleted interfaces.
    delete_list = pci_deleted(new_list, old_list)
    # Return the final list with unique elements
    return add_modify_list + delete_list

def _pci_packages(network_pci_pt_sriov_interfaces, package_list):
    pkg_list = []
    for interface in network_pci_pt_sriov_interfaces:
        for pkg in package_list:
            for k,v in pkg.items():
                matched_drivers = [driver for driver in v['drivers'] if driver == interface['driver']]
                if matched_drivers:
                    pkg_list.append(pkg)
    return pkg_list

def pci_packages(network_pci_pt_sriov_interfaces, package_list):
    """Returns a list of packages with matching drivers in network_pci_pt_sriov_interfaces."""
    lst = []
    tmp_pkg_list = _pci_packages(network_pci_pt_sriov_interfaces, package_list)
    for pkg in tmp_pkg_list:
        for k, v in pkg.items():
            lst.append(k)
    return lst

def pci_modules(network_pci_pt_sriov_interfaces, package_list):
    """Returns a list of modules from the package list."""
    mod_list = []
    tmp_pkg_list = _pci_packages(network_pci_pt_sriov_interfaces, package_list)
    for pkg in tmp_pkg_list:
        for k, v in pkg.items():
            mod_list = mod_list + v['modules']
    return mod_list

def pci_validate_multi_port_interfaces(multi_port_interfaces, config_scripts):
    """Returns an error string after performing a validation check on multi-port interfaces.

    Validation performed: For multi-port interfaces, vf_count cannot be configured for more than one port.
    """
    for interface in multi_port_interfaces:
        matched_bus_addresses = [x for x in multi_port_interfaces if x['bus_address'] == interface['bus_address']]
        bus_addresses_with_vfs = [y for y in matched_bus_addresses if 'vf_count' in y]
        if len(bus_addresses_with_vfs) > 1:
            for bus_address in bus_addresses_with_vfs:
                for script in config_scripts:
                    if (bus_address['config_script'] == script['name'] and
                        script.get('multi_vf_allowed', 'false') == 'false'):
                        return "For multi-port interfaces, vf_count cannot be configured for more than one port. bus_address = %s" % bus_address['bus_address']
    return ""

class FilterModule(object):

    def filters(self):
        return {'pci_changed': pci_changed,
                'pci_deleted': pci_deleted,
                'pci_config_script_list': pci_config_script_list,
                'pci_add_update_delete_list': pci_add_update_delete_list,
                'pci_packages': pci_packages,
                'pci_modules': pci_modules,
                'pci_validate_multi_port_interfaces': pci_validate_multi_port_interfaces
                }
