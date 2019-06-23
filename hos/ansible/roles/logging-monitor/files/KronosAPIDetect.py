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
import logging

import monasca_setup.agent_config
import monasca_setup.detection

log = logging.getLogger(__name__)

PROCESS = "monasca-log-api"
SERVICE = "logging"

class KronosAPIDetect(monasca_setup.detection.Plugin):
    """Detect Kronos Logging API and setup configuration to monitor it.
    """

    def _detect(self):
        """Run detection, set self.available True if the process is detected.
        """
        if monasca_setup.detection.find_process_cmdline(PROCESS) is not None:
            self.available = True

    def build_config(self):
        """Build the config as a Plugins object and return.
        """
        log.info("\tEnabling the Kronos Logging API Process Detect plugin")
        config = monasca_setup.agent_config.Plugins()
        config.merge(monasca_setup.detection.watch_process([PROCESS], exact_match=False, service=SERVICE))
        return config

    def dependencies_installed(self):
        return True
