#!/bin/bash
# gets all devices except boot

default_disk_pattern="/dev/sd[a-z]\+$"

function _get_all_devices() {
    devs=$( ls /dev/sd* | grep $default_disk_pattern 2>/dev/null )
    echo "${devs}"
}

function get_boot_dev() {
    #Assuming dev/sda is the boot_dev
    boot_dev="/dev/sda"
    echo $boot_dev
}

function get_non_boot_dev() {
    devs=$( _get_all_devices )
    boot_dev=$( get_boot_dev )
    other_devs=$( echo "${devs}" | grep -v $boot_dev )
    echo "${other_devs}"
}

devices=
function get_devices() {
    devices=$( get_non_boot_dev )
    echo -n $devices
}

get_devices;
