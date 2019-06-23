#!/bin/bash
set -eu
set -o pipefail

die() {
    echo "$1" >&2
    exit 1
}

make_bridge() {
    ovs-vsctl -- --may-exist add-br "${BRIDGE_NAME}"
    ip link set dev ${BRIDGE_NAME} up

    # Obtain current routes for the interface.
    ROUTES=$(ip route list | grep ${BRIDGE_INTERFACE} || true)
    CFG=$(ip addr show ${BRIDGE_INTERFACE} | awk '/inet / {$1="";$(NF)=""; print $0}' || true)
    CFG=$(echo "$CFG" |  sed  s/dynamic//)
    if [ -z "$CFG" ] ; then
        die "Error: BRIDGE_INTERFACE:${BRIDGE_INTERFACE} has no assigned IP address"
    fi

    ovs-vsctl -- --may-exist add-port ${BRIDGE_NAME} ${BRIDGE_INTERFACE}

    # Remap the current addresses to the bridge.
    if [[ -n "${CFG}" ]]; then
        SAVEIFS=$IFS;
        IFS=$(echo -en "\n\b");
        for item in ${CFG} ; do
            eval ip addr del dev ${BRIDGE_INTERFACE} ${item}
            eval ip addr add dev ${BRIDGE_NAME} ${item}
        done
        IFS=$SAVEIFS
    fi

    # Ensure we only set up the missing routes on the bridge.
    ROUTES=${ROUTES//${BRIDGE_INTERFACE}/${BRIDGE_NAME}}
    ROUTES_NEW=$( ( echo "${ROUTES}"; ip route list |
                            awk -v dev="${BRIDGE_NAME}" '$0 ~ dev {print $0}' ) | sort | uniq -u )

    SAVEIFS=$IFS;
    IFS=$(echo -en "\n\b");
    for LINE in ${ROUTES_NEW}; do
        eval ip route replace $LINE
    done
    IFS=$SAVEIFS
}

BRIDGE_INTERFACE=$1
BRIDGE_NAME=${2:-'vsa-bridge'}

make_bridge;
