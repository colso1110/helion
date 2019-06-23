#!/bin/bash
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

echo "entered in the shell script"
echo "trying ssh to the vsc.."
/usr/bin/sshpass -e ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no $1@$2<<ENDHERE

echo "configuring system name"
configure system name $7

echo "configuring ntpserver1"
configure system time ntp server $3

echo "configuring ntpserver2"
configure system time ntp server $4

echo "configuring configure system time ntp no shutdown"
configure system time ntp no shutdown

echo "configuring system time sntp shutdown"
configure system time sntp shutdown
exit

echo "configuring system time zone"
configure system time zone UTC
exit

echo "configuring XMPP server setup"
configure vswitch-controller xmpp-server $5
exit
exit

echo "saving configuration"
admin save

echo "configure TUL IP"
configure router interface "control"
address  $6
no shutdown
exit all
admin
save cf1:
exit

echo "saving configuration"
admin save
exit
logout
ENDHERE






