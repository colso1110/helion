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

CREATE DATABASE IF NOT EXISTS `monasca_transform` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `monasca_transform`;

SET foreign_key_checks = 0;

CREATE TABLE IF NOT EXISTS `kafka_offsets` (
  `id` INTEGER AUTO_INCREMENT NOT NULL,
  `topic` varchar(128) NOT NULL,
  `until_offset` BIGINT NULL,
  `from_offset` BIGINT NULL,
  `app_name` varchar(128) NOT NULL,
  `partition` integer NOT NULL,
  `batch_time` varchar(20) NOT NULL,
  `last_updated` varchar(20) NOT NULL,
  `revision` integer NOT NULL,
  PRIMARY KEY (`id`, `app_name`, `topic`, `partition`, `revision`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `transform_specs` (
  `metric_id` varchar(128) NOT NULL,
  `transform_spec` varchar(2048) NOT NULL,
  PRIMARY KEY (`metric_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `pre_transform_specs` (
  `event_type` varchar(128) NOT NULL,
  `pre_transform_spec` varchar(2048) NOT NULL,
  PRIMARY KEY (`event_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


