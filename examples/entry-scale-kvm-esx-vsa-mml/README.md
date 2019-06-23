
(c) Copyright 2016 Hewlett Packard Enterprise Development LP

Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.


##Helion Single Region Entry-scale-mml ESX+KVM+VSA Cloud model##
###Introduction###

This entry-scale model is intended as a template for a moderate sized cloud with few limitation like single management network and swift + neutron on control plane itself. The Control plane is made up of multiple server clusters to provide sufficient computational, network and IOPS capacity for a mid-size production style cloud.

The Helion entry-scale-kvm-esx-vsa-mml model is architected as follows:

####Control plane###

  - Core cluster: Runs Core OpenStack Services, (e.g. keystone, nova api, glance api, neutron api, horizon, heat api). Default configuration is two nodes of role type CORE-ROLE

  - Metering & Monitoring cluster: Runs the OpenStack Services for metering & monitoring (e.g. celiometer, monasca & logging). Default configuration is three nodes of role type MTRMON-ROLE

  - Database & Message Queue Cluster: Runs clustered MySQL and RabbitMQ services to support the Helion cloud infrastructure. Default configuration is three nodes of role type DBMQ-ROLE. Three nodes are required for high availability.

####Resource nodes###
  - Compute:
     - KVM: Runs nova compute sand associated services. Runs on nodes of role type COMPUTE-ROLE. The example lists 3 nodes, one node is required at a minimum.
     - ESX: (below listed resources will be provisioned in all activated clusters)
        - Nova compute proxy nodes runs nova compute services.
        - OVSvApp nodes run neutron related services.
  - Vsa: Runs the Store Virtual VSA appliance. Runs on nodes of role type VSA-ROLE. One node minimum is required for demo purposes, three for high availability. The example lists 1 node.

  *EON service will add required information related to nova compute proxy and OVSvApp Nodes. The user need not add them*

  *Minimal Swift Resources are provided by the control plane*

###Networking###

The example requires the following networks:

IMPI/iLO network, connected to the deployer and the IPMI/iLO ports of all servers

A network connected to a dedicated NIC on each server used to install the OS and install and configure Helion. In a future Beta release this network can be subsumed into system networks (below).

A pair of bonded NICs which are used used by the following networks:

- External API - This is the network that users will use to make requests to the cloud
- Internal API - This is the network that will be used within the cloud for API access between services
- External VM - This is the network that will be used to provide access to VMs (via floating IP addresses)
- Guest - This is the network that will carry traffic between VMs on private networks within the cloud
- Cloud Management - This is the network that will be used for all internal traffic between the cloud services. In the example this is shown as untagged. It can be tagged if needed.

Note that the EXTERNAL\_API network must be reachable from the EXTERNAL\_VM network if you want VMS to be able to make  API calls to the cloud.

TRUNK network is the network that will be used to apply security group rules on tenant traffic. It is managed internally by Helion cloud and is restricted to the vCenter environment.

ESX-CONF-NET network (of ESX-CONF network-group) represents a network that is used only to configure the ESX compute nodes in the cloud. This deployer network should be different from the pxe-based deployer network used by cobbler to standup the cloud controller cluster.

The Data Center Management network (which hosts the vcenter server) must be reachable from the Cloud Management network so that the controllers,
compute proxy and OVSvApp nodes can communicate to the vcenter server.

An example set of networks are defined in ***data/networks.yml***.    You will need to modify this file to reflect your environment.

The example uses bonded network for control planes, KVM computes, VSA, DBMQ & MTRMON nodes. If you need to modify these for your environment they are defined in ***data/net_interfaces.yml***

###Adapting the entry-scale model to fit your environment###

The minimum set of changes you need to make to adapt the model for your environment are:

- Update servers.yml to list the details of your bare metal servers (i.e ILO access info) If You need to perform this step if you are using the HLM supplied Cobber playbooks to install hLinux on your servers.

- Update the networks.yml file to replace network CIDRs and VLANs with site specific values

- Update the nic_mappings.yml file to ensure that network devices are mapped to the correct physical port(s)

- Review the disk models (disks_*.yml) and confirm that the associated
    servers have the number of disks required by the disk model. The device
    names in the disk models might need to be adjusted to match the probe order
    of your servers.
Disk models are provided as follows:

  - DISK SET CONTROLLER: Minimum 1 disk
  - DISK SET DBMQ: Minimum 3 disks
  - DISK SET COMPUTE: Minimum 2 disks
  - DISK SET VSA: Minimum 3 disks

*DISK_SET used by Nova compute proxy and OVSvApp is not recommended to modify by user*


- Update the net interfaces.yml file to match the server NICs used in your configuration. This file has a separate interface model definition for each of the following:

  - INTERFACE SET CONTROLLER
  - INTERFACE SET MTRMON
  - INTERFACE SET DBMQ
  - INTERFACE SET COMPUTE
  - INTERFACE SET VSA
  - INTERFACE SET ESX-COMPUTE
  - INTERFACE SET OVSVAPP
