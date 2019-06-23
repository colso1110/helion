#
# (c) Copyright 2015-2016 Hewlett Packard Enterprise Development LP
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


class HLMEon(monasca_setup.detection.ServicePlugin):

    """Detect Eon daemons and setup configuration to monitor them."""

    def __init__(self, template_dir, overwrite=True, args=None):
        service_params = {
            'args': args,
            'template_dir': template_dir,
            'overwrite': overwrite,
            'service_name': 'eon',
            'process_names': ['eon-api', 'eon-conductor'],
            'service_api_url': 'http://localhost:8282/',
            'search_pattern': '.*eon.*API.*',
        }

        super(HLMEon, self).__init__(service_params)
