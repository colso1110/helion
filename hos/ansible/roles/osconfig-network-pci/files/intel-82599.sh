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

# Usage: intel-82599.sh <Distro> <device-name> <vf-count> <operation>
# e.g. intel-82599.sh  Debian eth7 10 configure

#########################################################################
# Variables shared between functions
#########################################################################

export HLINUX_SYSPATH="/sys/class/net"
export INTEL_VFDRIVER_CONF="/etc/modprobe.d/blacklist-ixgbevf.conf"
export BLACKLIST="blacklist ixgbevf"

export DISTRO
export OPERATION
export DEVICE
export VF_COUNT
export DEV_FILE

export CONFIG_RUN_SKIPPED=0
# SUCCESS 0;FAILURE 1; SKIPPED=2
export EXIT_STATUS_SUCCESS=0
export EXIT_STATUS_FAILED=1
export EXIT_STATUS_SKIPPED=2
export EXIT_STATUS=$EXIT_STATUS_SUCCESS

# log a message identifying this script
log_msg() {
    logger "$SCRIPT: $1"
}

# Unload ixgbevf driver and blacklist this driver.
unload_ixgbevf() {
    local module="ixgbevf"
    # update $INTEL_VFDRIVER_CONF file to make ixgbevf driver never
    # load across re-boots
    if ! grep $BLACKLIST $INTEL_VFDRIVER_CONF; then
        echo  $BLACKLIST | tee $INTEL_VFDRIVER_CONF
    fi

    if [ `lsmod | grep $module | cut -f1 -d ' '` ]; then
        modprobe -r $module
    fi
}

# Pre-configure steps
pre_configure() {
    unload_ixgbevf
    EXIT_STATUS=$EXIT_STATUS_SUCCESS
}

# is the setting already correct?
is_configure_required() {
    if [ -f $DEV_FILE ]; then
        CONFIG_RUN_SKIPPED=0
        value=$(< $DEV_FILE)
        if [[ $value == $VF_COUNT ]]; then
           CONFIG_RUN_SKIPPED=1
        fi
    fi
}

# Update the active 'num_vfs' file
configure() {
    is_configure_required
    if [[ $CONFIG_RUN_SKIPPED == 1 ]]; then
        EXIT_STATUS=$EXIT_STATUS_SKIPPED
        log_msg "Configure: Skipped for $DEVICE"
    else
        log_msg "Configure: $DEV_FILE updated for $DEVICE"
        echo "0" | tee $DEV_FILE
        echo $VF_COUNT | tee $DEV_FILE
        EXIT_STATUS=$EXIT_STATUS_SUCCESS
        log_msg "Configure: Successfully completed for $DEVICE"
    fi
}

SCRIPT=$0
DISTRO=$1
DEVICE=$2
VF_COUNT=$3
OPERATION=$4

DEV_FILE=$HLINUX_SYSPATH/$DEVICE/device/sriov_numvfs

if [ "$DISTRO" == "Debian" ] || [ "$DISTRO" == "RedHat" ]; then
    case $OPERATION in
        'pre_configure')
            log_msg "Pre-configure"
            pre_configure
        ;;
        'configure')
            log_msg "Configure: $DEVICE"
            configure
        ;;
        'post_configure')
            log_msg "Post-configure: Successfully completed."
        ;;
        *)
            log_msg "Unknown Operation: $OPERATION"
            EXIT_STATUS=$EXIT_STATUS_FAILED
        ;;
    esac
else
    log_msg "Unsupported distro: $DISTRO"
    EXIT_STATUS=$EXIT_STATUS_FAILED
fi
exit $EXIT_STATUS
