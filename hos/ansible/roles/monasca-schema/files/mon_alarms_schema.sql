/*
#
# (c) Copyright 2015,2016 Hewlett Packard Enterprise Development LP
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
*/

CREATE SCHEMA MonAlarms;

CREATE TABLE MonAlarms.StateHistory(
    id AUTO_INCREMENT,
    tenant_id VARCHAR,
    alarm_id VARCHAR,
    metrics VARCHAR (65000),
    old_state VARCHAR,
    new_state VARCHAR,
    sub_alarms VARCHAR (65000),
    reason VARCHAR(65000),
    reason_data VARCHAR(65000),
    time_stamp TIMESTAMP NOT NULL
) PARTITION BY EXTRACT('year' FROM time_stamp)*10000 + EXTRACT('month' FROM time_stamp)*100 + EXTRACT('day' FROM time_stamp);
