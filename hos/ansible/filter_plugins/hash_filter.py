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

import zlib

# Given a string returns an integer hash < 2^32
# crc32 would be good but it returns a signed
# value which cannot be used for a server id
#
#   https://bugs.python.org/issue1202

def adler32_unsigned(value ):
    return zlib.adler32(value) & 0xffffffffL

class FilterModule(object):

    def filters(self):
        return {'adler32_unsigned': adler32_unsigned}
