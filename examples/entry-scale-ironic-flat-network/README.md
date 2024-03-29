
(c) Copyright 2015 Hewlett Packard Enterprise Development LP

Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.


##Helion Entry Scale Cloud with Ironic Example##

The input files in this example deploy a Baremetal cloud using Ironic that has the following characteristics:

### Control Planes ###

- A single control plane consisting of three servers that co-host all of the required services.

###Resource Pools###

*Minimal Swift Resources are provided by the control plane*

*Additional Ironic bare metal nodes resource nodes can be added later by using Ironic API.*

###Lifecycle Manager###

This configuration runs the lifecycle-manager on a control plane node. You need to include
this node address in your servers.yml definition.
This function does not need a dedicated network.

*The minimum server count for this example is therefore 4 servers
(Control Plane (x3) + 1 nova-compute proxy.*
*(Additional bare metal nodes will be added after deployment via the Ironic API)*


An example set of servers are defined in ***data/servers.yml***. You will need to modify
this file to reflect your specific environment.


###Networking###

The example requires the following networks:

IPMI/iLO network, connected to the deployer and the IPMI/iLO ports of all servers

A pair of bonded NICs which are used by the following networks:

- External API - This is the network that users will use to make requests to the cloud
- Management - This is the network that will be used for all internal traffic
  between the cloud services. This network is also used to install and configure the
  controller nodes only.
  This network needs to be on an untagged VLAN
- Guest - This is the flat network that will carry traffic between baremetal instances within
  the cloud. This is also the network used to PXE boot the ironic nodes and install the
  operating system selected by tenants.

Note that the EXTERNAL\_API network must be reachable from the GUEST network if you
want bare metal nodes to be able to make API calls to the cloud.

An example set of networks are defined in ***data/networks.yml***. You will need to
modify this file to reflect your environment.

The example uses the devices hed3 & hed4 as a bonded network for all services.
If you need to modify these for your environment they are defined in
***data/net_interfaces.yml*** The network devices eth3 & eth4 are renamed to devices
hed4 & hed5 using the PCI bus mappings specified in  ***data/nic_mappings.yml***.
You may need to modify the PCI bus addresses to match your system.

###Local Storage###

All servers should present a single OS disk, protected by a RAID controller. This
disk needs to be at least 512GB in capacity. In addition the example configures
additional disk depending on the role of the server:

- Controllers:  /dev/sdb and /dev/sdc is configured to be used by Swift

Additional discs can be configured for any of these roles by editing the corresponding
***data/disks_*.yml*** file
