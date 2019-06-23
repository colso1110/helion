#!/opt/stack/service/neutron/venv/bin/python
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

from ansible.module_utils.basic import *
import re
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa

TYPE_VLAN = "vlan"
OVSVAPP_AGENT_TYPE = "OVSvApp Agent"

Base = declarative_base()


class ClusterVNIAllocations(Base):
    """Represents cluster vni allocation table."""

    __tablename__ = "ovsvapp_cluster_vni_allocations"

    vcenter_id = sa.Column(sa.String(36), nullable=False, primary_key=True)
    cluster_id = sa.Column(sa.String(255), nullable=False, primary_key=True)
    lvid = sa.Column(sa.Integer, nullable=False, autoincrement=False,
                     primary_key=True)
    network_id = sa.Column(sa.String(36), default=None)
    allocated = sa.Column(sa.Boolean, nullable=False, default=False)
    network_port_count = sa.Column(sa.Integer, nullable=False, default=0)

    def __repr__(self):
        """Cluster VNI allocations representation."""
        return ("<ClusterVNIAllocations(%s,%s,%s,%s,%s,%s)>." %
                (self.vcenter_id, self.cluster_id, self.lvid, self.network_id,
                 self.allocated, self.network_port_count))

class Agent(object):
    def __init__(self, vcenter_id, cluster_id):
        self.vcenter_id = vcenter_id
        self.cluster_id = cluster_id

class OVSvAppDBUpdate(object):
    def __init__(self, connection):
        # Create a session with Neutron database
        self.engine = sa.create_engine(connection)
        self.metadata = sa.MetaData(self.engine)
        Session = sa.orm.sessionmaker(bind=self.engine)
        self.session = Session()

    def close(self):
        self.session.close()

    def is_ovsvapp_configured_vlan(self, ovsvapp_agent):
        # Every agent should provide bridge mappings information.
        # if the agents does not support VLAN, bridge_mappings will be empty list
        config = eval(re.sub('false', 'False', ovsvapp_agent.configurations))
        bridge_mappings = config['bridge_mappings']
        return bridge_mappings

    def get_ovsvapp_agents(self):
        agents = sa.Table("agents", self.metadata, autoload=True)
        ovsvapp_agents = self.session.query(agents).filter_by(agent_type=OVSVAPP_AGENT_TYPE).all()
        return ovsvapp_agents

    def cluster_entry_exists(self, vcenter_id, cluster_id):
        cluster_table = sa.Table("ovsvapp_cluster_vni_allocations", self.metadata, autoload=True)
        cluster_entry = self.session.query(cluster_table).filter_by(vcenter_id=vcenter_id).filter_by(cluster_id=cluster_id).count()
        return cluster_entry

    def create_cluster_default_entries(self,vcenter_id, cluster_id):
        bulk_size = 100
        allocs = []
        lvid_min = 1
        lvid_max = 4095
        # Create 4094 entries for a cluster
        for lvid in range(lvid_min, lvid_max):
            allocs.append(ClusterVNIAllocations(vcenter_id=vcenter_id,
                                            cluster_id=cluster_id,
                                            lvid=lvid))
        self.session.add_all(allocs)
        self.session.commit()

    def get_ovsvapp_ports(self, hostname):
        # ml2_port_bindings table has host and port_id mapping
        # Get the ports matching passed ovsvapp host
        port_bindings = sa.Table("ml2_port_bindings", self.metadata, autoload=True)
        ports = self.session.query(port_bindings).filter_by(host=hostname).all()
        return ports

    def get_ovsvapp_port_network_map(self, port_ids):
        # From the ports table fetch the port to network map
        ports = sa.Table("ports", self.metadata, autoload=True)
        port_network_map = {}
        for port_id in port_ids:
            port = self.session.query(ports).filter_by(id=port_id).first()
            port_network_map[port_id] = port.network_id
        return port_network_map

    def get_network_ovsvapp_port_count(self, port_ids):
        # Get the number of ovsvapp ports in a network for a host
        # The port_ids passed is the ids of ports on a particular host
        ports = sa.Table("ports", self.metadata, autoload=True)
        nw_port_cnt_map = {}
        for port_id in port_ids:
            port = self.session.query(ports).filter_by(id=port_id).first()
            net_id = port.network_id
            if net_id in nw_port_cnt_map.keys():
                nw_port_cnt_map[net_id] = nw_port_cnt_map[net_id] + 1
            else:
                nw_port_cnt_map[net_id] = 1

        return nw_port_cnt_map

    def get_network_vlans(self, network_ids):
        # Get the VLANs of the networks
        # The network_ids passed is the networks on a particular host
        networks = sa.Table("ml2_network_segments", self.metadata, autoload=True)
        network_vlan_map = {}
        for network_id in network_ids:
            network = self.session.query(networks).filter_by(network_id=network_id).first()
            network_vlan_map[network_id] = network.segmentation_id
        return network_vlan_map

    def update_cluster_lvid_allocations(self, vcenter_id, cluster_id, network_vlan_map,
                                        nw_port_cnt_map):
        # Update the cluster local vlan allocation entries of a host
        # Combination of vcenter_id and cluster_id represents a cluster
        # The combination of vcenter_id, cluster_id and lvid forms a primary key.
        with self.session.begin(subtransactions=True):
            for network in network_vlan_map.keys():
                # In HOS 3.0, for VLAN networks local vlan to global vlan map was not
                # created. The port groups on vCenter had global VLAN as VLAN.
                # Since we dont change the tenant port groups VLAN, we map those VLANs with
                # network_id in the database.
                lvid = network_vlan_map[network]
                port_count = nw_port_cnt_map[network]
                query = self.session.query(ClusterVNIAllocations)
                allocation = (query.filter(
                              ClusterVNIAllocations.vcenter_id == vcenter_id,
                              ClusterVNIAllocations.cluster_id == cluster_id,
                              ClusterVNIAllocations.lvid == lvid
                ).with_lockmode('update').one())

                allocation.network_id = network
                allocation.allocated = 1
                #  Update the database with the port count for the host
                allocation.network_port_count = allocation.network_port_count + port_count
        self.session.commit()

    def update_other_cluster(self, vcenter_id, cluster_id, network_vlan_map, ovsvapp_hosts):
        for element in ovsvapp_hosts.keys():
            # In HOS 3.0, the portgroups are common across cluster within vcenter
            # So update the network lvid mapping on the other clusters too. This
            # update should be for clusters within that vcenter.
            new_vcenter_id = ovsvapp_hosts[element].vcenter_id
            new_cluster_id = ovsvapp_hosts[element].cluster_id
            if ((new_vcenter_id == vcenter_id) and
                (new_cluster_id != cluster_id)):
                with self.session.begin(subtransactions=True):
                    for network in network_vlan_map.keys():
                        lvid = network_vlan_map[network]
                        query = self.session.query(ClusterVNIAllocations)
                        allocation = (query.filter(
                                      ClusterVNIAllocations.vcenter_id == new_vcenter_id,
                                      ClusterVNIAllocations.cluster_id == new_cluster_id,
                                      ClusterVNIAllocations.lvid == lvid
                        ).with_lockmode('update').one())
                        # Update network id and allocated columns. But donot update
                        # anything for network_port_count so that it wont manipulate
                        # anything if the entry exits.
                        allocation.network_id = network
                        allocation.allocated = 1
                self.session.commit()

    def update(self):
        ovsvapp_hosts = {}
        ovsvapp_agents = self.get_ovsvapp_agents()
        # Process further only if there are OVSvApp agents
        if ovsvapp_agents:
            # Check if OVSvApp is configured with VLAN
            # Process further only if VLAN networks present.
            if self.is_ovsvapp_configured_vlan(ovsvapp_agents[0]):
                # Update the default entries for all clusters
                for agent in ovsvapp_agents:
                    config= eval(agent.configurations)
                    vcenter_id = config['vcenter_id']
                    cluster_id = config['cluster_id']
                    ovsvapp_hosts[agent.host] = Agent(vcenter_id, cluster_id)
                    if not self.cluster_entry_exists(vcenter_id, cluster_id):
                        self.create_cluster_default_entries(vcenter_id, cluster_id)
                # Update the network_id, allocated and network port count columns
                for host in ovsvapp_hosts.keys():
                    # Get the ports on the host
                    ovsvapp_ports = self.get_ovsvapp_ports(host)
                    # Get the ports count on each network
                    port_ids = [ovsvapp_port.port_id for ovsvapp_port in ovsvapp_ports]
                    nw_port_cnt_map = self.get_network_ovsvapp_port_count(port_ids)
                    # Get the networks to VLAN map
                    network_ids = nw_port_cnt_map.keys()
                    network_vlan_map = self.get_network_vlans(network_ids)
                    # Update the cluster lvid table for this host
                    host_details = ovsvapp_hosts[host]
                    vcenter_id = host_details.vcenter_id
                    cluster_id = host_details.cluster_id
                    self.update_cluster_lvid_allocations(vcenter_id, cluster_id, network_vlan_map,
                                                         nw_port_cnt_map)
                    # Update the other cluster on this vcenter
                    self.update_other_cluster(vcenter_id, cluster_id, network_vlan_map,
                                              ovsvapp_hosts)


def main():

    module = AnsibleModule(argument_spec={'connection': {'required': True, 'type': 'str'}},
                           supports_check_mode=True)

    conn = module.params['connection']
    db_result = []
    updated = False
    db_update = None
    try:
        db_update = OVSvAppDBUpdate(conn)
        db_update.update()
        db_result.append("Successfully Updated DB")
        updated = True
    except sa.exc.SQLAlchemyError as e:
        db_result.append(e.message)
    finally:
        if db_update:
            db_update.close()

    module.exit_json(changed=updated,
                     result=db_result)

if __name__ == "__main__":
    main()
