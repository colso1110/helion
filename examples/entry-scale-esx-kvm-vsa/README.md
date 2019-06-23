
(c) Copyright 2015-2016 Hewlett Packard Enterprise Development LP

Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.


## Helion Single region Entry Scale Cloud with ESX+KVM+VSA Example ##

The input files in this example deploy a cloud with ESX and KVM hypervisor that has the following characteristics:


### Control Planes ###

- A single control plane consisting of three servers that co-host all of the required services.

### Resource Pools ###
- Compute:
    - KVM: Runs nova computes and associated services. Runs on nodes of role type COMPUTE-ROLE. The example lists 1 node.
    - ESX: (below listed reqources will be provisioned for all activated clusters)
        - Nova compute proxy nodes runs nova compute services.
        - OVSvApp nodes run neutron related services.
    - VSA: Runs the Store Virtual VSA appliance. Runs on nodes of role type VSA-ROLE. One node minimum is required for demo purposes,
    three for high availability. The example lists 1 node.

*EON service will add required information related to compute proxy and OVSvApp Nodes. The user need not add them*

*Minimal Swift Resources are provided by the control plane*

### Deployer Node ###

This configuration runs the lifecycle-manager (formerly referred to as the deployer) on a control plane node.
You need to include this node address in your servers.yml definition. This function does not need a dedicated network.

The minimum server count for this example is therefore 4 servers (Control Plane (x3) + 1 activated vCenter cluster having atleast 1 host)

An example set of servers are defined in ***data/servers.yml***.   You will need to modify this file to reflect your specific environment.


### Networking ###

The example requires the following networks:

IPMI/iLO network, connected to the deployer and the IPMI/iLO ports of all servers

A pair of bonded NICs which are used by the following networks:

- EXTERNAL-API - This is the network that users will use to make requests to the cloud
- EXTERNAL-VM - This is the network that will be used to provide access to VMs (via floating IP addresses)
- GUEST - This is the network that will carry traffic between VMs on  private networks within the cloud services.
- MANAGEMENT - This is the network that will be used for all internal traffic between the cloud services and traffic between VMs on private networks within the cloud

Note that the EXTERNAL_API network must be reachable from the EXTERNAL_VM network if you want VMs to be able to make API calls to the cloud.

TRUNK network is the network that will be used to apply security group rules on tenant traffic. It is managed internally by Helion cloud and
is restricted to the vCenter environment.

ESX-CONF-NET network (of ESX-CONF network-group) represents a network that is used only to configure the ESX compute nodes in the cloud.  This deployer network should be different from the pxe-based deployer network used by cobbler to standup the cloud controller cluster.

The Data Center Management network (which hosts the vcenter server) must be reachable from the Cloud Management network so that the controllers,
compute proxy and OVSvApp nodes can communicate to the vcenter server.

An example set of networks are defined in ***data/networks.yml***.    You will need to modify this file to reflect your environment.

The example uses the devices hed3 & hed4 as a bonded network for all services.  If you need to modify these for your environment they
are defined in ***data/net_interfaces.yml***.    The network devices eth3 & eth4 are renamed to devices hed3 & hed4 using the PCI bus mappings
specified in  ***data/nic_mappings.yml***.    You may need to modify the PCI bus addresses to match your system.

###Adapting the entry-scale model to fit your environment###

The minimum set of changes you need to make to adapt the model for your environment are:

- Update servers.yml to list the details of your bare metal servers (i.e ILO access info). You need to perform this step if you are using
 the HLM supplied Cobber playbooks to install hLinux on your servers.

- Update the networks.yml file to replace network CIDRs and VLANs with site specific values

- Update the nic_mappings.yml file to ensure that network devices are mapped to the correct physical port(s)

- Review the disk models (disks_*.yml) and confirm that the associated servers have the number of disks required by the disk model.
  The device names in the disk models might need to be adjusted to match the probe order of your servers.
Disk models are provided as follows:
    - DISK SET CONTROLLER: Minimum 1 disk
    - DISK SET KVM COMPUTE: Minimum 2 disks
    - DISK SET VSA: Minimum 3 disks

- Update the net interfaces.yml file to match the server NICs used in your configuration. This file has a separate interface model
  definition for each of the following:
    - INTERFACE SET CONTROLLER
    - INTERFACE SET COMPUTE
    - INTERFACE SET VSA
    - INTERFACE SET ESX-COMPUTE
    - INTERFACE SET OVSVAPP

*DISK_SET used by Nova compute proxy and OVSvApp is not recommanded to modify by user*
