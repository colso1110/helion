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
from sos.plugins import DebianPlugin
from sos.plugins import Plugin


class Freezer(Plugin, DebianPlugin):
    """ Freezer related information for Debian distributions
    """
    plugin_name = "freezer"
    option_list = [("log", "gathers all freezer logs", "slow", False)]
    files = ('/var/log/freezer-agent/',
             '/var/log/freezer.log',
             '/var/log/freezer-api/',
             '/etc/freezer/',
             '/root/.freezer/',
             '/usr/bin/freezer-agent',
             '/usr/bin/freezer-scheduler')

    def setup(self):
        self.add_copy_spec([
            "/etc/freezer/",
            "/var/log/freezer-*",
        ])
