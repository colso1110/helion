#!/bin/sh
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
# HELION-MANAGED - Managed by Helion - Do not edit

devpath=`env | grep 'DEVPATH' | cut -f2 -d '='`
NET_PCI_SCRIPT=/etc/udev/hlm_network_pci.py
if [ -x $NET_PCI_SCRIPT ]
then
     $NET_PCI_SCRIPT $devpath
fi
