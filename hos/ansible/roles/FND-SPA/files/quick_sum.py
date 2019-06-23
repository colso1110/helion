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

from __future__ import print_function
from pyspark import SparkConf
from pyspark import SparkContext

if __name__ == "__main__":

    my_spark_conf = SparkConf().setAppName("Quicksum")
    spark_context = SparkContext(conf=my_spark_conf)
    data = [1, 2, 3, 4, 5]
    distData = spark_context.parallelize(data)
    total = distData.reduce(lambda a, b: a + b)
    print("Total is %s" % total)
    spark_context.stop()
