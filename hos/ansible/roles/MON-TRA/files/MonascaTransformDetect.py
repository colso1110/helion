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

import logging

import monasca_setup.detection

log = logging.getLogger(__name__)


class MonascaTransformDetect(monasca_setup.detection.ServicePlugin):

    """Detect Monasca Transform daemons and setup configuration to
    monitor them."""

    def __init__(self, template_dir, overwrite=True, args=None):
        log.info("\tWatching the monasca transform processes.")
        service_params = {
            'args': {},
            'template_dir': template_dir,
            'overwrite': overwrite,
            'service_name': 'monasca-transform',
            'process_names': [
                'monasca-transform',
                'pyspark',
                'org.apache.spark.executor.CoarseGrainedExecutorBackend']
        }

        super(MonascaTransformDetect, self).__init__(service_params)

