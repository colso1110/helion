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
import monasca_setup.detection

class DCN(monasca_setup.detection.ServicePlugin):
    """Detect DCN service VM specific daemons and setup configuration to monitor them.
    """
    def __init__(self, template_dir, overwrite=True, args=None):
        service_params = {
            'args': args,
            'template_dir': template_dir,
            'overwrite': overwrite,
            'service_name': 'dcn',
            'process_names': ['nuage-metadata-agent',
                              'nuage-rpc',
                              'nuage-housekeeper',
                              'nuage-SysMon',
                              'vm-monitor'],
            'service_api_url': '',
            'search_pattern': ''
        }
        super(DCN, self).__init__(service_params)

    def build_config(self):
        """Build the config as a Plugins object and return."""
        self.service_api_url = None
        self.search_pattern = None
        return monasca_setup.detection.ServicePlugin.build_config(self)
