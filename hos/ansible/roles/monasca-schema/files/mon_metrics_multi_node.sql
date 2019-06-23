/*
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
*/

CREATE PROJECTION MonMetrics.Measurements_DBD_1_seg_monmetrics_design_b0 /*+basename(Measurements_DBD_1_seg_monmetrics_design),createtype(D)*/
(
 definition_dimensions_id ENCODING AUTO,
 time_stamp ENCODING RLE,
 value ENCODING AUTO,
 value_meta ENCODING RLE
)
AS
 SELECT definition_dimensions_id,
        time_stamp,
        value,
        value_meta
 FROM MonMetrics.Measurements
 ORDER BY time_stamp,
          definition_dimensions_id
SEGMENTED BY MODULARHASH (definition_dimensions_id) ALL NODES OFFSET 0;

CREATE PROJECTION MonMetrics.Measurements_DBD_1_seg_monmetrics_design_b1 /*+basename(Measurements_DBD_1_seg_monmetrics_design),createtype(D)*/
(
 definition_dimensions_id ENCODING AUTO,
 time_stamp ENCODING RLE,
 value ENCODING AUTO,
 value_meta ENCODING RLE
)
AS
 SELECT definition_dimensions_id,
        time_stamp,
        value,
        value_meta
 FROM MonMetrics.Measurements
 ORDER BY time_stamp,
          definition_dimensions_id
SEGMENTED BY MODULARHASH (definition_dimensions_id) ALL NODES OFFSET 1;



CREATE PROJECTION MonMetrics.DefinitionDimensions_DBD_3_seg_monmetrics_design_b0 /*+basename(DefinitionDimensions_DBD_3_seg_monmetrics_design),createtype(D)*/
(
 id ENCODING AUTO,
 definition_id ENCODING AUTO,
 dimension_set_id ENCODING RLE
)
AS
 SELECT id,
        definition_id,
        dimension_set_id
 FROM MonMetrics.DefinitionDimensions
 ORDER BY dimension_set_id,
          definition_id
SEGMENTED BY MODULARHASH (id) ALL NODES OFFSET 0;

CREATE PROJECTION MonMetrics.DefinitionDimensions_DBD_3_seg_monmetrics_design_b1 /*+basename(DefinitionDimensions_DBD_3_seg_monmetrics_design),createtype(D)*/
(
 id ENCODING AUTO,
 definition_id ENCODING AUTO,
 dimension_set_id ENCODING RLE
)
AS
 SELECT id,
        definition_id,
        dimension_set_id
 FROM MonMetrics.DefinitionDimensions
 ORDER BY dimension_set_id,
          definition_id
SEGMENTED BY MODULARHASH (id) ALL NODES OFFSET 1;



CREATE PROJECTION MonMetrics.Dimensions_seg_set_id_b0 /*+basename(Dimensions_seg_set_id),createtype(D)*/
(
 dimension_set_id,
 name ENCODING RLE,
 value
)
AS
 SELECT Dimensions.dimension_set_id,
        Dimensions.name,
        Dimensions.value
 FROM MonMetrics.Dimensions
 ORDER BY Dimensions.dimension_set_id,
          Dimensions.name,
          Dimensions.value
SEGMENTED BY hash(Dimensions.dimension_set_id) ALL NODES OFFSET 0;

CREATE PROJECTION MonMetrics.Dimensions_seg_set_id_b1 /*+basename(Dimensions_seg_set_id),createtype(D)*/
(
 dimension_set_id,
 name ENCODING RLE,
 value
)
AS
 SELECT Dimensions.dimension_set_id,
        Dimensions.name,
        Dimensions.value
 FROM MonMetrics.Dimensions
 ORDER BY Dimensions.dimension_set_id,
          Dimensions.name,
          Dimensions.value
SEGMENTED BY hash(Dimensions.dimension_set_id) ALL NODES OFFSET 1;

select start_refresh();

