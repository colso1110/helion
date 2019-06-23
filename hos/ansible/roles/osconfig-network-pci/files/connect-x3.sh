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

# Usage: connect-x3.sh <Distro> <device-name> <vf-count> <operation> <bus_address> <port_num>
# e.g. connect-x3.sh  Debian eth7 10 configure 0000:04:00.0 1

#########################################################################
# Variables shared between functions
#########################################################################

export MLX_CORE_CONF="/etc/modprobe.d/mlx4_core.conf"

export SCRIPT
export DISTRO
export DEVICE
export VF_COUNT
export OPERATION
export BUS_ADDRESS
export PORT_NUM
export DEVICE_ID

#SUCCESS 0; FAILURE 1; SKIPPED 2
export EXIT_STATUS_SUCCESS=0
export EXIT_STATUS_FAILED=1
export EXIT_STATUS_SKIPPED=2
export EXIT_STATUS=$EXIT_STATUS_SUCCESS

# log a message identifying this script
log_msg() {
    logger "$SCRIPT: $1"
}

# Initialise port number value when empty and check the device status
init() {
    if [ -z $PORT_NUM ]; then
        PORT_NUM=0
    fi

    dev_id=$( cat /sys/bus/pci/devices/$BUS_ADDRESS/device )
    DEVICE_ID=${dev_id:2}
}

# Unload mlx4_en and mlx4_ib drivers.
unload_mlx4_drivers() {
    log_msg "unload mlx4_en driver"
    if [ `lsmod | grep mlx4_en | cut -f1 -d ' ' | grep mlx4_en` ]; then
        modprobe -r mlx4_en
    fi
    log_msg "unload mlx4_ib driver"
    if [ `lsmod | grep mlx4_ib | cut -f1 -d ' ' | grep mlx4_ib` ]; then
        modprobe -r mlx4_ib
    fi
}

# Check if vfs are configured in the existing vf by checking if it contains non-zero digits
# - If yes, return 0 - e.g. vf="0;6" returns 0
# - Else, return 1 - e.g. vf="0;0" returns 1
is_vf_configured() {
   if [[ `echo $1 | grep -o '[1-9]*'` ]]
   then
        return 0
   else
        return 1
   fi
}

extend_vf_array() {
    array_size=${#VFS_ARRAY[@]}
    pos=`expr $PORT_NUM + 1`
    if (( $pos > $array_size ))
    then
        diff=`expr $pos - $array_size`
        i=0
        while [ $i -lt $diff ]
        do
            VFS_ARRAY+=('0')
            i=`expr $i + 1`
        done
    fi
}

extend_port_type_array() {
    array_size=${#PORT_TYPE_ARRAY[@]}
    pos=`expr $PORT_NUM + 1`
    if (( $pos > $array_size ))
    then
        diff=`expr $pos - $array_size`
        i=0
        while [ $i -lt $diff ]
        do
            PORT_TYPE_ARRAY+=('2')
            i=`expr $i + 1`
        done
    fi
}

# Pre configure to flush the VFs values to 0 if the entry exists in MLX_CORE_CONF file
pre_configure() {
    if [[ -f $MLX_CORE_CONF && $DEVICE_ID -eq 1007 ]]
    then
        if grep "$BUS_ADDRESS/*" $MLX_CORE_CONF
        then
            num_vf=`grep -o "num_vfs.*" $MLX_CORE_CONF`
            # Fetching the existing vf value, e.g.-0000:04:00.0-0;4
            existing_vfs=`echo $num_vf | grep -o "$BUS_ADDRESS[^ ]*"`
            vfs=`echo $existing_vfs | cut -d '-' -f2`
            # Prepare VF array for initializing
            IFS=';' read -r -a VFS_ARRAY <<< $vfs

            # Get port type array
            port_array=$(grep -o "port_type_array=[^ ]*" $MLX_CORE_CONF)
            existing_port_types=`echo $port_array | grep -o "$BUS_ADDRESS[^ ]*"`
            old_port_array=`echo $existing_port_types | cut -d '-' -f2`
            # Prepare PORT TYPE array for initializing
            IFS=';' read -r -a PORT_TYPE_ARRAY <<< $old_port_array

            array_size=${#VFS_ARRAY[@]}
            i=0
            while [ $i -lt $array_size ]
            do
                VFS_ARRAY[$i]='0'
                i=`expr $i + 1`
            done
            extend_vf_array
            extend_port_type_array

            # Initialize the vf configuration
            final_vf=$(IFS=";" ; echo "${VFS_ARRAY[*]}")
            vf_str="$BUS_ADDRESS-${final_vf}"
            sed -i "s/${existing_vfs}/${vf_str}/g" $MLX_CORE_CONF

            # Update port_type_array
            final_port_array=$(IFS=";" ; echo "${PORT_TYPE_ARRAY[*]}")
            port_str="$BUS_ADDRESS-${final_port_array}"
            sed -i "s/${existing_port_types}/${port_str}/g" $MLX_CORE_CONF
        else
            # BUS_ADDRESS does not exist in the MLX_CORE_CONF file
            log_msg "Pre-configure: Skipped for $BUS_ADDRESS as the bus address does not exist in $MLX_CORE_CONF"
        fi
    else
        log_msg "Pre-configure: Skipped for $BUS_ADDRESS as either $MLX_CORE_CONF not found, or it is unsupported device $DEVICE_ID"
    fi
}

# This function updates existing VF configuration for multiport device with ID 1007,
# and is called only if there is a change in the vf-count for the specified port.
# This function is expected to do the following :
#   - Update the existing VF configuration to reflect the current request for the port.
#     For e.g. num_vfs=0000:04:00.0-1;0, for the case where vf-count of 1 is specified for port
#     number 0 in the request.
#     For e.g. num_vfs=0000:04:00.0-0;2, for the case where vf-count of 2 is specified for port
#     number 1 in the request.
#  -  Check and fail if vfs exists on other ports of the same bus address.

configure_vfs() {
    vf=$1
    existing_vfs=$2
    if is_vf_configured $vf;
    then
        IFS=';' read -r -a vfs_array <<< $vf
        log_msg "Configure: Updating $MLX_CORE_CONF file for Device Id - $DEVICE_ID"
        # Update the num of vfs only if configuration is already done for that port
        if [ ${vfs_array[$PORT_NUM]} -eq 0 ]
        then
            log_msg "Configure: Device Id 1007 does not support VF creation on multiple ports of the same card."
            EXIT_STATUS=$EXIT_STATUS_FAILED
            exit $EXIT_STATUS
        fi
    fi
    sed -i "s/${existing_vfs}/${NUM_VFS}/g" $MLX_CORE_CONF
    # Get port type array
    port_array=$(grep -o "port_type_array=[^ ]*" $MLX_CORE_CONF)
    existing_port_types=`echo $port_array | grep -o "$BUS_ADDRESS[^ ]*"`
    old_port_array=`echo $existing_port_types | cut -d '-' -f2`
    # Update port_type_array
    sed -i "s/${existing_port_types}/$PORT_TYPE_ARRAY/g" $MLX_CORE_CONF
    log_msg "Configure: $MLX_CORE_CONF file updated for $DEVICE and $BUS_ADDRESS"
}

# This function creates vf configuration if it doesn't exists. It skips the configuration
# if there is no change required or else updates the existing configuration.
# This function is expected to do the following :
#   - Check for the device id and call appropriate functions to handle VF creation.
#   - Maintain idempotency with respect to vf counts.

configure() {
    PORT_TYPE_ETHERNET=2

    # e.g. In case of ethernet, num_vfs=0000:04:00.0-0;4 and port_type_array=0000:04:00.0-2;2
    i=0
    ports=$PORT_NUM
    if (( $PORT_NUM % 2 == 0 ));
    then
        ports=`expr $PORT_NUM + 1`
    fi
    while [ $i -le $ports ]
    do
        vf_array[i]=0
        port_array[i]=$PORT_TYPE_ETHERNET
        if [[ $i = $PORT_NUM ]]; then
            vf_array[i]=$VF_COUNT
        fi
        i=`expr $i + 1`
    done
    vf=$(IFS=";" ; echo "${vf_array[*]}")
    port=$(IFS=";" ; echo "${port_array[*]}")

    NUM_VFS="$BUS_ADDRESS-$vf"
    PORT_TYPE_ARRAY="$BUS_ADDRESS-$port"

    VIRT_FUN="options mlx4_core port_type_array=$PORT_TYPE_ARRAY num_vfs=$NUM_VFS enable_64b_cqe_eqe=0 log_num_mgm_entry_size=-1"

    if [ -f $MLX_CORE_CONF ]
    then
        if grep -Fq "$BUS_ADDRESS" $MLX_CORE_CONF
        then
            # VF configuration exists. Update it
            vfs=$(grep -o "num_vfs.*" $MLX_CORE_CONF)
            # Fetching the existing vf value, e.g.-0000:04:00.0-0;4
            existing_vfs=`echo $vfs | grep -o "$BUS_ADDRESS[^ ]*"`
            old_vf=`echo $existing_vfs | cut -d '-' -f2`
            if [ "$existing_vfs" = "$NUM_VFS" ]
            then
                log_msg "Configure: Skipped for $DEVICE and $BUS_ADDRESS"
                EXIT_STATUS=$EXIT_STATUS_SKIPPED
            # Device Id 1007 has a limitation that it cannot handle VFs creation across multiple ports of the same card.
            elif [[ $DEVICE_ID -eq 1007 ]]
            then
                log_msg "Configure: Device $DEVICE already configured. Updating."
                configure_vfs $old_vf $existing_vfs
            else
                log_msg "Configure: Device $DEVICE with device id $DEVICE_ID not supported "
                EXIT_STATUS=$EXIT_STATUS_SKIPPED
            fi
        # If values for num_vfs and port_array already exists then prepending new
        # values to the existing value
        elif vf_num=$(grep -o "num_vfs=[^ ]*" $MLX_CORE_CONF)
        then
            # VF configuration does not exist. Write the one requested.
            log_msg "Configure: Device $DEVICE not configured for VF. Creating."
            old_vfs=`echo $vf_num | cut -d '=' -f2`
            #Fetching the previous port_type_array value, eg-0000:04:00.0-2;2
            port_array=$(grep -o "port_type_array=[^ ]*" $MLX_CORE_CONF)
            old_port_array=`echo $port_array | cut -d '=' -f2`
            new_vfs="$NUM_VFS $old_vfs"
            new_port_array="$PORT_TYPE_ARRAY $old_port_array"
            sed -i "s/${old_vfs}/${new_vfs}/g" $MLX_CORE_CONF
            sed -i "s/${old_port_array}/${new_port_array}/g" $MLX_CORE_CONF
            log_msg "Configure: $MLX_CORE_CONF file updated for $DEVICE and $BUS_ADDRESS"
        else
            echo $VIRT_FUN | tee $MLX_CORE_CONF
            log_msg "Configure: $MLX_CORE_CONF file updated for $DEVICE and $BUS_ADDRESS"
        fi
    else
        # Config file does not exist. Create it.
        log_msg "Configure: Creating $MLX_CORE_CONF file"
        touch $MLX_CORE_CONF
        chmod 644 $MLX_CORE_CONF
        echo $VIRT_FUN | tee $MLX_CORE_CONF
        log_msg "Configure: $MLX_CORE_CONF file updated for $DEVICE and $BUS_ADDRESS"
    fi
    # If VF count got updated for success, or skipped case (vf_count = 0), then
    # reload the required drivers.
    if (( (EXIT_STATUS == EXIT_STATUS_SUCCESS) || (EXIT_STATUS == EXIT_STATUS_SKIPPED && VF_COUNT == 0) ))
    then
        if [[ $VF_COUNT > 0 ]]
        then
            update-initramfs -k all -t -u
        fi
        unload_mlx4_drivers
        modprobe mlx4_en
        # Bring up the interface that is impacted
        if [[ ! `ip link show $DEVICE up` ]]
        then
            ip link set $DEVICE up
        fi
    fi
    # At this stage EXIT_STATUS can have 2 values EXIT_STATUS_SKIPPED or EXIT_STATUS_SUCCESS
    # Since this script is called from system, we do not want to sent FAILED status hence
    # setting the EXIT_STATUS to SUCCESS
    EXIT_STATUS=$EXIT_STATUS_SUCCESS
}

SCRIPT=$0
DISTRO=$1
DEVICE=$2
VF_COUNT=$3
OPERATION=$4
BUS_ADDRESS=$5
PORT_NUM=$6

if [ "$DISTRO" == "Debian" ]; then
    case $OPERATION in

        'pre_configure')
            init
            log_msg "Pre-configure: $DEVICE"
            pre_configure
            log_msg "Pre-configure: Successfully completed for $DEVICE"
        ;;

        'configure')
            init
            log_msg "Configure: $DEVICE"
            configure
            if [[ "$EXIT_STATUS" == "$EXIT_STATUS_SUCCESS" ]];then
                log_msg "Configure: Successfully completed for $DEVICE"
            fi
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