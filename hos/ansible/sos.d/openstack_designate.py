#
# (c) Copyright 2015 Hewlett Packard Enterprise Development LP
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

import os
import os.path
from sos.plugins import Plugin, DebianPlugin


class OpenStackDesignate(Plugin):
    """OpenStackDesignate related information
    """
    plugin_name = "OpenStackDesignate"


class DebianOpenStackDesignate(OpenStackDesignate, DebianPlugin):
    """OpenStackDesignate related information for Debian distributions
    """

    def setup(self):
        super(DebianOpenStackDesignate, self).setup()

        self.add_copy_spec([
            "/var/log/designate/",
        ])
